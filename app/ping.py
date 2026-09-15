from __future__ import annotations

from app.config import get_settings
from app.llm_client import LLMClient


def main() -> None:
    LLMClient(get_settings()).ping()
    print("model ping ok")


if __name__ == "__main__":
    main()
