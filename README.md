# Scope Spotify Plugin

A [Daydream Scope](https://github.com/daydreamlive/scope) plugin that generates AI image prompts from your currently playing Spotify music.

## Features

- **Manual Mode**: Test prompt generation without Spotify API - just enter song details manually
- **Real-time Spotify Integration**: Automatically detects what you're listening to (when API available)
- **Title Mode**: Generate prompts based on song title, artist, and genre
- **Lyrics Mode**: Generate prompts from actual song lyrics synced to playback
- **Genre-aware Styling**: Automatically adds visual style hints based on music genre
- **Customizable Templates**: Full control over prompt generation

## Quick Start (Manual Mode)

**No API keys required!** You can test the plugin immediately using Manual Mode:

1. Install the plugin in Scope
2. Select **Spotify Prompt Generator** from the pipeline dropdown
3. Set **Input Source** to `manual` (default)
4. Enter a song title, artist, and genre
5. Prompts are generated instantly!

This is perfect for testing and development, or when Spotify API access is unavailable.

## Installation

### Prerequisites

1. **Python 3.12+** and [uv](https://docs.astral.sh/uv/) package manager
2. **Daydream Scope** installed and running
3. **Genius API Token** (optional, for lyrics in manual mode)
4. **Spotify Developer Account** (only needed for live Spotify mode)

### Install the Plugin

**Option 1: From GitHub**
```
git+https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
```

**Option 2: Local Development**
1. Clone this repository
2. In Scope, go to Settings > Plugins
3. Click Browse and select the `scope-spotify` folder

### Get API Credentials (Optional)

#### Genius API (for Lyrics) - Recommended

1. Go to [Genius API Clients](https://genius.com/api-clients)
2. Create a new API client
3. Generate an access token
4. Works with both manual and Spotify modes!

#### Spotify API (for Live Playback)

> **Note:** As of February 2026, Spotify has temporarily paused new app creation. Check the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) for current status.

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your **Client ID** and **Client Secret**
4. Add `http://localhost:8888/callback` to Redirect URIs in app settings

## Configuration

After installing, select **Spotify Prompt Generator** from the pipeline dropdown.

### Manual Mode Settings (Runtime)

| Setting | Description |
|---------|-------------|
| Input Source | `manual` or `spotify` - choose where to get song info |
| Song Title | Song name for prompt generation |
| Artist | Artist name |
| Album | Album name |
| Genre | Music genre (rock, pop, electronic, jazz, etc.) |
| Playback Progress % | Simulate playback position (0-100%) for lyrics sync |

### Prompt Settings (Runtime)

| Setting | Description |
|---------|-------------|
| Prompt Mode | `title` (song info) or `lyrics` |
| Prompt Template | Customizable template with variables |
| Art Style | Style to append to all prompts |
| Include Genre Style | Auto-add genre-based visual hints |
| Lines Per Prompt | Lyric lines to combine |
| Fallback Prompt | Used when no music playing (Spotify mode only) |

### API Settings (Load-time, optional)

| Setting | Description |
|---------|-------------|
| Genius API Token | For lyrics fetching (works in manual mode too!) |
| Spotify Client ID | Your Spotify API Client ID (only for Spotify mode) |
| Spotify Client Secret | Your Spotify API Client Secret (only for Spotify mode) |
| Redirect URI | OAuth callback URL (default: `http://localhost:8888/callback`) |
| Headless/Server Mode | Enable for RunPod/servers - uses manual auth flow |

### Template Variables

Use these in your prompt template:
- `{song}` - Song title
- `{artist}` - Artist name
- `{album}` - Album name
- `{mood}` - Auto-detected mood from genre
- `{genre}` - Music genre
- `{lyrics}` - Current lyrics segment (lyrics mode only)

## Usage

### Manual Mode (No API Required)

1. Launch Scope and select **Spotify Prompt Generator**
2. Keep **Input Source** set to `manual`
3. Enter song details (title, artist, genre)
4. Adjust the **Playback Progress %** slider to test lyrics sync
5. Watch prompts generate based on your input!

### Spotify Mode (Live Playback)

1. Get API credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Enter credentials in the plugin settings
3. Set **Input Source** to `spotify`
4. Start playing music on Spotify
5. The plugin will authenticate (browser opens for first-time auth)
6. Prompts are automatically generated from your live playback!

### Adding Lyrics

To enable lyrics-based prompts:

1. Get a free API token from [Genius](https://genius.com/api-clients)
2. Enter the token in **Genius API Token** setting
3. Set **Prompt Mode** to `lyrics`
4. Lyrics will be fetched and used for visual prompts!

## RunPod / Server Deployment

This plugin is designed to work on headless servers like RunPod.

### Manual Mode on RunPod (Recommended Start)

Manual mode works immediately on RunPod with no additional setup:
1. Install the plugin
2. Use `manual` input source
3. Optionally add Genius API token for lyrics

### Spotify Mode on RunPod (When API Available)

Since RunPod doesn't have a browser, use the authentication helper script:

```bash
# SSH into your RunPod instance
cd /path/to/scope-spotify

# Run the auth helper
python scripts/spotify_auth.py
```

The script will:
1. Ask for your Spotify credentials
2. Give you a URL to visit in your local browser
3. You authorize the app and copy the redirect URL back
4. Token is cached for the plugin to use

Alternatively, authenticate locally first and copy the token cache:
```bash
# Local machine - run auth
python scripts/spotify_auth.py

# Copy cache to RunPod
scp ~/.scope-spotify/.spotify_token_cache runpod:~/.scope-spotify/
```

## Development

### Local Development Setup

```bash
# Clone the repo
git clone https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
cd Spotify_Scope_Plugin/scope-spotify

# Install in development mode
pip install -e .
```

### Testing Prompt Generation (Manual Mode)

```python
from scope_spotify.spotify_client import TrackInfo
from scope_spotify.pipeline import SpotifyPipeline

# Create pipeline (no API keys needed for manual mode)
pipeline = SpotifyPipeline()

# Test with manual input
result = pipeline(
    input_source="manual",
    manual_song_title="Bohemian Rhapsody",
    manual_artist="Queen",
    manual_genre="rock",
    prompt_mode="title",
)

print(result["prompt"])
```

### Testing Spotify Connection (when API available)

```python
from scope_spotify.spotify_client import SpotifyClient

client = SpotifyClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)

track = client.get_current_track()
if track:
    print(f"Now playing: {track.name} by {track.artist}")
```

## Roadmap

- [x] Phase 1: Basic song title/metadata prompts
- [x] Phase 2: Lyrics integration via Genius API
- [ ] Phase 3: Time-synced lyrics (Musixmatch/LRC)
- [ ] Phase 4: LLM-enhanced prompt generation
- [ ] Phase 5: Mood/sentiment analysis for colors

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [Daydream Scope](https://github.com/daydreamlive/scope) - Real-time AI video platform
- [Spotipy](https://github.com/spotipy-dev/spotipy) - Spotify Web API wrapper
- [LyricsGenius](https://github.com/johnwmillr/LyricsGenius) - Genius API wrapper
