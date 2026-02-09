"""Lyrics client for fetching song lyrics from Genius API."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class LyricsClient:
    """Client for fetching lyrics from Genius API."""
    
    def __init__(self, genius_token: str = ""):
        """Initialize the lyrics client.
        
        Args:
            genius_token: Genius API access token
        """
        self.genius_token = genius_token
        self._genius = None
        self._cache: dict[str, list[str]] = {}
    
    def _ensure_client(self):
        """Ensure we have an initialized Genius client."""
        if self._genius is None:
            if not self.genius_token:
                raise ValueError(
                    "Genius API token not configured. "
                    "Get one at genius.com/api-clients"
                )
            
            try:
                import lyricsgenius
                self._genius = lyricsgenius.Genius(self.genius_token)
                self._genius.verbose = False
                self._genius.remove_section_headers = True
                logger.info("Genius client initialized successfully")
            except ImportError:
                raise ImportError(
                    "lyricsgenius package not installed. "
                    "Install with: pip install lyricsgenius"
                )
    
    def get_lyrics(self, song: str, artist: str) -> list[str]:
        """Fetch lyrics for a song and return as list of lines.
        
        Args:
            song: Song title
            artist: Artist name
            
        Returns:
            List of lyric lines, or empty list if not found
        """
        cache_key = f"{artist.lower()}:{song.lower()}"
        
        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Lyrics cache hit for: {song} by {artist}")
            return self._cache[cache_key]
        
        try:
            self._ensure_client()
            
            logger.info(f"Fetching lyrics for: {song} by {artist}")
            result = self._genius.search_song(song, artist)
            
            if result is None:
                logger.warning(f"No lyrics found for: {song} by {artist}")
                self._cache[cache_key] = []
                return []
            
            # Clean up lyrics
            lines = self._parse_lyrics(result.lyrics)
            self._cache[cache_key] = lines
            
            logger.info(f"Found {len(lines)} lyric lines for: {song}")
            return lines
            
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            return []
    
    def _parse_lyrics(self, raw_lyrics: str) -> list[str]:
        """Parse raw lyrics into clean lines.
        
        Args:
            raw_lyrics: Raw lyrics text from Genius
            
        Returns:
            List of cleaned lyric lines
        """
        if not raw_lyrics:
            return []
        
        lines = []
        for line in raw_lyrics.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip section headers like [Verse 1], [Chorus], etc.
            if re.match(r'^\[.*\]$', line):
                continue
            
            # Skip contributor info that Genius sometimes includes
            if line.endswith("Lyrics"):
                continue
            if "Embed" in line:
                continue
            
            # Clean up the line
            line = re.sub(r'\s+', ' ', line)  # Normalize whitespace
            
            if line:
                lines.append(line)
        
        return lines
    
    def get_lyrics_segment(
        self,
        song: str,
        artist: str,
        progress_percent: float,
        lines_per_segment: int = 2,
    ) -> Optional[str]:
        """Get a segment of lyrics based on playback progress.
        
        Args:
            song: Song title
            artist: Artist name
            progress_percent: Playback progress (0-100)
            lines_per_segment: Number of lines to return
            
        Returns:
            Lyric segment string, or None if no lyrics
        """
        lyrics = self.get_lyrics(song, artist)
        
        if not lyrics:
            return None
        
        # Calculate which segment we're at based on progress
        total_segments = max(1, len(lyrics) // lines_per_segment)
        segment_index = int((progress_percent / 100) * total_segments)
        segment_index = min(segment_index, total_segments - 1)
        
        # Get the lines for this segment
        start_line = segment_index * lines_per_segment
        end_line = min(start_line + lines_per_segment, len(lyrics))
        
        segment_lines = lyrics[start_line:end_line]
        
        if segment_lines:
            return " / ".join(segment_lines)
        
        return None
    
    def clear_cache(self):
        """Clear the lyrics cache."""
        self._cache.clear()
        logger.debug("Lyrics cache cleared")
