"""Spotify API client for fetching currently playing track information.

Uses the spotipy package (pip install spotipy), imported as spotify in code.
"""

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import spotipy as spotify
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

# Default cache location for Spotify tokens
DEFAULT_CACHE_DIR = Path.home() / ".scope-spotify"
DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / ".spotify_token_cache"


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
    """Client for interacting with the Spotify Web API.
    
    Supports both browser-based OAuth (for local development) and
    manual authentication flow (for headless servers like RunPod).
    """
    
    SCOPES = [
        "user-read-currently-playing",
        "user-read-playback-state",
    ]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8888/callback",
        cache_path: Optional[str] = None,
        headless_mode: bool = False,
    ):
        """Initialize the Spotify client with OAuth credentials.
        
        Args:
            client_id: Spotify API Client ID
            client_secret: Spotify API Client Secret
            redirect_uri: OAuth redirect URI (must match Spotify app settings)
            cache_path: Optional custom path for token cache file
            headless_mode: If True, don't try to open browser (for servers)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.headless_mode = headless_mode
        self._spotify: Optional[spotify.Spotify] = None
        self._last_track_id: Optional[str] = None
        self._auth_manager: Optional[SpotifyOAuth] = None
        # Cache current track to avoid calling Spotify API every frame (large FPS impact)
        self._track_cache: Optional[Tuple[float, Optional["TrackInfo"]]] = None  # (monotonic_time, track)
        try:
            self._track_cache_ttl = float(os.environ.get("SPOTIFY_TRACK_CACHE_SECONDS", "0.4"))
        except (TypeError, ValueError):
            self._track_cache_ttl = 0.4

        # Set up cache path
        if cache_path:
            self.cache_path = Path(cache_path)
        else:
            self.cache_path = DEFAULT_CACHE_FILE
        
        # Ensure cache directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_auth_manager(self) -> SpotifyOAuth:
        """Get or create the OAuth manager."""
        if self._auth_manager is None:
            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "Spotify credentials not configured. "
                    "Please set Client ID and Client Secret in the pipeline settings."
                )
            
            self._auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=" ".join(self.SCOPES),
                cache_path=str(self.cache_path),
                open_browser=not self.headless_mode,
            )
        return self._auth_manager
    
    def get_auth_url(self) -> str:
        """Get the authorization URL for manual authentication.
        
        Use this on headless servers (like RunPod) where browser auth isn't possible.
        
        Returns:
            URL to visit in a browser to authorize the app
        """
        auth_manager = self._get_auth_manager()
        return auth_manager.get_authorize_url()
    
    def complete_auth(self, redirect_url_or_code: str) -> bool:
        """Complete authentication with the redirect URL or authorization code.
        
        After visiting the auth URL and authorizing, you'll be redirected to
        a URL like: http://127.0.0.1:8888/callback?code=AQD...
        
        Pass either the full redirect URL or just the code parameter.
        
        Args:
            redirect_url_or_code: The full redirect URL or just the auth code
            
        Returns:
            True if authentication succeeded, False otherwise
        """
        try:
            auth_manager = self._get_auth_manager()
            
            # Extract code if full URL provided
            if "code=" in redirect_url_or_code:
                # Parse the code from the URL
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(redirect_url_or_code)
                code = parse_qs(parsed.query).get("code", [None])[0]
            else:
                code = redirect_url_or_code
            
            if not code:
                logger.error("No authorization code found")
                return False
            
            # Exchange code for token
            auth_manager.get_access_token(code, as_dict=False)
            logger.info("Spotify authentication completed successfully!")
            logger.info(f"Token cached at: {self.cache_path}")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if we have valid cached credentials.
        
        Returns:
            True if we have a valid (or refreshable) token cached
        """
        try:
            auth_manager = self._get_auth_manager()
            token_info = auth_manager.get_cached_token()
            return token_info is not None
        except Exception:
            return False
        
    def _ensure_authenticated(self) -> spotify.Spotify:
        """Ensure we have an authenticated Spotify client."""
        if self._spotify is None:
            auth_manager = self._get_auth_manager()
            
            # Check for cached token first
            token_info = auth_manager.get_cached_token()
            
            if token_info is None and self.headless_mode:
                # On headless server without cached token, provide instructions
                auth_url = self.get_auth_url()
                logger.error("=" * 60)
                logger.error("SPOTIFY AUTHENTICATION REQUIRED")
                logger.error("=" * 60)
                logger.error("Running on headless server - manual auth needed.")
                logger.error("")
                logger.error("Step 1: Visit this URL in your browser:")
                logger.error(f"  {auth_url}")
                logger.error("")
                logger.error("Step 2: After authorizing, you'll be redirected to a URL like:")
                logger.error("  http://127.0.0.1:8888/callback?code=AQD...")
                logger.error("")
                logger.error("Step 3: Copy the ENTIRE redirect URL from your browser")
                logger.error("")
                logger.error("Step 4: On THIS server (where Scope runs), in a terminal run:")
                logger.error("  cd /app/Spotify_Scope_Plugin   # or wherever the repo is cloned (e.g. /app)")
                logger.error("  python3 -m pip install spotipy   # if needed")
                logger.error("  python3 scripts/spotify_auth.py")
                logger.error("  When prompted, paste the redirect URL. Token saves to ~/.scope-spotify/")
                logger.error("  Then RESTART Scope so it picks up the token.")
                logger.error("=" * 60)
                raise ValueError(
                    "Spotify authentication required. See logs for instructions. "
                    "Or use Manual mode until authenticated."
                )
            
            self._spotify = spotify.Spotify(auth_manager=auth_manager)
            logger.info("Spotify client authenticated successfully")
            
        return self._spotify
    
    def get_current_track(self) -> Optional[TrackInfo]:
        """Get information about the currently playing track.
        Results are cached for SPOTIFY_TRACK_CACHE_SECONDS (default 0.4s) to avoid
        calling the API every frame, which would severely reduce FPS.
        """
        now = time.monotonic()
        if self._track_cache is not None and (now - self._track_cache[0]) < self._track_cache_ttl:
            return self._track_cache[1]
        try:
            sp = self._ensure_authenticated()
            current = sp.current_user_playing_track()

            if current is None or current.get("item") is None:
                logger.debug("No track currently playing")
                self._track_cache = (now, None)
                return None

            track = current["item"]
            track_info = TrackInfo(
                track_id=track["id"],
                name=track["name"],
                artist=", ".join(artist["name"] for artist in track["artists"]),
                album=track["album"]["name"],
                duration_ms=track["duration_ms"],
                progress_ms=current.get("progress_ms", 0),
                is_playing=current.get("is_playing", False),
                genres=[],
            )
            self._track_cache = (now, track_info)

            if track_info.track_id != self._last_track_id:
                logger.info("Now playing: %s by %s", track_info.name, track_info.artist)
                self._last_track_id = track_info.track_id

            return track_info

        except spotify.SpotifyException as e:
            logger.error("Spotify API error: %s", e)
            self._track_cache = (now, None)
            return None
        except Exception as e:
            logger.error("Error getting current track: %s", e)
            self._track_cache = (now, None)
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
