# Scope Spotify Plugin

A [Daydream Scope](https://github.com/daydreamlive/scope) plugin that generates AI image prompts from your currently playing Spotify music.

## Features

- **Manual Mode**: Test prompt generation without Spotify API — just enter song details manually
- **Real-time Spotify Integration**: Automatically detects what you're listening to (with Spotify app credentials)
- **Title Mode**: Generate prompts based on song title, artist, album, and genre
- **Lyrics Mode**: Uses title/metadata (no external lyrics API; extendable later)
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
3. **Spotify Developer App** (only needed for live Spotify mode — see below)

### Install the Plugin

**Option 1: From GitHub**

Use the **HTTPS** URL. Do **not** use the SSH form (`git@github.com:...`) — it can cause install failures and 422 errors:
```
https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
```
If Scope expects a pip-style URL, use:
```
git+https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
```
If you still get "dependency conflict", check the server logs for the exact conflicting package; the plugin only requires Python ≥3.10 and `spotipy` (no version pin).

**Option 2: Local Development**
1. Clone this repository
2. In Scope, go to Settings > Plugins
3. Click Browse and select the `scope-spotify` folder

### What You Need for Spotify (Live Playback)

To use **Spotify mode** (live “now playing” from your account), you need a **Spotify app** and credentials:

| What | Where to get it |
|------|------------------|
| **Spotify Developer Account** | [developer.spotify.com](https://developer.spotify.com) — sign in with your Spotify account |
| **Create an app** | [Dashboard](https://developer.spotify.com/dashboard) → Create app → name it (e.g. “Scope Spotify”) |
| **Client ID** | App dashboard → copy **Client ID** |
| **Client Secret** | App dashboard → click **Show client secret** → copy **Client Secret** |
| **Redirect URI** | In app settings, add: `http://127.0.0.1:8888/callback` (Spotify requires 127.0.0.1, not localhost) |

Put these in `.env.local` or in the plugin’s load-time settings:

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI` (default `http://127.0.0.1:8888/callback`)

**Manual mode** works with no API keys — you can test everything by entering song title, artist, and genre.

## Where to Find the Plugin in Scope

The plugin is a **Preprocessor**, not a main pipeline. The "Input Mode" dropdown (Text / Video) is Scope’s built-in setting — our options are under the **Preprocessor**:

1. **Select your main pipeline** (e.g. an image or video generation model) in the main pipeline selector.
2. **Add or select the Preprocessor**: open the **Preprocessor** dropdown (or “Add preprocessor” step) and choose **Spotify Prompt Generator**.
3. Once it’s selected, the **Input** panel should show:
   - **Input Source** — `manual` (enter song yourself) or `spotify` (use what’s playing).
   - **Song Title**, **Artist**, **Album**, **Genre** (for manual mode).
   - **Playback Progress %** (for testing).

If you don’t see these, check for a preprocessor/settings area for the current pipeline; Spotify Prompt Generator’s controls appear when it is the active preprocessor.

**Spotify mode:** Yes — you need to **start playing a track** in the Spotify app first. The plugin reads the “currently playing” track from the Spotify API, so something must be playing (or have just played) on the same account you authorized.

## Lyrics / Karaoke-Style Prompts

Spotify’s in-app karaoke (synced “sing along” lyrics) is **not** available to third-party apps via the public Web API. Right now the plugin builds prompts from **song title, artist, album, and genre** (and optional progress %). There is no line-by-line synced lyrics yet.

- **Current behavior:** “Lyrics” mode still uses title/metadata only (no external lyrics API).
- **Possible later step:** We could add a lyrics provider (e.g. Musixmatch or another API) so prompts update line-by-line for a karaoke-style experience. That would require an extra API/key and is not implemented yet.

## Configuration

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

### API Settings (Load-time, for Spotify mode)

| Setting | Description |
|---------|-------------|
| Spotify Client ID | Your Spotify app Client ID |
| Spotify Client Secret | Your Spotify app Client Secret |
| Redirect URI | OAuth callback URL (default: `http://127.0.0.1:8888/callback`) |
| Headless/Server Mode | Enable for RunPod/servers — uses manual auth flow |

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

## RunPod / Server Deployment

This plugin is designed to work on headless servers like RunPod.

### Manual Mode on RunPod (Recommended Start)

Manual mode works immediately on RunPod with no additional setup:
1. Install the plugin
2. Use `manual` input source
3. Enter song details or use env vars (e.g. `SPOTIFY_SONG_TITLE`, `SPOTIFY_ARTIST`)

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
- [x] Phase 2: Spotify app integration (live playback)
- [ ] Phase 3: Time-synced lyrics (optional lyrics API)
- [ ] Phase 4: LLM-enhanced prompt generation
- [ ] Phase 5: Mood/sentiment analysis for colors

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [Daydream Scope](https://github.com/daydreamlive/scope) — Real-time AI video platform
- [Spotipy](https://github.com/spotipy-dev/spotipy) — Spotify Web API wrapper
