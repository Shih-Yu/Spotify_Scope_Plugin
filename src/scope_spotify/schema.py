"""Configuration schema for the Spotify Prompt Generator pipeline."""

from pydantic import Field

from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, ui_field_config


class SpotifyConfig(BasePipelineConfig):
    """Configuration for the Spotify Prompt Generator pipeline."""

    pipeline_id = "spotify-prompts"
    pipeline_name = "Spotify Prompt Generator"
    pipeline_description = (
        "Generate AI image prompts from currently playing Spotify music. "
        "Uses song metadata and lyrics to create dynamic visual prompts."
    )

    supports_prompts = True
    modes = {"text": ModeDefaults(default=True)}

    # --- Spotify Authentication (Load-time params) ---

    spotify_client_id: str = Field(
        default="",
        description="Your Spotify API Client ID from developer.spotify.com",
        json_schema_extra=ui_field_config(
            order=1, 
            label="Spotify Client ID",
            is_load_param=True,
        ),
    )

    spotify_client_secret: str = Field(
        default="",
        description="Your Spotify API Client Secret from developer.spotify.com",
        json_schema_extra=ui_field_config(
            order=2, 
            label="Spotify Client Secret",
            is_load_param=True,
        ),
    )

    spotify_redirect_uri: str = Field(
        default="http://localhost:8888/callback",
        description="Redirect URI configured in your Spotify app settings",
        json_schema_extra=ui_field_config(
            order=3, 
            label="Redirect URI",
            is_load_param=True,
        ),
    )

    # --- Genius/Lyrics Authentication (Load-time params) ---

    genius_token: str = Field(
        default="",
        description="Genius API access token for fetching lyrics (optional for Phase 1)",
        json_schema_extra=ui_field_config(
            order=4, 
            label="Genius API Token",
            is_load_param=True,
        ),
    )

    # --- Prompt Generation Settings (Runtime params) ---

    prompt_mode: str = Field(
        default="title",
        description="What to use for prompt generation: 'title' (song info only) or 'lyrics'",
        json_schema_extra=ui_field_config(
            order=10, 
            label="Prompt Mode",
        ),
    )

    prompt_template: str = Field(
        default="A surreal, dreamlike artistic visualization of the song '{song}' by {artist}, {mood} atmosphere, cinematic lighting",
        description="Template for prompts. Variables: {song}, {artist}, {album}, {mood}, {genre}, {lyrics}",
        json_schema_extra=ui_field_config(
            order=11, 
            label="Prompt Template",
        ),
    )

    art_style: str = Field(
        default="surreal digital art",
        description="Art style to append to prompts",
        json_schema_extra=ui_field_config(
            order=12, 
            label="Art Style",
        ),
    )

    include_genre_style: bool = Field(
        default=True,
        description="Automatically add genre-based style hints to prompts",
        json_schema_extra=ui_field_config(
            order=13, 
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
            order=20, 
            label="Lyric Line Duration",
        ),
    )

    lyrics_lines_per_prompt: int = Field(
        default=2,
        ge=1,
        le=6,
        description="Number of lyric lines to combine per prompt",
        json_schema_extra=ui_field_config(
            order=21, 
            label="Lines Per Prompt",
        ),
    )

    # --- Fallback Settings ---

    fallback_prompt: str = Field(
        default="Abstract flowing colors and shapes, ambient music visualization, ethereal atmosphere",
        description="Prompt to use when no music is playing",
        json_schema_extra=ui_field_config(
            order=30, 
            label="Fallback Prompt",
        ),
    )
