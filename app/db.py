from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


@contextmanager
def connection() -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(get_settings().database_url, row_factory=dict_row) as conn:
        yield conn


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(query, params)
        return list(cursor.fetchall())


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(query, params)
        conn.commit()
