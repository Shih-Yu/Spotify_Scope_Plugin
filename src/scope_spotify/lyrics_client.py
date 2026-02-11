"""Fetch lyrics by song title and artist. Supports synced (LRC) and plain lyrics.

- LRCLIB (free, no API key): time-synced lyrics so the prompt can follow the current line.
- Lyrics.ovh (free, no API key): plain lyrics fallback when synced not available.
"""

import json
import logging
import re
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

# LRCLIB: synced lyrics; requires track_name, artist_name, album_name, duration (seconds)
LRCLIB_GET = "https://lrclib.net/api/get"
# Lyrics.ovh: plain lyrics; artist + title in path
LYRICS_OVH_BASE = "https://api.lyrics.ovh/v1"

# LRC line: [mm:ss.xx] or [m:ss.xx] or [mm:ss] then optional text
LRC_LINE_RE = re.compile(r"^\[(\d+):(\d{2})(?:\.(\d{2,3}))?\]\s*(.*)$")


def _parse_lrc_line(line: str) -> tuple[int, str] | None:
    """Parse one LRC line to (start_ms, text). Returns None if not a valid timestamp line."""
    line = line.strip()
    m = LRC_LINE_RE.match(line)
    if not m:
        return None
    minutes, seconds, frac, text = m.groups()
    minutes = int(minutes)
    seconds = int(seconds)
    frac = frac or "0"
    # LRC: .12 = 120ms (hundredths), .123 = 123ms (milliseconds)
    if len(frac) == 2:
        frac_ms = int(frac) * 10
    else:
        frac_ms = int(frac.ljust(3, "0")[:3])
    ms = minutes * 60 * 1000 + seconds * 1000 + frac_ms
    return (ms, (text or "").strip())


def parse_synced_lrc(synced_lrc: str) -> list[tuple[int, str]]:
    """Parse LRC string to list of (start_ms, text) sorted by time. Skips empty/invalid lines."""
    lines: list[tuple[int, str]] = []
    for raw in synced_lrc.split("\n"):
        parsed = _parse_lrc_line(raw)
        if parsed and parsed[1]:
            lines.append(parsed)
    lines.sort(key=lambda x: x[0])
    return lines


def get_line_at_position(synced_lines: list[tuple[int, str]], progress_ms: int) -> str:
    """Return the lyric line at the given playback position (ms). Empty if before first line."""
    if not synced_lines:
        return ""
    current = ""
    for start_ms, text in synced_lines:
        if start_ms <= progress_ms:
            current = text
        else:
            break
    return current


def fetch_synced_lyrics(
    artist: str,
    title: str,
    album: str,
    duration_sec: int,
) -> list[tuple[int, str]]:
    """Fetch time-synced lyrics from LRCLIB. Returns list of (start_ms, text) or empty list on failure.

    duration_sec should match the track duration (Spotify duration_ms // 1000). LRCLIB matches within ±2s.
    """
    if not artist or not title:
        return []
    try:
        q = {
            "track_name": title.strip(),
            "artist_name": artist.strip(),
            "album_name": (album or "").strip() or "Unknown",
            "duration": max(1, int(duration_sec)),
        }
        query = urllib.parse.urlencode(q)
        url = f"{LRCLIB_GET}?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "ScopeSpotifyPlugin/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status != 200:
                return []
            data = json.loads(resp.read().decode())
            raw = (data.get("syncedLyrics") or "").strip()
            if not raw:
                return []
            return parse_synced_lrc(raw)
    except Exception as e:
        logger.debug("LRCLIB fetch failed for %s by %s: %s", title, artist, e)
        return []


def fetch_plain_lyrics(artist: str, title: str, max_chars: int = 500) -> str:
    """Get plain lyrics from Lyrics.ovh. Returns empty string if not found or on error."""
    if not artist or not title:
        return ""
    try:
        path_artist = urllib.parse.quote(artist.strip())
        path_title = urllib.parse.quote(title.strip())
        url = f"{LYRICS_OVH_BASE}/{path_artist}/{path_title}"
        req = urllib.request.Request(url, headers={"User-Agent": "ScopeSpotifyPlugin/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return ""
            data = json.loads(resp.read().decode())
            raw = (data.get("lyrics") or "").strip()
            one_line = " ".join(raw.split())
            if max_chars > 0 and len(one_line) > max_chars:
                one_line = one_line[:max_chars].rstrip() + "..."
            return one_line
    except Exception as e:
        logger.debug("Lyrics.ovh fetch failed for %s by %s: %s", title, artist, e)
        return ""
