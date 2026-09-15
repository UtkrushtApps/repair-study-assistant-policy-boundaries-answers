from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_base_url: str
    assistant_model: str
    database_url: str


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        assistant_model=os.getenv("ASSISTANT_MODEL", "gpt-4o-mini"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://study:study@localhost:5432/study_assistant",
        ),
    )
