"""Main pipeline for generating prompts from Spotify music."""

import logging
from typing import TYPE_CHECKING, Optional

import torch

from scope.core.pipelines.interface import Pipeline, Requirements

from .lyrics_client import LyricsClient
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
        spotify_redirect_uri: str = "http://localhost:8888/callback",
        headless_mode: bool = True,
        genius_token: str = "",
        **kwargs,
    ):
        """Initialize the Spotify pipeline.
        
        Args:
            device: Torch device (not used, but required by interface)
            spotify_client_id: Spotify API Client ID
            spotify_client_secret: Spotify API Client Secret
            spotify_redirect_uri: OAuth redirect URI
            headless_mode: If True, use manual auth flow (for servers like RunPod)
            genius_token: Genius API token for lyrics
            **kwargs: Additional arguments (ignored)
        """
        self.device = device or torch.device("cpu")
        
        # Initialize clients
        self.spotify_client = SpotifyClient(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
            headless_mode=headless_mode,
        )
        
        self.lyrics_client = LyricsClient(genius_token=genius_token)
        
        # State tracking
        self._current_track: Optional[TrackInfo] = None
        self._current_lyrics_segment: Optional[str] = None
        
        logger.info(f"SpotifyPipeline initialized (headless_mode={headless_mode})")

    def prepare(self, **kwargs) -> Requirements:
        """Declare pipeline requirements.
        
        This pipeline doesn't process video frames, it generates prompts.
        """
        return Requirements(input_size=0)

    def __call__(self, **kwargs) -> dict:
        """Generate a prompt based on currently playing Spotify track or manual input.
        
        Args:
            **kwargs: Runtime parameters from the UI
            
        Returns:
            Dict with 'prompt' key containing the generated prompt
        """
        from .config_manager import get_config_manager
        
        # Get config manager for live config updates (edit ~/.scope-spotify/config.json)
        config = get_config_manager()
        
        # Get runtime parameters - priority: config file > env vars > kwargs > defaults
        import os
        input_source = config.get("input_source") or os.environ.get("SPOTIFY_INPUT_SOURCE") or kwargs.get("input_source", "manual")
        prompt_mode = config.get("prompt_mode") or os.environ.get("SPOTIFY_PROMPT_MODE") or kwargs.get("prompt_mode", "title")
        prompt_template = kwargs.get(
            "prompt_template",
            "A surreal, dreamlike artistic visualization of the song '{song}' by {artist}, {mood} atmosphere"
        )
        art_style = config.get("art_style") or os.environ.get("SPOTIFY_ART_STYLE") or kwargs.get("art_style", "surreal digital art")
        include_genre_style = kwargs.get("include_genre_style", True)
        fallback_prompt = kwargs.get(
            "fallback_prompt",
            "Abstract flowing colors and shapes, ambient music visualization"
        )
        lyrics_lines_per_prompt = config.get("lyrics_lines") or int(os.environ.get("SPOTIFY_LYRICS_LINES", "0") or kwargs.get("lyrics_lines_per_prompt", 2))
        
        # Get track info based on input source
        if input_source == "manual":
            # Manual mode - create TrackInfo from UI inputs
            track = self._get_manual_track(kwargs)
            logger.debug(f"Manual mode: {track.name} by {track.artist}")
        else:
            # Spotify mode - get from API
            track = self.spotify_client.get_current_track()
            
            if track is None or not track.is_playing:
                logger.debug("No track playing, using fallback prompt")
                return {"prompt": fallback_prompt}
        
        self._current_track = track
        
        # Build the prompt based on mode
        if prompt_mode == "lyrics":
            prompt = self._build_lyrics_prompt(
                track=track,
                template=prompt_template,
                art_style=art_style,
                include_genre=include_genre_style,
                lines_per_prompt=lyrics_lines_per_prompt,
            )
        else:
            # Default to title mode
            prompt = self._build_title_prompt(
                track=track,
                template=prompt_template,
                art_style=art_style,
                include_genre=include_genre_style,
            )
        
        logger.debug(f"Generated prompt: {prompt[:100]}...")
        return {"prompt": prompt}

    def _get_manual_track(self, kwargs: dict) -> TrackInfo:
        """Create a TrackInfo from config file, env vars, or UI inputs.
        
        Args:
            kwargs: Runtime parameters containing manual input values
            
        Returns:
            TrackInfo populated from manual inputs
        """
        import os
        from .config_manager import get_config_manager
        
        config = get_config_manager()
        
        # Priority: config file > env vars > kwargs > defaults
        song_title = config.get("song_title") or os.environ.get("SPOTIFY_SONG_TITLE") or kwargs.get("manual_song_title", "Unknown Song")
        artist = config.get("artist") or os.environ.get("SPOTIFY_ARTIST") or kwargs.get("manual_artist", "Unknown Artist")
        album = config.get("album") or os.environ.get("SPOTIFY_ALBUM") or kwargs.get("manual_album", "Unknown Album")
        genre = config.get("genre") or os.environ.get("SPOTIFY_GENRE") or kwargs.get("manual_genre", "")
        progress = config.get("progress") or float(os.environ.get("SPOTIFY_PROGRESS", "0") or kwargs.get("manual_progress", 0.0))
        
        # Parse genres (allow comma-separated)
        genres = [g.strip() for g in genre.split(",") if g.strip()]
        
        return TrackInfo(
            track_id=f"manual-{song_title}-{artist}".replace(" ", "-").lower(),
            name=song_title,
            artist=artist,
            album=album,
            duration_ms=300000,  # Assume 5 minute song for manual mode
            progress_ms=int(progress * 3000),  # Convert percentage to ms (of 5 min)
            is_playing=True,
            genres=genres,
        )

    def _build_title_prompt(
        self,
        track: TrackInfo,
        template: str,
        art_style: str,
        include_genre: bool,
    ) -> str:
        """Build a prompt using song title and metadata.
        
        Args:
            track: Current track information
            template: Prompt template string
            art_style: Art style to append
            include_genre: Whether to add genre-based style
            
        Returns:
            Generated prompt string
        """
        # Determine mood/genre style
        genre_style = ""
        if include_genre and track.genres:
            for genre in track.genres:
                genre_lower = genre.lower()
                for key, style in GENRE_STYLES.items():
                    if key in genre_lower:
                        genre_style = style
                        break
                if genre_style:
                    break
        
        # Format the template
        prompt = template.format(
            song=track.name,
            artist=track.artist,
            album=track.album,
            mood=genre_style or "ethereal",
            genre=", ".join(track.genres[:2]) if track.genres else "ambient",
            lyrics="",  # No lyrics in title mode
        )
        
        # Append art style
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
        """Build a prompt using song lyrics.
        
        Args:
            track: Current track information
            template: Prompt template string
            art_style: Art style to append
            include_genre: Whether to add genre-based style
            lines_per_prompt: Number of lyric lines per prompt
            
        Returns:
            Generated prompt string
        """
        # Try to get lyrics segment based on playback progress
        lyrics_segment = self.lyrics_client.get_lyrics_segment(
            song=track.name,
            artist=track.artist,
            progress_percent=track.progress_percent,
            lines_per_segment=lines_per_prompt,
        )
        
        self._current_lyrics_segment = lyrics_segment
        
        # If no lyrics found, fall back to title mode
        if not lyrics_segment:
            logger.debug(f"No lyrics found for {track.name}, using title mode")
            return self._build_title_prompt(track, template, art_style, include_genre)
        
        # Determine genre style
        genre_style = ""
        if include_genre and track.genres:
            for genre in track.genres:
                genre_lower = genre.lower()
                for key, style in GENRE_STYLES.items():
                    if key in genre_lower:
                        genre_style = style
                        break
                if genre_style:
                    break
        
        # Build lyrics-based prompt
        # Create a visual interpretation of the lyrics
        prompt = f"Artistic visualization of: \"{lyrics_segment}\" - from '{track.name}' by {track.artist}"
        
        if genre_style:
            prompt = f"{prompt}, {genre_style}"
        
        if art_style:
            prompt = f"{prompt}, {art_style}"
        
        return prompt

    def get_current_track_info(self) -> Optional[dict]:
        """Get info about the current track (for debugging/display).
        
        Returns:
            Dict with track info, or None
        """
        if self._current_track:
            return {
                "name": self._current_track.name,
                "artist": self._current_track.artist,
                "album": self._current_track.album,
                "progress": f"{self._current_track.progress_percent:.1f}%",
                "genres": self._current_track.genres,
                "lyrics_segment": self._current_lyrics_segment,
            }
        return None
