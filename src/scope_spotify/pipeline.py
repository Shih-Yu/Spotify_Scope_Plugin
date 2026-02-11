"""Main pipeline for generating prompts from Spotify music."""

import logging
import os
from typing import TYPE_CHECKING, Optional

import torch

from scope.core.pipelines.interface import Pipeline, Requirements

from .schema import SpotifyConfig
from .spotify_client import SpotifyClient, TrackInfo

if TYPE_CHECKING:
    from scope.core.pipelines.base_schema import BasePipelineConfig

logger = logging.getLogger(__name__)


# Genre to visual style mapping
GENRE_STYLES = {
    "rock": "bold contrasts, electric energy, raw textures",
    "pop": "vibrant colors, glossy finish, modern aesthetic",
    "hip hop": "urban landscape, street art style, bold typography",
    "rap": "urban landscape, street art style, bold typography",
    "electronic": "neon lights, digital artifacts, futuristic",
    "edm": "neon lights, laser beams, euphoric atmosphere",
    "jazz": "smoky atmosphere, warm tones, vintage feel",
    "classical": "elegant, orchestral grandeur, timeless beauty",
    "r&b": "smooth gradients, sensual mood, soft lighting",
    "soul": "warm golden tones, emotional depth, vintage warmth",
    "country": "rustic landscapes, golden hour, americana",
    "folk": "earthy tones, natural textures, handcrafted feel",
    "metal": "dark imagery, intense energy, dramatic lighting",
    "punk": "anarchic energy, DIY aesthetic, raw and unpolished",
    "indie": "dreamy atmosphere, soft focus, artistic flair",
    "alternative": "abstract shapes, moody lighting, experimental",
    "reggae": "tropical colors, laid-back vibes, sunshine",
    "blues": "deep blues, melancholic mood, soulful expression",
    "ambient": "ethereal fog, peaceful atmosphere, soft gradients",
    "techno": "geometric patterns, industrial aesthetic, hypnotic",
}


def _get_genre_style(genres: list[str]) -> str:
    """Look up a visual style string from a list of genre tags.

    Args:
        genres: Genre strings (e.g. from Spotify artist info).

    Returns:
        Matching style description, or empty string if no match.
    """
    for genre in genres:
        genre_lower = genre.lower()
        for key, style in GENRE_STYLES.items():
            if key in genre_lower:
                return style
    return ""


