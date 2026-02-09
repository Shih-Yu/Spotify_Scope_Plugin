# Scope Spotify Plugin

A [Daydream Scope](https://github.com/daydreamlive/scope) plugin that generates AI image prompts from your currently playing Spotify music.

## Features

- **Real-time Spotify Integration**: Automatically detects what you're listening to
- **Title Mode**: Generate prompts based on song title, artist, and genre
- **Lyrics Mode**: Generate prompts from actual song lyrics synced to playback
- **Genre-aware Styling**: Automatically adds visual style hints based on music genre
- **Customizable Templates**: Full control over prompt generation

## Installation

### Prerequisites

1. **Python 3.12+** and [uv](https://docs.astral.sh/uv/) package manager
2. **Daydream Scope** installed and running
3. **Spotify Developer Account** (free)
4. **Genius API Token** (optional, for lyrics)

### Get API Credentials

#### Spotify API

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your **Client ID** and **Client Secret**
4. Add `http://localhost:8888/callback` to Redirect URIs in app settings

#### Genius API (for Lyrics)

1. Go to [Genius API Clients](https://genius.com/api-clients)
2. Create a new API client
3. Generate an access token

### Install the Plugin

**Option 1: From GitHub**
```
git+https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
```

**Option 2: Local Development**
1. Clone this repository
2. In Scope, go to Settings > Plugins
3. Click Browse and select the `scope-spotify` folder

## Configuration

After installing, select **Spotify Prompt Generator** from the pipeline dropdown.

### Required Settings (Load-time)

| Setting | Description |
|---------|-------------|
| Spotify Client ID | Your Spotify API Client ID |
| Spotify Client Secret | Your Spotify API Client Secret |
| Redirect URI | OAuth callback URL (default: `http://localhost:8888/callback`) |
| Genius API Token | For lyrics fetching (optional) |

### Runtime Settings

| Setting | Description |
|---------|-------------|
| Prompt Mode | `title` (song info) or `lyrics` |
| Prompt Template | Customizable template with variables |
| Art Style | Style to append to all prompts |
| Include Genre Style | Auto-add genre-based visual hints |
| Lyric Line Duration | Seconds per lyric line |
| Lines Per Prompt | Lyric lines to combine |
| Fallback Prompt | Used when no music playing |

### Template Variables

Use these in your prompt template:
- `{song}` - Song title
- `{artist}` - Artist name
- `{album}` - Album name
- `{mood}` - Auto-detected mood from genre
- `{genre}` - Music genre
- `{lyrics}` - Current lyrics segment (lyrics mode only)

## Usage

1. Start playing music on Spotify
2. Launch Scope and select **Spotify Prompt Generator**
3. Enter your API credentials in the settings
4. The plugin will authenticate with Spotify (browser opens for first-time auth)
5. Prompts are automatically generated from your music!

### First-time Authentication

On first run, a browser window will open asking you to authorize the app with Spotify. After authorizing, you'll be redirected to a localhost URL. The authentication token is cached for future sessions.

## Development

### Local Development Setup

```bash
# Clone the repo
git clone https://github.com/Shih-Yu/Sptoffy_Scope_Plugin.git
cd Sptoffy_Scope_Plugin/scope-spotify

# Install in development mode
pip install -e .
```

### Testing Spotify Connection

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
