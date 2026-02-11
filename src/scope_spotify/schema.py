"""Configuration schema for the Spotify Prompt Generator pipeline."""

from pydantic import Field

from scope.core.pipelines.base_schema import BasePipelineConfig, ModeDefaults, UsageType, ui_field_config


class SpotifyConfig(BasePipelineConfig):
    """Configuration for the Spotify Prompt Generator pipeline.

    Minimal: current Spotify track -> one prompt -> preprocessor for Scope.
    """

    pipeline_id = "spotify-prompts"
    pipeline_name = "Spotify Prompt Generator"
    pipeline_description = (
        "Generate an image prompt from the current Spotify song title. "
        "Use as a PREPROCESSOR with Stream Diffusion (or any image pipeline)."
    )

    usage = [UsageType.PREPROCESSOR]
    supports_prompts = True
    modes = {"video": ModeDefaults(default=True), "text": ModeDefaults()}

    # --- Spotify credentials (from UI or env) ---
    spotify_client_id: str = Field(
        default="",
        description="Spotify API Client ID from developer.spotify.com",
        json_schema_extra=ui_field_config(order=10, label="Spotify Client ID", category="configuration"),
    )
    spotify_client_secret: str = Field(
        default="",
        description="Spotify API Client Secret",
        json_schema_extra=ui_field_config(order=11, label="Spotify Client Secret", category="configuration"),
    )
    spotify_redirect_uri: str = Field(
        default="http://127.0.0.1:8888/callback",
        description="Redirect URI (must match your Spotify app settings)",
        json_schema_extra=ui_field_config(order=12, label="Redirect URI", category="configuration"),
    )
    headless_mode: bool = Field(
        default=True,
        description="Enable for servers (RunPod); use manual auth flow",
        json_schema_extra=ui_field_config(order=13, label="Headless Mode", category="configuration"),
    )

    # --- Single prompt template ---
    prompt_template: str = Field(
        default="Artistic visualization of {song} by {artist}",
        description="Prompt template. Use {song} and {artist}.",
        json_schema_extra=ui_field_config(order=20, label="Prompt Template", category="configuration"),
    )
    fallback_prompt: str = Field(
        default="Abstract flowing colors and shapes",
        description="Prompt when no track is playing",
        json_schema_extra=ui_field_config(order=21, label="Fallback Prompt", category="configuration"),
    )
