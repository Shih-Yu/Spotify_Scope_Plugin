"""Minimal pipeline: current Spotify song title -> one prompt -> preprocessor. Optional synced lyrics."""

import logging
import os
from typing import TYPE_CHECKING, Optional

import torch

from scope.core.pipelines.interface import Pipeline, Requirements

from .lyrics_client import (
    fetch_plain_lyrics,
    fetch_synced_lyrics,
    get_line_at_position,
)
from .schema import SpotifyConfig
from .spotify_client import SpotifyClient, TrackInfo

if TYPE_CHECKING:
    from scope.core.pipelines.base_schema import BasePipelineConfig

# Preset templates: theme key -> template string. Used when template_theme != "custom".
PROMPT_TEMPLATE_PRESETS: dict[str, str] = {
    "dreamy_abstract": "{lyrics}, dreamlike, {song} by {artist}, soft lighting",
    "lyrics_style": "{lyrics}, inspired by {song} and {artist}, vivid",
    "music_video": 'Music video frame: {lyrics}, "{song}" by {artist}, cinematic',
    "minimal": "{lyrics}",
    "song_artist": "{song} by {artist}, vivid, cinematic",
}

logger = logging.getLogger(__name__)


class SpotifyPipeline(Pipeline):
    """Preprocessor: get current Spotify track, build one prompt from song title, pass to pipeline."""

    @classmethod
    def get_config_class(cls) -> type["BasePipelineConfig"]:
        return SpotifyConfig

    def __init__(
        self,
        device: torch.device | None = None,
        **kwargs,
    ):
        self.device = (
            device
            if device is not None
            else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        )
        self._spotify_client: Optional[SpotifyClient] = None
        self._spotify_credentials: Optional[tuple] = None
        # Cache synced lyrics per track so we don't refetch every frame
        self._synced_cache: Optional[tuple[str, int, list]] = None  # (track_id, duration_ms, lines)
        self._last_logged_prompt: Optional[str] = None  # log prompt only when it changes

    def prepare(self, **kwargs) -> Requirements:
        return Requirements(input_size=1)

    def _get_spotify_client(self, kwargs: dict) -> SpotifyClient:
        # Credentials and redirect URI come from environment (e.g. RunPod pod env at setup).
        client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        headless = os.environ.get("SPOTIFY_HEADLESS", "true").lower() in ("1", "true", "yes")
        creds = (client_id, client_secret, redirect_uri, headless)
        if self._spotify_client is None or self._spotify_credentials != creds:
            self._spotify_credentials = creds
            self._spotify_client = SpotifyClient(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                headless_mode=headless,
            )
        return self._spotify_client

    def __call__(self, **kwargs) -> dict:
        logger.warning("Spotify preprocessor: __call__ invoked (if you see this, the plugin is running)")
        template_theme = kwargs.get("template_theme") or kwargs.get("templateTheme") or os.environ.get("SPOTIFY_TEMPLATE_THEME", "dreamy_abstract")
        custom_template = (
            kwargs.get("prompt_template")
            or os.environ.get("SPOTIFY_PROMPT_TEMPLATE", "{lyrics}")
        )
        if template_theme == "custom" or template_theme not in PROMPT_TEMPLATE_PRESETS:
            prompt_template = custom_template
        else:
            prompt_template = PROMPT_TEMPLATE_PRESETS[template_theme]
        fallback_prompt = (
            kwargs.get("fallback_prompt")
            or os.environ.get("SPOTIFY_FALLBACK_PROMPT", "Abstract flowing colors and shapes")
        )

        try:
            client = self._get_spotify_client(kwargs)
            track = client.get_current_track()
        except Exception as e:
            logger.warning("Spotify get_current_track failed: %s", e)
            track = None

        if track is None or not track.is_playing:
            prompt = fallback_prompt
            self._synced_cache = None
            logger.warning(
                "Spotify preprocessor: no track playing or API failed. Using fallback. "
                "Check SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and token at ~/.scope-spotify/.spotify_token_cache"
            )
        else:
            lyrics = ""
            # Scope may pass snake_case (schema) or camelCase (frontend); env fallback if UI doesn't pass
            use_lyrics = kwargs.get("use_lyrics", kwargs.get("useLyrics"))
            if use_lyrics is None:
                use_lyrics = os.environ.get("SPOTIFY_USE_LYRICS", "1").lower() in ("1", "true", "yes")
            use_synced = kwargs.get("use_synced_lyrics", kwargs.get("useSyncedLyrics"))
            if use_synced is None:
                use_synced = os.environ.get("SPOTIFY_USE_SYNCED_LYRICS", "1").lower() in ("1", "true", "yes")
            lyrics_max = int(kwargs.get("lyrics_max_chars", kwargs.get("lyricsMaxChars", 300)) or 0)
            # WARNING so it shows when Scope log level is WARNING (INFO often filtered)
            logger.warning(
                "Spotify preprocessor: use_lyrics=%s, use_synced_lyrics=%s",
                use_lyrics, use_synced,
            )

            if use_lyrics:
                if use_synced:
                    # Time-synced: current line from LRCLIB, cached per track
                    cache = self._synced_cache
                    if cache is None or cache[0] != track.track_id or cache[1] != track.duration_ms:
                        duration_sec = max(1, track.duration_ms // 1000)
                        lines = fetch_synced_lyrics(
                            track.artist, track.name, track.album, duration_sec
                        )
                        self._synced_cache = (track.track_id, track.duration_ms, lines)
                        if not lines:
                            logger.warning(
                                "Spotify preprocessor: no synced lyrics found for %s by %s (LRCLIB). Using title only.",
                                track.name, track.artist,
                            )
                    else:
                        lines = cache[2]
                    lyrics = get_line_at_position(lines, track.progress_ms)
                    # Log current line so you can verify sync in server logs (line changes as song plays)
                    if lyrics:
                        sec = track.progress_ms // 1000
                        logger.warning(
                            "Spotify preprocessor: synced lyric @ %d:%02d — %s",
                            sec // 60, sec % 60, lyrics[:80] + ("..." if len(lyrics) > 80 else ""),
                        )
                else:
                    lyrics = fetch_plain_lyrics(track.artist, track.name, lyrics_max or 500)

            format_kw: dict = {"song": track.name, "artist": track.artist, "lyrics": lyrics}
            try:
                prompt = prompt_template.format(**format_kw)
            except KeyError:
                prompt = f"{track.name} by {track.artist}" + (f": {lyrics}" if lyrics else "")
            logger.warning("Spotify preprocessor: prompt from track: %s by %s", track.name, track.artist)

        # Log the actual prompt when it changes so you can see what's driving the image
        if prompt != getattr(self, "_last_logged_prompt", None):
            self._last_logged_prompt = prompt
            snippet = (prompt[:120] + "…") if len(prompt) > 120 else prompt
            logger.warning("Spotify preprocessor: prompt sent to pipeline: %s", snippet or "(empty)")

        return self._passthrough(kwargs, prompt)

    def _passthrough(self, kwargs: dict, prompt: str) -> dict:
        video = kwargs.get("video")
        if video is not None and len(video) > 0:
            frames = torch.stack([f.squeeze(0) for f in video], dim=0)
            frames = frames.to(device=self.device, dtype=torch.float32) / 255.0
        else:
            frames = torch.zeros(1, 512, 512, 3, device=self.device)
        # Pass both keys: some Scope pipelines/UI use "prompt", others "prompts"
        return {"video": frames.clamp(0, 1), "prompt": prompt, "prompts": prompt}
