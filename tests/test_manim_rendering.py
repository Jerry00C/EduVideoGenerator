from pathlib import Path
from types import SimpleNamespace

import pytest

from chemistry_video.artifacts import LocalArtifactStore
from chemistry_video.domain import (
    AudioPlan,
    PlannedScene,
    SceneNarrationSegment,
    ScenePlan,
    VisualBeat,
)
from chemistry_video.manim_rendering import (
    ManimRenderer,
    OpenAIVisualCritic,
    build_code_prompt,
    capture_sample_frames,
    extract_manim_code,
    scene_class_name,
)


def make_scene_plan():
    scene = PlannedScene(
        id="scene_1_big_idea",
        purpose="Introduce atoms",
        estimated_duration_seconds=10,
        narration_segments=[SceneNarrationSegment(id="narration-1", text="An atom is one unit.")],
        visual_beats=[
            VisualBeat(
                id="visual-1",
                trigger_narration_id="narration-1",
                trigger_phrase="An atom",
                action="Show one atom",
                visual_type="atom_diagram",
                on_screen_text="Atom",
            )
        ],
    )
    return ScenePlan(
        title="Atoms",
        target_duration_seconds=240,
        scenes=[scene],
        audio_plan=AudioPlan(
            voice_style="friendly tutor",
            speaking_rate="moderate",
            segment_ids=["narration-1"],
        ),
        estimated_total_duration_seconds=10,
    )


def test_scene_prompt_and_code_extraction_use_scene_plan():
    plan = make_scene_plan()
    class_name = scene_class_name(plan.scenes[0].id)
    prompt = build_code_prompt(plan.scenes[0], plan, class_name)

    assert class_name == "Scene1BigIdeaScene"
    assert "An atom is one unit." in prompt
    assert "atom_diagram" in prompt
    assert extract_manim_code(f"Here is the code:\n```python\nclass {class_name}(Scene):\n    pass\n```") == (
        f"class {class_name}(Scene):\n    pass"
    )


def test_capture_sample_frames_runs_ffmpeg_and_returns_pngs(tmp_path: Path):
    captured = {}

    def frame_runner(command, cwd):
        captured["command"] = command
        assert cwd == tmp_path / "frames"
        (cwd / "frame_00.png").write_bytes(b"png")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    frames = capture_sample_frames(tmp_path / "scene.mp4", tmp_path / "frames", frame_runner)

    assert frames == [tmp_path / "frames" / "frame_00.png"]
    assert str(tmp_path / "scene.mp4") not in captured["command"]
    assert "../scene.mp4" in captured["command"]
    assert "frame_%02d.png" in captured["command"]


@pytest.mark.asyncio
async def test_openai_visual_critic_uses_gpt4o_supported_verbosity(tmp_path: Path):
    class Responses:
        def __init__(self):
            self.request = None

        async def create(self, **kwargs):
            self.request = kwargs
            return SimpleNamespace(output_text="OK")

    responses = Responses()
    critic = OpenAIVisualCritic.__new__(OpenAIVisualCritic)
    critic.model = "gpt-4o"
    critic.client = SimpleNamespace(responses=responses)
    frame = tmp_path / "frame.png"
    frame.write_bytes(b"png")

    result = await critic.inspect(scene=make_scene_plan().scenes[0], frame_paths=[frame])

    assert result == ""
    assert responses.request["model"] == "gpt-4o"
    assert responses.request["text"] == {"verbosity": "medium"}


