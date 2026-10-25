from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Nebius Token Factory
    nebius_api_key: str = Field(default="", alias="NEBIUS_API_KEY")
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.nebius.com/v1/",
        alias="NEBIUS_BASE_URL"
    )
    nebius_model: str = Field(
        default="nvidia/Llama-3.1-Nemotron-70B-Instruct",
        alias="NEBIUS_MODEL"
    )

    # GitHub
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    # Agent Loop
    autofix_max_iterations: int = Field(default=3, alias="AUTOFIX_MAX_ITERATIONS")
    autofix_timeout_seconds: int = Field(default=60, alias="AUTOFIX_TIMEOUT_SECONDS")
    autofix_mock_fallback: bool = Field(default=True, alias="AUTOFIX_MOCK_FALLBACK")

    # Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")


settings = Settings()
