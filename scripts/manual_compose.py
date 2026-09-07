#!/usr/bin/env python3
"""Manually compose existing draft scene videos and narration audio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from chemistry_video.artifacts import LocalArtifactStore
from chemistry_video.composition import FFmpegSceneComposer
from chemistry_video.domain import ScenePlan


def compose_job(video_id: str, artifacts_root: Path) -> List[str]:
    store = LocalArtifactStore(artifacts_root)
    scene_plan_path = store.resolve(video_id, "scene_plan.json")
    scene_plan = ScenePlan.model_validate_json(scene_plan_path.read_text(encoding="utf-8"))
    composer = FFmpegSceneComposer()
    composed_scenes: List[Path] = []
    output_paths: List[str] = []

    for scene in scene_plan.scenes:
        scene_root = f"scene_composition/{scene.id}"
        draft_path = store.resolve(video_id, f"draft_visual/{scene.id}/scene.mp4")
        if not draft_path.is_file():
            raise FileNotFoundError(f"missing draft video: {draft_path}")

        copied_draft = store.write(
            video_id,
            f"{scene_root}/draft_scene.mp4",
            draft_path.read_bytes(),
            "video/mp4",
        )
        audio_paths = []
        for segment in scene.narration_segments:
            source = store.resolve(video_id, f"audio/{segment.id}.mp3")
            if not source.is_file():
                raise FileNotFoundError(f"missing narration audio: {source}")
            copied_audio = store.write(
                video_id,
                f"{scene_root}/audio/{segment.id}.mp3",
                source.read_bytes(),
                "audio/mpeg",
            )
            audio_paths.append(store.resolve(video_id, copied_audio.path))

        composer.compose_scene(
            video_id=video_id,
            scene=scene,
            scene_directory=store.resolve(video_id, scene_root),
            draft_video=draft_path,
            audio_files=audio_paths,
            artifacts=store,
        )
        composed_path = store.resolve(video_id, f"{scene_root}/scene.mp4")
        composed_scenes.append(composed_path)
        output_paths.extend([copied_draft.path, *(f"{scene_root}/audio/{segment.id}.mp3" for segment in scene.narration_segments), f"{scene_root}/scene.mp4"])

    final_ref = composer.concatenate(video_id=video_id, scene_files=composed_scenes, artifacts=store)
    output_paths.append(final_ref.path)
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_id", help="Existing video artifact ID, such as vid_abc123")
    parser.add_argument("--artifacts-root", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    print(json.dumps({"video_id": args.video_id, "artifacts": compose_job(args.video_id, args.artifacts_root)}, indent=2))


if __name__ == "__main__":
    main()
