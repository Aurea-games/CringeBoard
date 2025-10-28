from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _parse_origins(raw_value: str) -> list[str]:
    """Split a comma-separated list of origins while trimming whitespace."""
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    project_name: str = "CringeBoard API"
    cors_origins: tuple[str, ...] = ()
    scheduler_interval: int = 60

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", tuple(self.cors_origins or ()))


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings sourced from environment variables."""
    cors_origins = _parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:3000"))

    return Settings(
        project_name=os.getenv("PROJECT_NAME", "CringeBoard API"),
        cors_origins=tuple(cors_origins),
        scheduler_interval=int(os.getenv("SCHEDULER_INTERVAL", "60")),
    )


__all__ = ["Settings", "get_settings"]
