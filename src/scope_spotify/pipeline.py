"""Minimal pipeline: current Spotify song title -> one prompt -> preprocessor. Optional synced lyrics."""

import logging
import os
import time
from typing import TYPE_CHECKING, Optional

import torch

from scope.core.pipelines.interface import Pipeline, Requirements

from .lyrics_client import (
    fetch_plain_lyrics,
    fetch_synced_lyrics,
    get_line_at_position,
    lyrics_to_keywords,
)
from .schema import SpotifyConfig
from .spotify_client import SpotifyClient, TrackInfo

if TYPE_CHECKING:
    from scope.core.pipelines.base_schema import BasePipelineConfig

# Rotating style words appended to lyrics when lyrics_rotating_style is on (more visual variety).
LYRICS_STYLE_WORDS = (
    "cinematic",
    "dreamy",
    "noir",
    "vivid",
    "surreal",
    "ethereal",
    "dramatic",
    "moody",
    "luminous",
    "atmospheric",
)

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
        # Rotating style: advance when line changes (if rotation_seconds==0) or by time
        self._style_index: int = 0
        self._last_style_line: Optional[str] = None
        # FPS logging: preprocessor is invoked once per pipeline frame, so invocation rate = pipeline FPS
        self._fps_invocation_count: int = 0
        self._fps_last_log_time: float = 0.0
        self._last_call_time: Optional[float] = None

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
        now = time.perf_counter()
        # Log pipeline FPS periodically (preprocessor invoked once per frame; rate = output FPS)
        self._fps_invocation_count += 1
        self._last_call_time = now
        if self._fps_last_log_time == 0.0:
            self._fps_last_log_time = now
        elif now - self._fps_last_log_time >= 5.0:
            elapsed = now - self._fps_last_log_time
            fps = self._fps_invocation_count / elapsed
            logger.warning(
                "Spotify preprocessor: pipeline FPS ≈ %.1f (preprocessor invoked %d times in %.1fs). "
                "Low FPS is from the image pipeline (Stream Diffusion steps/resolution), not this plugin. "
                "Tune Scope/Stream Diffusion settings (e.g. fewer steps, lower resolution) for higher FPS.",
                fps, self._fps_invocation_count, elapsed,
            )
            self._fps_invocation_count = 0
            self._fps_last_log_time = now

        template_theme = kwargs.get("template_theme") or kwargs.get("templateTheme") or os.environ.get("SPOTIFY_TEMPLATE_THEME", "dreamy_abstract")
        custom_template = (
            kwargs.get("prompt_template")
            or os.environ.get("SPOTIFY_PROMPT_TEMPLATE", "{lyrics}")
        )
        if template_theme == "custom" or template_theme not in PROMPT_TEMPLATE_PRESETS:
            prompt_template = custom_template
            logger.warning("Spotify preprocessor: template_theme=custom, using Prompt Template from settings")
        else:
            prompt_template = PROMPT_TEMPLATE_PRESETS[template_theme]
            logger.warning("Spotify preprocessor: template_theme=%s", template_theme)
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
            keywords_only = kwargs.get("lyrics_keywords_only", kwargs.get("lyricsKeywordsOnly"))
            if keywords_only is None:
                keywords_only = os.environ.get("SPOTIFY_LYRICS_KEYWORDS_ONLY", "").lower() in ("1", "true", "yes")
            rotating_style = kwargs.get("lyrics_rotating_style", kwargs.get("lyricsRotatingStyle"))
            if rotating_style is None:
                rotating_style = os.environ.get("SPOTIFY_LYRICS_ROTATING_STYLE", "").lower() in ("1", "true", "yes")
            style_rotation_sec = float(kwargs.get("lyrics_style_rotation_seconds", kwargs.get("lyricsStyleRotationSeconds")) or 0)
            if style_rotation_sec <= 0:
                style_rotation_sec = float(os.environ.get("SPOTIFY_LYRICS_STYLE_ROTATION_SECONDS", "0") or 0)
            preview_sec = float(kwargs.get("lyrics_preview_seconds", kwargs.get("lyricsPreviewSeconds")) or 0)
            if preview_sec <= 0:
                preview_sec = float(os.environ.get("SPOTIFY_LYRICS_PREVIEW_SECONDS", "0") or 0)
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
                        self._last_style_line = None  # reset so first line of new track can advance style
                        if not lines:
                            logger.warning(
                                "Spotify preprocessor: no synced lyrics found for %s by %s (LRCLIB). Using title only.",
                                track.name, track.artist,
                            )
                    else:
                        lines = cache[2]
                    # Preview: use position N seconds ahead so next line appears earlier
                    progress_ms = track.progress_ms + int(preview_sec * 1000)
                    lyrics = get_line_at_position(lines, progress_ms)
                    # Rotating style: advance by time (every N sec) or by line change
                    if rotating_style and LYRICS_STYLE_WORDS:
                        if style_rotation_sec > 0:
                            self._style_index = int(progress_ms / 1000.0 / style_rotation_sec) % len(LYRICS_STYLE_WORDS)
                        else:
                            if self._last_style_line != lyrics:
                                self._last_style_line = lyrics
                                self._style_index = (self._style_index + 1) % len(LYRICS_STYLE_WORDS)
                        style_word = LYRICS_STYLE_WORDS[self._style_index]
                        lyrics = f"{lyrics}, {style_word}" if lyrics else style_word
                    # Keywords-only: strip stopwords for stronger visual prompts
                    if keywords_only and lyrics:
                        lyrics = lyrics_to_keywords(lyrics) or lyrics
                    # Log current line so you can verify sync in server logs (line changes as song plays)
                    if lyrics:
                        sec = track.progress_ms // 1000
                        logger.warning(
                            "Spotify preprocessor: synced lyric @ %d:%02d — %s",
                            sec // 60, sec % 60, lyrics[:80] + ("..." if len(lyrics) > 80 else ""),
                        )
                else:
                    lyrics = fetch_plain_lyrics(track.artist, track.name, lyrics_max or 500)
                    if keywords_only and lyrics:
                        lyrics = lyrics_to_keywords(lyrics) or lyrics
                    if rotating_style and LYRICS_STYLE_WORDS:
                        self._style_index = (self._style_index + 1) % len(LYRICS_STYLE_WORDS)
                        style_word = LYRICS_STYLE_WORDS[self._style_index]
                        lyrics = f"{lyrics}, {style_word}" if lyrics else style_word

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
