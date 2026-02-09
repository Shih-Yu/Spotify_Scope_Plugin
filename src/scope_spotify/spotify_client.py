"""Spotify API client for fetching currently playing track information."""

import logging
from dataclasses import dataclass
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)


@dataclass
class TrackInfo:
    """Information about the currently playing track."""
    
    track_id: str
    name: str
    artist: str
    album: str
    duration_ms: int
    progress_ms: int
    is_playing: bool
    genres: list[str]
    
    @property
    def progress_percent(self) -> float:
        """Get playback progress as a percentage (0-100)."""
        if self.duration_ms == 0:
            return 0.0
        return (self.progress_ms / self.duration_ms) * 100


class SpotifyClient:
    """Client for interacting with the Spotify Web API."""
    
    SCOPES = [
        "user-read-currently-playing",
        "user-read-playback-state",
    ]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8888/callback",
    ):
        """Initialize the Spotify client with OAuth credentials.
        
        Args:
            client_id: Spotify API Client ID
            client_secret: Spotify API Client Secret
            redirect_uri: OAuth redirect URI (must match Spotify app settings)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._spotify: Optional[spotipy.Spotify] = None
        self._last_track_id: Optional[str] = None
        
    def _ensure_authenticated(self) -> spotipy.Spotify:
        """Ensure we have an authenticated Spotify client."""
        if self._spotify is None:
            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "Spotify credentials not configured. "
                    "Please set Client ID and Client Secret in the pipeline settings."
                )
            
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=" ".join(self.SCOPES),
                open_browser=True,
            )
            self._spotify = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Spotify client authenticated successfully")
            
        return self._spotify
    
    def get_current_track(self) -> Optional[TrackInfo]:
        """Get information about the currently playing track.
        
        Returns:
            TrackInfo if a track is playing, None otherwise.
        """
        try:
            sp = self._ensure_authenticated()
            current = sp.current_user_playing_track()
            
            if current is None or current.get("item") is None:
                logger.debug("No track currently playing")
                return None
            
            track = current["item"]
            artist_ids = [artist["id"] for artist in track["artists"] if artist.get("id")]
            
            # Fetch genres from artist info
            genres = []
            if artist_ids:
                try:
                    artists_info = sp.artists(artist_ids[:1])  # Get first artist's genres
                    if artists_info and artists_info.get("artists"):
                        genres = artists_info["artists"][0].get("genres", [])
                except Exception as e:
                    logger.warning(f"Could not fetch artist genres: {e}")
            
            track_info = TrackInfo(
                track_id=track["id"],
                name=track["name"],
                artist=", ".join(artist["name"] for artist in track["artists"]),
                album=track["album"]["name"],
                duration_ms=track["duration_ms"],
                progress_ms=current.get("progress_ms", 0),
                is_playing=current.get("is_playing", False),
                genres=genres,
            )
            
            # Log when track changes
            if track_info.track_id != self._last_track_id:
                logger.info(f"Now playing: {track_info.name} by {track_info.artist}")
                self._last_track_id = track_info.track_id
            
            return track_info
            
        except spotipy.SpotifyException as e:
            logger.error(f"Spotify API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            return None
    
    def is_track_changed(self, track_info: Optional[TrackInfo]) -> bool:
        """Check if the track has changed since last check.
        
        Args:
            track_info: Current track info to compare
            
        Returns:
            True if track changed, False otherwise
        """
        if track_info is None:
            changed = self._last_track_id is not None
            self._last_track_id = None
            return changed
        
        changed = track_info.track_id != self._last_track_id
        return changed
