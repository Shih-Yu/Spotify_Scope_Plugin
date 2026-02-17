"""Minimal pipeline: current Spotify song title -> one prompt -> preprocessor. Optional synced lyrics."""

import logging
import os
import time
from typing import TYPE_CHECKING, Optional

import torch

from scope.core.pipelines.interface import Pipeline, Requirements

from .lyrics_client import (
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
        # Per-section timing (ms) to diagnose FPS drop when using plugin; accumulated and logged every ~5s
        self._time_get_track_sum: float = 0.0
        self._time_lyrics_sum: float = 0.0
        self._time_passthrough_sum: float = 0.0
        self._time_count: int = 0
        # Log settings only when they change (avoid per-frame log spam)
        self._last_logged_theme: Optional[str] = None
        self._last_logged_lyric_line: Optional[str] = None
        # Cache resolved config from kwargs so we don't re-read 15+ dict/env lookups every frame
        self._last_kwargs_id: Optional[int] = None
        self._cached_config: Optional[dict] = None

    def prepare(self, **kwargs) -> Requirements:
        return Requirements(input_size=1)

    def _get_config(self, kwargs: dict) -> dict:
        """Resolve theme, template, and lyrics options from kwargs/env. Cached per kwargs identity to avoid 15+ lookups every frame."""
        kid = id(kwargs)
        if self._last_kwargs_id == kid and self._cached_config is not None:
            return self._cached_config
        self._last_kwargs_id = kid
        theme = kwargs.get("template_theme") or kwargs.get("templateTheme") or os.environ.get("SPOTIFY_TEMPLATE_THEME", "dreamy_abstract")
        custom = kwargs.get("prompt_template") or os.environ.get("SPOTIFY_PROMPT_TEMPLATE", "{lyrics}")
        if theme == "custom" or theme not in PROMPT_TEMPLATE_PRESETS:
            prompt_template = custom
        else:
            prompt_template = PROMPT_TEMPLATE_PRESETS[theme]
        fallback = kwargs.get("fallback_prompt") or os.environ.get("SPOTIFY_FALLBACK_PROMPT", "Abstract flowing colors and shapes")
        lyrics_max = int(kwargs.get("lyrics_max_chars", kwargs.get("lyricsMaxChars", 300)) or 0)
        keywords_only = kwargs.get("lyrics_keywords_only", kwargs.get("lyricsKeywordsOnly"))
        if keywords_only is None:
            keywords_only = os.environ.get("SPOTIFY_LYRICS_KEYWORDS_ONLY", "").lower() in ("1", "true", "yes")
        style_rotation_sec = float(kwargs.get("lyrics_style_rotation_seconds", kwargs.get("lyricsStyleRotationSeconds")) or 0)
        if style_rotation_sec <= 0:
            style_rotation_sec = float(os.environ.get("SPOTIFY_LYRICS_STYLE_ROTATION_SECONDS", "0") or 0)
        preview_sec = float(kwargs.get("lyrics_preview_seconds", kwargs.get("lyricsPreviewSeconds")) or 0)
        if preview_sec <= 0:
            preview_sec = float(os.environ.get("SPOTIFY_LYRICS_PREVIEW_SECONDS", "0") or 0)
        self._cached_config = {
            "theme": theme,
            "prompt_template": prompt_template,
            "fallback_prompt": fallback,
            "lyrics_max": lyrics_max,
            "keywords_only": keywords_only,
            "style_rotation_sec": style_rotation_sec,
            "preview_sec": preview_sec,
        }
        return self._cached_config

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
            n = max(1, self._time_count)
            avg_get_track = self._time_get_track_sum / n
            avg_lyrics = self._time_lyrics_sum / n
            avg_passthrough = self._time_passthrough_sum / n
            msg = (
                "Spotify preprocessor: pipeline FPS ≈ %.1f (preprocessor invoked %d times in %.1fs). "
                "Avg ms per frame: get_track=%.1f lyrics=%.1f passthrough=%.1f — use these to find what reduces FPS."
            ) % (fps, self._fps_invocation_count, elapsed, avg_get_track, avg_lyrics, avg_passthrough)
            logger.warning(msg)
            print(msg, flush=True)
            self._fps_invocation_count = 0
            self._fps_last_log_time = now
            self._time_get_track_sum = 0.0
            self._time_lyrics_sum = 0.0
            self._time_passthrough_sum = 0.0
            self._time_count = 0

        cfg = self._get_config(kwargs)
        template_theme = cfg["theme"]
        prompt_template = cfg["prompt_template"]
        fallback_prompt = cfg["fallback_prompt"]
        if self._last_logged_theme != template_theme:
            self._last_logged_theme = template_theme
            if template_theme == "custom":
                logger.warning("Spotify preprocessor: template_theme=custom, using Prompt Template from settings")
            else:
                logger.warning("Spotify preprocessor: template_theme=%s", template_theme)

        t0_get = time.perf_counter()
        try:
            client = self._get_spotify_client(kwargs)
            track = client.get_current_track()
        except Exception as e:
            logger.warning("Spotify get_current_track failed: %s", e)
            track = None
        t_get_track_ms = (time.perf_counter() - t0_get) * 1000

        t0_lyrics = time.perf_counter()
        if track is None or not track.is_playing:
            prompt = fallback_prompt
            self._synced_cache = None
            if self._last_logged_lyric_line != "_fallback_":
                self._last_logged_lyric_line = "_fallback_"
                logger.warning(
                    "Spotify preprocessor: no track playing or API failed. Using fallback. "
                    "Check SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and token at ~/.scope-spotify/.spotify_token_cache"
                )
        else:
            lyrics = ""
            lyrics_max = cfg["lyrics_max"]
            keywords_only = cfg["keywords_only"]
            style_rotation_sec = cfg["style_rotation_sec"]
            preview_sec = cfg["preview_sec"]
            # Built-in: always use time-synced lyrics (LRCLIB) and rotating style word
            cache = self._synced_cache
            if cache is None or cache[0] != track.track_id or cache[1] != track.duration_ms:
                duration_sec = max(1, track.duration_ms // 1000)
                lines = fetch_synced_lyrics(
                    track.artist, track.name, track.album, duration_sec
                )
                self._synced_cache = (track.track_id, track.duration_ms, lines)
                self._last_style_line = None
                if not lines:
                    logger.warning(
                        "Spotify preprocessor: no synced lyrics found for %s by %s (LRCLIB). Using title only.",
                        track.name, track.artist,
                    )
            else:
                lines = cache[2]
            progress_ms = track.progress_ms + int(preview_sec * 1000)
            lyrics = get_line_at_position(lines, progress_ms)
            # Rotating style word (built-in): advance by time or by line change
            if LYRICS_STYLE_WORDS:
                if style_rotation_sec > 0:
                    self._style_index = int(progress_ms / 1000.0 / style_rotation_sec) % len(LYRICS_STYLE_WORDS)
                else:
                    if self._last_style_line != lyrics:
                        self._last_style_line = lyrics
                        self._style_index = (self._style_index + 1) % len(LYRICS_STYLE_WORDS)
                style_word = LYRICS_STYLE_WORDS[self._style_index]
                lyrics = f"{lyrics}, {style_word}" if lyrics else style_word
            if keywords_only and lyrics:
                lyrics = lyrics_to_keywords(lyrics) or lyrics
            if lyrics and self._last_logged_lyric_line != lyrics:
                self._last_logged_lyric_line = lyrics
                sec = track.progress_ms // 1000
                logger.warning(
                    "Spotify preprocessor: synced lyric @ %d:%02d — %s",
                    sec // 60, sec % 60, lyrics[:80] + ("..." if len(lyrics) > 80 else ""),
                )

            format_kw: dict = {"song": track.name, "artist": track.artist, "lyrics": lyrics}
            try:
                prompt = prompt_template.format(**format_kw)
            except KeyError:
                prompt = f"{track.name} by {track.artist}" + (f": {lyrics}" if lyrics else "")

        t_lyrics_ms = (time.perf_counter() - t0_lyrics) * 1000

        # Log the actual prompt when it changes so you can see what's driving the image
        if prompt != getattr(self, "_last_logged_prompt", None):
            self._last_logged_prompt = prompt
            snippet = (prompt[:120] + "…") if len(prompt) > 120 else prompt
            logger.warning("Spotify preprocessor: prompt sent to pipeline: %s", snippet or "(empty)")

        t0_passthrough = time.perf_counter()
        out = self._passthrough(kwargs, prompt)
        t_passthrough_ms = (time.perf_counter() - t0_passthrough) * 1000
        self._time_get_track_sum += t_get_track_ms
        self._time_lyrics_sum += t_lyrics_ms
        self._time_passthrough_sum += t_passthrough_ms
        self._time_count += 1
        return out

    def _passthrough(self, kwargs: dict, prompt: str) -> dict:
        video = kwargs.get("video")
        if video is not None and len(video) > 0:
            frames = torch.stack([f.squeeze(0) for f in video], dim=0)
            # Only copy to device if needed (avoids redundant CPU→GPU when already on device)
            if frames.device != self.device or frames.dtype != torch.float32:
                frames = frames.to(device=self.device, dtype=torch.float32)
            frames = frames / 255.0
            frames.clamp_(0, 1)  # in-place to avoid extra tensor allocation
        else:
            frames = torch.zeros(1, 512, 512, 3, device=self.device)
        return {"video": frames, "prompt": prompt, "prompts": prompt}
