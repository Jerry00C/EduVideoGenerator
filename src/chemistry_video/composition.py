"""FFmpeg-based scene audio/video composition."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, List, Protocol, Sequence

from .artifacts import LocalArtifactStore
from .domain import ArtifactRef, PlannedScene


class SceneComposer(Protocol):
    def compose_scene(
        self,
        *,
        video_id: str,
        scene: PlannedScene,
        scene_directory: Path,
        draft_video: Path,
        audio_files: Sequence[Path],
        artifacts: LocalArtifactStore,
    ) -> List[ArtifactRef]:
        """Mux one scene's visual and narration audio."""

    def concatenate(
        self,
        *,
        video_id: str,
        scene_files: Sequence[Path],
        artifacts: LocalArtifactStore,
    ) -> ArtifactRef:
        """Concatenate composed scenes into the final video."""


class FFmpegSceneComposer:
    def __init__(self, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe"):
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe

    def _run(self, command: Sequence[str], cwd: Path) -> Any:
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=300)

    def _duration(self, path: Path, cwd: Path) -> float:
        result = self._run(
            [self.ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", os.path.relpath(path, cwd)],
            cwd,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or f"ffprobe failed for {path}")
        return float(result.stdout.strip())

    def _check(self, result: Any, operation: str) -> None:
        if result.returncode != 0:
            raise RuntimeError(f"{operation} failed: {result.stderr or result.stdout}")

    def compose_scene(
        self,
        *,
        video_id: str,
        scene: PlannedScene,
        scene_directory: Path,
        draft_video: Path,
        audio_files: Sequence[Path],
        artifacts: LocalArtifactStore,
    ) -> List[ArtifactRef]:
        if not audio_files:
            raise ValueError(f"scene {scene.id} has no audio segments")
        scene_directory.mkdir(parents=True, exist_ok=True)
        concat_list = scene_directory / "audio_concat.txt"
        concat_list.write_text(
            "".join(
                f"file '{os.path.relpath(path, scene_directory)}'\n"
                for path in audio_files
            ),
            encoding="utf-8",
        )
        audio_path = scene_directory / "narration.mp3"
        result = self._run(
            [self.ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", concat_list.name, "-c:a", "libmp3lame", audio_path.name],
            scene_directory,
        )
        self._check(result, "audio concatenation")

        video_duration = self._duration(draft_video, scene_directory)
        audio_duration = self._duration(audio_path, scene_directory)
        target_duration = max(video_duration, audio_duration)
        video_pad = max(0.0, target_duration - video_duration)
        audio_pad = max(0.0, target_duration - audio_duration)
        output_path = scene_directory / "scene.mp4"
        result = self._run(
            [
                self.ffmpeg,
                "-y",
                "-i",
                os.path.relpath(draft_video, scene_directory),
                "-i",
                audio_path.name,
                "-filter_complex",
                f"[0:v]tpad=stop_mode=clone:stop_duration={video_pad:.3f}[v];[1:a]apad=pad_dur={audio_pad:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-t",
                f"{target_duration:.3f}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                output_path.name,
            ],
            scene_directory,
        )
        self._check(result, "scene audio/video composition")
        return [
            artifacts.write(video_id, f"scene_composition/{scene.id}/narration.mp3", audio_path.read_bytes(), "audio/mpeg"),
            artifacts.write(video_id, f"scene_composition/{scene.id}/scene.mp4", output_path.read_bytes(), "video/mp4"),
        ]

    def concatenate(self, *, video_id: str, scene_files: Sequence[Path], artifacts: LocalArtifactStore) -> ArtifactRef:
        if not scene_files:
            raise ValueError("no composed scenes to concatenate")
        root = artifacts.job_directory(video_id).resolve()
        upload_dir = root / "uploading"
        upload_dir.mkdir(parents=True, exist_ok=True)
        concat_list = upload_dir / "scenes.txt"
        concat_list.write_text("".join(f"file '{path.resolve()}'\n" for path in scene_files), encoding="utf-8")
        output_path = upload_dir / "final.mp4"
        result = self._run(
            [self.ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(output_path)],
            root,
        )
        self._check(result, "scene concatenation")
        return artifacts.write(video_id, "final.mp4", output_path.read_bytes(), "video/mp4")


class FakeSceneComposer:
    def compose_scene(self, *, video_id: str, scene: PlannedScene, scene_directory: Path, draft_video: Path, audio_files: Sequence[Path], artifacts: LocalArtifactStore) -> List[ArtifactRef]:
        return [artifacts.write(video_id, f"scene_composition/{scene.id}/scene.mp4", b"fake composed scene", "video/mp4")]

    def concatenate(self, *, video_id: str, scene_files: Sequence[Path], artifacts: LocalArtifactStore) -> ArtifactRef:
        return artifacts.write(video_id, "final.mp4", b"fake video artifact", "video/mp4")
