"""Local artifact storage for generated video outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, List

from .domain import ArtifactManifest, ArtifactRef, utc_now


class LocalArtifactStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def job_directory(self, video_id: str) -> Path:
        directory = self.root / video_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write(self, video_id: str, relative_path: str, content: bytes, media_type: str) -> ArtifactRef:
        path = self.job_directory(video_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return ArtifactRef(
            artifact_id=f"{video_id}:{relative_path}",
            path=relative_path,
            media_type=media_type,
            size_bytes=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
        )

    def resolve(self, video_id: str, relative_path: str) -> Path:
        root = self.job_directory(video_id).resolve()
        path = (root / relative_path).resolve()
        if root != path and root not in path.parents:
            raise ValueError("artifact path escapes job directory")
        return path

    def manifest(self, video_id: str, files: Iterable[ArtifactRef], final_video_artifact_id: str) -> ArtifactManifest:
        manifest = ArtifactManifest(
            artifact_id=f"{video_id}:manifest",
            video_id=video_id,
            files=list(files),
            created_at=utc_now(),
            final_video_artifact_id=final_video_artifact_id,
        )
        self.write(
            video_id,
            "artifact_manifest.json",
            manifest.model_dump_json(indent=2).encode("utf-8"),
            "application/json",
        )
        return manifest