class SpotifyPipeline(Pipeline):
    """Pipeline that generates prompts from Spotify music playback."""

    @classmethod
    def get_config_class(cls) -> type["BasePipelineConfig"]:
        return SpotifyConfig

    def __init__(
        self,
        device: torch.device | None = None,
        spotify_client_id: str = "",
        spotify_client_secret: str = "",
        spotify_redirect_uri: str = "http://127.0.0.1:8888/callback",
        headless_mode: bool = True,
        **kwargs,
    ):
        self.device = (
            device
            if device is not None
            else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        )

        # Fall back to env vars for credentials (essential for RunPod)
        spotify_client_id = spotify_client_id or os.environ.get("SPOTIFY_CLIENT_ID", "")
        spotify_client_secret = spotify_client_secret or os.environ.get("SPOTIFY_CLIENT_SECRET", "")
        spotify_redirect_uri = spotify_redirect_uri or os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

        # Initialize Spotify client
        self.spotify_client = SpotifyClient(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
            headless_mode=headless_mode,
        )

        # State tracking
        self._current_track: Optional[TrackInfo] = None

        logger.info(f"SpotifyPipeline initialized (headless_mode={headless_mode})")

    def prepare(self, **kwargs) -> Requirements:
        """Declare that we need one input frame to pass through."""
        return Requirements(input_size=1)

    # ------------------------------------------------------------------
    # Parameter resolution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve(kwargs: dict, config: dict, key_kwargs: str, key_config: str,
                 env_var: str | None, default):
        """Resolve a parameter with correct priority: kwargs > env > config > default.

        UI controls (kwargs) should always win when the user sets them.
        """
        # kwargs from the Scope UI
        val = kwargs.get(key_kwargs)
        if val is not None:
            return val

        # Environment variable override
        if env_var:
            env_val = os.environ.get(env_var)
            if env_val is not None:
                return env_val

        # Config file value
        cfg_val = config.get(key_config)
        if cfg_val is not None:
            return cfg_val

        return default

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def __call__(self, **kwargs) -> dict:
        """Generate a prompt and pass through the input video frames.

        Returns:
            Dict with "video" (THWC float32 [0,1]) and "prompt" (str).
        """
        from .config_manager import get_config_manager

        config = get_config_manager().get_all()

        # Resolve runtime parameters (kwargs > env > config > defaults)
        input_source = self._resolve(
            kwargs, config, "input_source", "input_source",
            "SPOTIFY_INPUT_SOURCE", "manual",
        )
        prompt_mode = self._resolve(
            kwargs, config, "prompt_mode", "prompt_mode",
            "SPOTIFY_PROMPT_MODE", "title",
        )
        prompt_template = kwargs.get(
            "prompt_template",
            "A surreal, dreamlike artistic visualization of the song '{song}' by {artist}, {mood} atmosphere, cinematic lighting",
        )
        art_style = self._resolve(
            kwargs, config, "art_style", "art_style",
            "SPOTIFY_ART_STYLE", "surreal digital art",
        )
        include_genre_style = kwargs.get("include_genre_style", True)
        fallback_prompt = kwargs.get(
            "fallback_prompt",
            "Abstract flowing colors and shapes, ambient music visualization",
        )
        lyrics_lines_per_prompt = int(self._resolve(
            kwargs, config, "lyrics_lines_per_prompt", "lyrics_lines",
            "SPOTIFY_LYRICS_LINES", 2,
        ))

        # --- Get track info ---
        if input_source == "manual":
            track = self._get_manual_track(kwargs, config)
            logger.debug(f"Manual mode: {track.name} by {track.artist}")
        else:
            track = self.spotify_client.get_current_track()
            if track is None or not track.is_playing:
                logger.debug("No track playing, using fallback prompt")
                return self._passthrough(kwargs, fallback_prompt)

        self._current_track = track

        # --- Build prompt ---
        if prompt_mode == "lyrics":
            prompt = self._build_lyrics_prompt(
                track=track,
                template=prompt_template,
                art_style=art_style,
                include_genre=include_genre_style,
                lines_per_prompt=lyrics_lines_per_prompt,
            )
        else:
            prompt = self._build_title_prompt(
                track=track,
                template=prompt_template,
                art_style=art_style,
                include_genre=include_genre_style,
            )

        logger.debug(f"Generated prompt: {prompt[:100]}...")
        return self._passthrough(kwargs, prompt)

    # ------------------------------------------------------------------
    # Video passthrough
    # ------------------------------------------------------------------

    def _passthrough(self, kwargs: dict, prompt: str) -> dict:
        """Pass through input video frames and attach the generated prompt.

        A preprocessor must return {"video": tensor} so the downstream
        pipeline receives valid frames. We also forward the prompt.
        """
        video = kwargs.get("video")

        if video is not None and len(video) > 0:
            frames = torch.stack([f.squeeze(0) for f in video], dim=0)
            frames = frames.to(device=self.device, dtype=torch.float32) / 255.0
        else:
            # Text-only mode — generate a single black frame as placeholder
            frames = torch.zeros(1, 512, 512, 3, device=self.device)

        return {"video": frames.clamp(0, 1), "prompt": prompt}

    # ------------------------------------------------------------------
    # Track helpers
    # ------------------------------------------------------------------

    def _get_manual_track(self, kwargs: dict, config: dict) -> TrackInfo:
        """Create a TrackInfo from UI inputs, env vars, or config file."""
        song_title = self._resolve(
            kwargs, config, "manual_song_title", "song_title",
            "SPOTIFY_SONG_TITLE", "Unknown Song",
        )
        artist = self._resolve(
            kwargs, config, "manual_artist", "artist",
            "SPOTIFY_ARTIST", "Unknown Artist",
        )
        album = self._resolve(
            kwargs, config, "manual_album", "album",
            "SPOTIFY_ALBUM", "Unknown Album",
        )
        genre = self._resolve(
            kwargs, config, "manual_genre", "genre",
            "SPOTIFY_GENRE", "",
        )
        progress = float(self._resolve(
            kwargs, config, "manual_progress", "progress",
            "SPOTIFY_PROGRESS", 0.0,
        ))

        genres = [g.strip() for g in str(genre).split(",") if g.strip()]

        return TrackInfo(
            track_id=f"manual-{song_title}-{artist}".replace(" ", "-").lower(),
            name=song_title,
            artist=artist,
            album=album,
            duration_ms=300000,  # Assume 5-minute song for manual mode
            progress_ms=int(progress * 3000),  # percentage -> ms of 5 min
            is_playing=True,
            genres=genres,
        )

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_title_prompt(
        self,
        track: TrackInfo,
        template: str,
        art_style: str,
        include_genre: bool,
    ) -> str:
        """Build a prompt using song title and metadata."""
        genre_style = _get_genre_style(track.genres) if include_genre else ""

        prompt = template.format(
            song=track.name,
            artist=track.artist,
            album=track.album,
            mood=genre_style or "ethereal",
            genre=", ".join(track.genres[:2]) if track.genres else "ambient",
            lyrics="",
        )

        if art_style:
            prompt = f"{prompt}, {art_style}"

        return prompt

    def _build_lyrics_prompt(
        self,
        track: TrackInfo,
        template: str,
        art_style: str,
        include_genre: bool,
        lines_per_prompt: int,
    ) -> str:
        """Build a prompt; lyrics mode uses title + metadata (no external lyrics API)."""
        # No lyrics source configured — use title-based prompt; {lyrics} stays empty
        logger.debug("Lyrics mode: using title/metadata (no lyrics API)")
        return self._build_title_prompt(track, template, art_style, include_genre)