@pytest.mark.asyncio
async def test_renderer_uses_frame_feedback_to_repair_and_rerender(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.prompts = []

        async def generate(self, prompt):
            self.prompts.append(prompt)
            return _generated_code()

    class Critic:
        def __init__(self):
            self.calls = 0

        async def inspect(self, *, scene, frame_paths):
            self.calls += 1
            assert frame_paths
            return "Move the title down so it does not overlap the top edge." if self.calls == 1 else ""

    render_count = 0

    def runner(command, cwd):
        nonlocal render_count
        render_count += 1
        media_path = cwd / "media" / "videos" / f"attempt_{render_count}" / "scene.mp4"
        media_path.parent.mkdir(parents=True, exist_ok=True)
        media_path.write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="rendered", stderr="")

    def frame_runner(command, cwd):
        (cwd / "frame_00.png").write_bytes(b"png")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    provider = Provider()
    critic = Critic()
    renderer = ManimRenderer(
        provider,
        runner=runner,
        critic=critic,
        frame_runner=frame_runner,
        max_layout_feedback_attempts=1,
    )
    artifacts = LocalArtifactStore(tmp_path)
    plan = make_scene_plan()

    generated = await renderer.render_scene(
        video_id="vid_feedback",
        scene_plan=plan,
        scene=plan.scenes[0],
        artifacts=artifacts,
    )

    assert render_count == 2
    assert critic.calls == 1
    assert len(provider.prompts) == 2
    assert "Move the title down" in provider.prompts[1]
    assert any(path.endswith("final_code.json") for path in [artifact.path for artifact in generated])


@pytest.mark.asyncio
async def test_renderer_repairs_failed_manim_and_persists_final_code(tmp_path: Path):
    class Provider:
        def __init__(self):
            self.prompts = []

        async def generate(self, prompt):
            self.prompts.append(prompt)
            if len(self.prompts) == 1:
                return "```python\nfrom manim import *\nclass Scene1BigIdeaScene(Scene):\n    pass\n```"
            return "```python\nfrom manim import *\nclass Scene1BigIdeaScene(Scene):\n    def construct(self):\n        self.add(Text('fixed'))\n```"

    results = [
        SimpleNamespace(returncode=1, stdout="", stderr="SyntaxError: bad code"),
        SimpleNamespace(returncode=0, stdout="rendered", stderr=""),
    ]

    def runner(command, cwd):
        if results[0].returncode == 0:
            (cwd / "media" / "videos" / "attempt_2" / "scene.mp4").parent.mkdir(parents=True)
            (cwd / "media" / "videos" / "attempt_2" / "scene.mp4").write_bytes(b"video")
        return results.pop(0)

    provider = Provider()
    renderer = ManimRenderer(provider, max_repair_attempts=1, runner=runner)
    artifacts = LocalArtifactStore(tmp_path)
    plan = make_scene_plan()

    generated = await renderer.render_scene(
        video_id="vid_test",
        scene_plan=plan,
        scene=plan.scenes[0],
        artifacts=artifacts,
    )

    assert len(provider.prompts) == 2
    assert "SyntaxError: bad code" in provider.prompts[1]
    assert {artifact.path for artifact in generated} == {
        "visual/scene_1_big_idea/final.py",
        "visual/scene_1_big_idea/final_code.json",
        "visual/scene_1_big_idea/scene.mp4",
    }
    final_code = artifacts.resolve("vid_test", "visual/scene_1_big_idea/final_code.json").read_text()
    assert '"status": "rendered"' in final_code
    assert '"final_code":' in final_code
    assert "fixed" in artifacts.resolve("vid_test", "visual/scene_1_big_idea/final.py").read_text()


@pytest.mark.asyncio
async def test_renderer_reports_missing_manim_executable(tmp_path: Path):
    def missing_runner(command, cwd):
        raise FileNotFoundError("manim")

    class Provider:
        async def generate(self, prompt):
            return _generated_code()

    renderer = ManimRenderer(
        provider=Provider(),
        runner=missing_runner,
    )

    with pytest.raises(RuntimeError, match="Manim is not installed"):
        await renderer.render_scene(
            video_id="vid_test",
            scene_plan=make_scene_plan(),
            scene=make_scene_plan().scenes[0],
            artifacts=LocalArtifactStore(tmp_path),
        )


def _generated_code():
    return "from manim import *\nclass Scene1BigIdeaScene(Scene):\n    pass\n"
