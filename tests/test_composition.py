from pathlib import Path
from types import SimpleNamespace

from chemistry_video.artifacts import LocalArtifactStore
from chemistry_video.composition import FFmpegSceneComposer
from chemistry_video.domain import PlannedScene, SceneNarrationSegment, VisualBeat


def make_scene():
    return PlannedScene(
        id="scene-1",
        purpose="Explain",
        estimated_duration_seconds=10,
        narration_segments=[
            SceneNarrationSegment(id="narration-1", text="An atom is one unit."),
            SceneNarrationSegment(id="narration-2", text="A molecule has bonded atoms."),
        ],
        visual_beats=[
            VisualBeat(
                id="visual-1",
                trigger_narration_id="narration-1",
                trigger_phrase="An atom",
                action="Show an atom",
                visual_type="atom_diagram",
            )
        ],
    )


def test_scene_composer_pads_and_normalizes_audio(tmp_path: Path):
    commands = []
    scene_directory = tmp_path / "scene"
    scene_directory.mkdir()
    draft_video = scene_directory / "draft_scene.mp4"
    audio_directory = scene_directory / "audio"
    audio_directory.mkdir()
    audio_one = audio_directory / "one.mp3"
    audio_two = audio_directory / "two.mp3"
    for path in (draft_video, audio_one, audio_two):
        path.write_bytes(b"input")

    def runner(command, cwd):
        commands.append(command)
        if command[0] == "ffprobe":
            return SimpleNamespace(returncode=0, stdout="4.0\n", stderr="")
        if "-c:a" in command and "libmp3lame" in command:
            (cwd / "narration.mp3").write_bytes(b"audio")
        else:
            (cwd / "scene.mp4").write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    composer = FFmpegSceneComposer()
    composer._run = runner
    artifacts = LocalArtifactStore(tmp_path / "artifacts")

    refs = composer.compose_scene(
        video_id="vid_test",
        scene=make_scene(),
        scene_directory=scene_directory,
        draft_video=draft_video,
        audio_files=[audio_one, audio_two],
        artifacts=artifacts,
    )

    mux_command = commands[-1]
    filter_graph = mux_command[mux_command.index("-filter_complex") + 1]
    concat_list = (scene_directory / "audio_concat.txt").read_text()
    assert "audio/one.mp3" in concat_list
    assert "audio/two.mp3" in concat_list
    assert "tpad=" in filter_graph
    assert "apad=" in filter_graph
    assert "loudnorm=" in filter_graph
    assert "libx264" in mux_command
    assert "aac" in mux_command
    assert {ref.path for ref in refs} == {
        "scene_composition/scene-1/narration.mp3",
        "scene_composition/scene-1/scene.mp4",
    }


def test_scene_composer_concatenates_scene_files(tmp_path: Path):
    commands = []
    scene_one = tmp_path / "scene-one.mp4"
    scene_two = tmp_path / "scene-two.mp4"
    scene_one.write_bytes(b"one")
    scene_two.write_bytes(b"two")

    def runner(command, cwd):
        commands.append(command)
        (cwd / "uploading" / "final.mp4").write_bytes(b"final")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    composer = FFmpegSceneComposer()
    composer._run = runner
    artifacts = LocalArtifactStore(tmp_path / "artifacts")
    result = composer.concatenate(
        video_id="vid_test",
        scene_files=[scene_one, scene_two],
        artifacts=artifacts,
    )

    assert result.path == "final.mp4"
    assert commands[0][0:6] == ["ffmpeg", "-y", "-f", "concat", "-safe", "0"]
    assert "-c" in commands[0]
    assert commands[0][commands[0].index("-c") + 1] == "copy"


def test_concat_uses_absolute_paths_with_relative_artifact_root(tmp_path: Path):
    commands = []
    artifact_root = tmp_path / "artifacts"
    store = LocalArtifactStore(artifact_root)
    scene_file = tmp_path / "scene.mp4"
    scene_file.write_bytes(b"scene")

    def runner(command, cwd):
        commands.append(command)
        output_path = cwd / "uploading" / "final.mp4"
        output_path.write_bytes(b"final")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    composer = FFmpegSceneComposer()
    composer._run = runner
    composer.concatenate(video_id="vid_test", scene_files=[scene_file], artifacts=store)

    concat_input = commands[0][commands[0].index("-i") + 1]
    assert Path(concat_input).is_absolute()
