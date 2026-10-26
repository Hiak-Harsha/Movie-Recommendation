"""
CineMatch API Configuration (pydantic-settings)
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    app_name: str = "CineMatch API"
    version: str = "2.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Path settings
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    artifacts_dir: Path = Path(__file__).resolve().parent.parent.parent / "artifacts"
    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data"

    # Database settings (SQLite default)
    database_url: str = "sqlite:///./data/cinematch.db"

    # TMDB Integration (optional, API key never exposed to client)
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p/w500"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_prefix="CINEMATCH_API_",
        case_sensitive=False,
        extra="ignore"
    )


api_settings = APISettings()
