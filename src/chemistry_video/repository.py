"""SQLite persistence for video jobs."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from .domain import VideoResponse


class SQLiteJobRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS video_jobs (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

    def create(self, job: VideoResponse) -> VideoResponse:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO video_jobs (id, payload) VALUES (?, ?)",
                (job.id, job.model_dump_json()),
            )
        return job

    def get(self, video_id: str) -> Optional[VideoResponse]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM video_jobs WHERE id = ?", (video_id,)
            ).fetchone()
        return VideoResponse.model_validate_json(row["payload"]) if row else None

    def list(self) -> List[VideoResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM video_jobs ORDER BY rowid"
            ).fetchall()
        return [VideoResponse.model_validate_json(row["payload"]) for row in rows]

    def update(self, job: VideoResponse) -> VideoResponse:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE video_jobs SET payload = ? WHERE id = ?",
                (job.model_dump_json(), job.id),
            )
            if cursor.rowcount != 1:
                raise KeyError(job.id)
        return job
