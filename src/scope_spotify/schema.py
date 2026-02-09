"""Configuration schema for the Spotify Prompt Generator pipeline."""

from pydantic import Field

from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, ui_field_config


class SpotifyConfig(BasePipelineConfig):
    """Configuration for the Spotify Prompt Generator pipeline."""

    pipeline_id = "spotify-prompts"
    pipeline_name = "Spotify Prompt Generator"
    pipeline_description = (
        "Generate AI image prompts from currently playing Spotify music. "
        "Uses song metadata and lyrics to create dynamic visual prompts. "
        "Supports manual input mode for testing without Spotify API."
    )

    supports_prompts = True
    modes = {"text": ModeDefaults(default=True)}

    # --- Input Source Selection (Runtime - top of UI) ---

    input_source: str = Field(
        default="manual",
        description="Where to get song info: 'manual' (enter song details) or 'spotify' (live playback)",
        json_schema_extra=ui_field_config(
            order=0,
            label="Input Source",
        ),
    )

    # --- Manual Input Fields (Runtime params) ---

    manual_song_title: str = Field(
        default="Bohemian Rhapsody",
        description="Song title for manual mode",
        json_schema_extra=ui_field_config(
            order=1,
            label="Song Title",
        ),
    )

    manual_artist: str = Field(
        default="Queen",
        description="Artist name for manual mode",
        json_schema_extra=ui_field_config(
            order=2,
            label="Artist",
        ),
    )

    manual_album: str = Field(
        default="A Night at the Opera",
        description="Album name for manual mode",
        json_schema_extra=ui_field_config(
            order=3,
            label="Album",
        ),
    )

    manual_genre: str = Field(
        default="rock",
        description="Genre for manual mode (rock, pop, electronic, jazz, classical, hip hop, etc.)",
        json_schema_extra=ui_field_config(
            order=4,
            label="Genre",
        ),
    )

    manual_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Simulated playback progress (0-100%) for lyrics sync testing",
        json_schema_extra=ui_field_config(
            order=5,
            label="Playback Progress %",
        ),
    )

    # --- Spotify Authentication (Load-time params) ---

    spotify_client_id: str = Field(
        default="",
        description="Your Spotify API Client ID from developer.spotify.com (not needed for manual mode)",
        json_schema_extra=ui_field_config(
            order=50, 
            label="Spotify Client ID",
            is_load_param=True,
        ),
    )

    spotify_client_secret: str = Field(
        default="",
        description="Your Spotify API Client Secret from developer.spotify.com (not needed for manual mode)",
        json_schema_extra=ui_field_config(
            order=51, 
            label="Spotify Client Secret",
            is_load_param=True,
        ),
    )

    spotify_redirect_uri: str = Field(
        default="http://localhost:8888/callback",
        description="Redirect URI configured in your Spotify app settings",
        json_schema_extra=ui_field_config(
            order=52, 
            label="Redirect URI",
            is_load_param=True,
        ),
    )

    # --- Genius/Lyrics Authentication (Load-time params) ---

    genius_token: str = Field(
        default="",
        description="Genius API access token for fetching lyrics (get one at genius.com/api-clients)",
        json_schema_extra=ui_field_config(
            order=53, 
            label="Genius API Token",
            is_load_param=True,
        ),
    )

    # --- Prompt Generation Settings (Runtime params) ---

    prompt_mode: str = Field(
        default="title",
        description="What to use for prompt generation: 'title' (song info only) or 'lyrics'",
        json_schema_extra=ui_field_config(
            order=60, 
            label="Prompt Mode",
        ),
    )

    prompt_template: str = Field(
        default="A surreal, dreamlike artistic visualization of the song '{song}' by {artist}, {mood} atmosphere, cinematic lighting",
        description="Template for prompts. Variables: {song}, {artist}, {album}, {mood}, {genre}, {lyrics}",
        json_schema_extra=ui_field_config(
            order=61, 
            label="Prompt Template",
        ),
    )

    art_style: str = Field(
        default="surreal digital art",
        description="Art style to append to prompts",
        json_schema_extra=ui_field_config(
            order=62, 
            label="Art Style",
        ),
    )

    include_genre_style: bool = Field(
        default=True,
        description="Automatically add genre-based style hints to prompts",
        json_schema_extra=ui_field_config(
            order=63, 
            label="Include Genre Style",
        ),
    )

    # --- Lyrics Settings (Runtime params) ---

    lyrics_line_duration: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Seconds to display each lyric line before moving to next",
        json_schema_extra=ui_field_config(
            order=70, 
            label="Lyric Line Duration",
        ),
    )

    lyrics_lines_per_prompt: int = Field(
        default=2,
        ge=1,
        le=6,
        description="Number of lyric lines to combine per prompt",
        json_schema_extra=ui_field_config(
            order=71, 
            label="Lines Per Prompt",
        ),
    )

    # --- Fallback Settings ---

    fallback_prompt: str = Field(
        default="Abstract flowing colors and shapes, ambient music visualization, ethereal atmosphere",
        description="Prompt to use when no music is playing (Spotify mode only)",
        json_schema_extra=ui_field_config(
            order=80, 
            label="Fallback Prompt",
        ),
    )
