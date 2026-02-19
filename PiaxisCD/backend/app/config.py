from __future__ import annotations

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "PiaxisCD"
    debug: bool = True
    database_url: str = "mysql+aiomysql://root@localhost:3306/piaxiscd"
    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data"
    cors_origins: list[str] = ["http://localhost:5173"]
    default_seed: int = 42

    model_config = {"env_prefix": "PIAXIS_"}


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
