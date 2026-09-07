"""LLM-assisted Manim code generation, repair, and scene rendering."""

from __future__ import annotations

import json
import base64
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence

from .artifacts import LocalArtifactStore
from .domain import ArtifactRef, PlannedScene, ScenePlan


MANIM_CODE_DEVELOPER_PROMPT = """You are an expert Manim Community Edition developer.
Generate one executable Python scene from the supplied structured chemistry scene.
The scene plan is authoritative: use only its narration, visual beats, labels,
visual types, and actions. Do not invent chemistry facts or use Code2Video's
storyboard format.

Requirements:
- Use Manim Community Edition 0.19-compatible Python.
- Return one complete Python file and no Markdown outside the code.
- Define exactly one Scene subclass named {class_name}.
- Implement every visual beat in order and keep narration text out of the animation
  unless the scene plan supplies it as on-screen text.
- Use clear 2D educational visuals. Keep labels readable and avoid overlap.
- Use simple, reliable Manim primitives and animations; do not use external assets
  or imports beyond Manim and Python standard-library modules.
- Do not create audio, captions, or video-composition logic. Rendering is handled by
  the caller.

SCENE PLAN:
{scene_json}
"""


class ManimCodeProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Generate or repair a complete Manim Python file."""


class ManimRendererProvider(Protocol):
    async def render_scene(
        self,
        *,
        video_id: str,
        scene_plan: ScenePlan,
        scene: PlannedScene,
        artifacts: LocalArtifactStore,
        feedback_enabled: bool = True,
        artifact_namespace: str = "visual",
    ) -> List[ArtifactRef]:
        """Render one planned scene and return its artifacts."""


class VisualCritic(Protocol):
    async def inspect(self, *, scene: PlannedScene, frame_paths: Sequence[Path]) -> str:
        """Return correction instructions, or an empty string when layout is acceptable."""


class OpenAIManimCodeProvider:
    """OpenAI Responses API adapter for Manim code generation and repair."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from openai import AsyncOpenAI

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def generate(self, prompt: str) -> str:
        response = await self.client.responses.create(
            model=self.model,
            reasoning={"effort": "medium"},
            input=[
                {"role": "system", "content": "Return only executable Python code."},
                {"role": "developer", "content": prompt},
            ],
            text={"verbosity": "low"},
        )
        return response.output_text


class OpenAIVisualCritic:
    """GPT vision adapter for rendered-frame layout feedback."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from openai import AsyncOpenAI

        self.model = model or os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def inspect(self, *, scene: PlannedScene, frame_paths: Sequence[Path]) -> str:
        content: List[Dict[str, Any]] = [
            {
                "type": "input_text",
                "text": (
                    "Inspect these sample frames from a chemistry educational Manim scene. "
                    "Check clipping, overlap, unreadable text, empty composition, and whether "
                    "the visuals match the supplied visual beats. Return either the exact text "
                    "OK or concise correction instructions. Do not suggest new chemistry facts.\n\n"
                    f"Scene plan:\n{json.dumps(scene.model_dump(mode='json'), indent=2)}"
                ),
            }
        ]
        for frame_path in frame_paths:
            encoded = base64.b64encode(frame_path.read_bytes()).decode("ascii")
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/png;base64,{encoded}",
                    "detail": "low",
                }
            )
        response = await self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": "You are a precise educational video layout critic."},
                {"role": "user", "content": content},
            ],
            # GPT-4o accepts only the default/medium text verbosity. The concise
            # output requirement is already expressed in the input prompt.
            text={"verbosity": "medium"},
        )
        result = response.output_text.strip()
        return "" if result.upper() == "OK" else result


class FakeManimCodeProvider:
    """Deterministic code provider for tests and local development."""

    async def generate(self, prompt: str) -> str:
        match = re.search(r"named ([A-Za-z_]\w*)", prompt)
        class_name = match.group(1) if match else "GeneratedScene"
        return (
            "from manim import *\n\n"
            f"class {class_name}(Scene):\n"
            "    def construct(self):\n"
            "        self.add(Text(\"Chemistry\"))\n"
            "        self.wait(0.1)\n"
        )


def scene_class_name(scene_id: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", scene_id)
    name = "".join(part[:1].upper() + part[1:] for part in parts) or "Scene"
    if name[0].isdigit():
        name = f"Scene{name}"
    return f"{name}Scene"


def extract_manim_code(response: str) -> str:
    """Extract Python from a model response while rejecting empty output."""

    fenced = re.search(r"```(?:python|py)?\s*(.*?)```", response, flags=re.IGNORECASE | re.DOTALL)
    code = fenced.group(1).strip() if fenced else response.strip()
    if not code:
        raise ValueError("code provider returned empty output")
    if "class " not in code or "Scene" not in code:
        raise ValueError("code provider output does not contain a Manim Scene")
    return code


def build_code_prompt(scene: PlannedScene, scene_plan: ScenePlan, class_name: str) -> str:
    scene_json = json.dumps(
        {
            "title": scene_plan.title,
            "target_duration_seconds": scene_plan.target_duration_seconds,
            "scene": scene.model_dump(mode="json"),
        },
        ensure_ascii=True,
        indent=2,
    )
    return MANIM_CODE_DEVELOPER_PROMPT.format(class_name=class_name, scene_json=scene_json)


def build_repair_prompt(
    *,
    original_prompt: str,
    code: str,
    error: str,
    attempt: int,
    max_attempts: int,
) -> str:
    return (
        f"{original_prompt}\n\n"
        f"REPAIR REQUEST ({attempt}/{max_attempts})\n"
        "The previous file failed during syntax checking or Manim rendering. "
        "Return the complete corrected Python file only. Preserve the scene plan "
        "and make the smallest reliable fix.\n"
        f"ERROR:\n{error}\n\nPREVIOUS CODE:\n```python\n{code}\n```"
    )


def build_layout_repair_prompt(*, scene: PlannedScene, code: str, correction: str) -> str:
    return (
        "You are repairing a Manim scene after visual layout review. Return only the "
        "complete corrected Python file. Preserve the scene's scientific meaning and "
        "visual beats; apply only the requested layout or readability fixes. Do not "
        "add chemistry facts.\n\n"
        f"SCENE:\n{json.dumps(scene.model_dump(mode='json'), indent=2)}\n\n"
        f"CORRECTION INSTRUCTIONS:\n{correction}\n\n"
        f"CURRENT CODE:\n```python\n{code}\n```"
    )


Runner = Callable[[Sequence[str], Path], Any]


def run_manim(command: Sequence[str], cwd: Path) -> Any:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=180)


def run_frame_capture(command: Sequence[str], cwd: Path) -> Any:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60)


def capture_sample_frames(video_path: Path, frames_dir: Path, runner: Runner = run_frame_capture) -> List[Path]:
    """Extract three representative PNG frames from a rendered draft."""

    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = frames_dir / "frame_%02d.png"
    input_path = os.path.relpath(video_path, frames_dir)
    result = runner(
        [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            "fps=1/5",
            "-frames:v",
            "3",
            pattern.name,
        ],
        frames_dir,
    )
    if getattr(result, "returncode", 1) != 0:
        raise RuntimeError(getattr(result, "stderr", "") or "ffmpeg failed to capture sample frames")
    return sorted(frames_dir.glob("frame_*.png"))


class ManimRenderer:
    def __init__(
        self,
        provider: ManimCodeProvider,
        executable: Optional[str] = None,
        max_repair_attempts: int = 3,
        runner: Runner = run_manim,
        critic: Optional[VisualCritic] = None,
        frame_runner: Runner = run_frame_capture,
        max_layout_feedback_attempts: int = 1,
    ):
        self.provider = provider
        self.executable = executable or str(Path(sys.executable).with_name("manim"))
        self.max_repair_attempts = max_repair_attempts
        self.runner = runner
        self.critic = critic
        self.frame_runner = frame_runner
        self.max_layout_feedback_attempts = max_layout_feedback_attempts

    async def render_scene(
        self,
        *,
        video_id: str,
        scene_plan: ScenePlan,
        scene: PlannedScene,
        artifacts: LocalArtifactStore,
        feedback_enabled: bool = True,
        artifact_namespace: str = "visual",
    ) -> List[ArtifactRef]:
        class_name = scene_class_name(scene.id)
        prompt = build_code_prompt(scene, scene_plan, class_name)
        code = ""
        errors: List[str] = []
        attempt_records: List[Dict[str, Any]] = []
        layout_feedback: List[str] = []
        use_existing_code = False
        output_dir = artifacts.job_directory(video_id) / artifact_namespace / scene.id
        output_dir.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.max_repair_attempts + 2):
            if attempt > 1 and not use_existing_code:
                prompt = build_repair_prompt(
                    original_prompt=build_code_prompt(scene, scene_plan, class_name),
                    code=code,
                    error=errors[-1],
                    attempt=attempt - 1,
                    max_attempts=self.max_repair_attempts,
                )
            try:
                if not use_existing_code:
                    code = extract_manim_code(await self.provider.generate(prompt))
                use_existing_code = False
            except Exception as exc:
                errors.append(str(exc))
                attempt_records.append({"attempt": attempt, "error": str(exc), "code": code})
                continue

            code_path = output_dir / f"attempt_{attempt}.py"
            code_path.write_text(code, encoding="utf-8")
            try:
                compile(code, f"{scene.id}.py", "exec")
            except SyntaxError as exc:
                error = f"SyntaxError: {exc}"
                errors.append(error)
                attempt_records.append({"attempt": attempt, "error": error, "code": code})
                continue

            command = [
                self.executable,
                "-ql",
                "--media_dir",
                str(output_dir / "media"),
                str(code_path.name),
                class_name,
                "-o",
                "scene.mp4",
            ]
            try:
                result = self.runner(command, output_dir)
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "Manim is not installed or is not available on PATH. "
                    "Install it in the active virtual environment with "
                    "`python -m pip install 'manim>=0.19,<0.20'`, or configure "
                    "a compatible Manim executable."
                ) from exc
            stdout = getattr(result, "stdout", "") or ""
            stderr = getattr(result, "stderr", "") or ""
            return_code = getattr(result, "returncode", 1)
            attempt_records.append(
                {"attempt": attempt, "returncode": return_code, "stdout": stdout, "stderr": stderr, "code": code}
            )
            if return_code == 0:
                rendered_path = next(output_dir.glob(f"**/attempt_{attempt}/**/scene.mp4"), None)
                if rendered_path is None:
                    rendered_path = next(output_dir.glob("**/scene.mp4"), None)
                if rendered_path is None:
                    errors.append("Manim exited successfully but scene.mp4 was not produced")
                else:
                    if feedback_enabled and self.critic is not None and len(layout_feedback) < self.max_layout_feedback_attempts:
                        frames_dir = output_dir / "frames" / f"attempt_{attempt}"
                        frame_paths = capture_sample_frames(rendered_path, frames_dir, self.frame_runner)
                        correction = await self.critic.inspect(scene=scene, frame_paths=frame_paths)
                        attempt_records[-1]["sample_frames"] = [str(path.relative_to(output_dir)) for path in frame_paths]
                        attempt_records[-1]["layout_feedback"] = correction
                        if correction:
                            layout_feedback.append(correction)
                            errors.append(f"Layout critic correction: {correction}")
                            code = extract_manim_code(
                                await self.provider.generate(
                                    build_layout_repair_prompt(
                                        scene=scene,
                                        code=code,
                                        correction=correction,
                                    )
                                )
                            )
                            use_existing_code = True
                            continue
                    final_code = artifacts.write(video_id, f"{artifact_namespace}/{scene.id}/final.py", code.encode("utf-8"), "text/x-python")
                    final_json = artifacts.write(
                        video_id,
                        f"{artifact_namespace}/{scene.id}/final_code.json",
                        json.dumps(
                            {
                                "scene_id": scene.id,
                                "class_name": class_name,
                                "status": "rendered",
                                "final_code": code,
                                "attempts": attempt_records,
                                "layout_feedback": layout_feedback,
                            },
                            indent=2,
                        ).encode("utf-8"),
                        "application/json",
                    )
                    video_ref = artifacts.write(video_id, f"{artifact_namespace}/{scene.id}/scene.mp4", rendered_path.read_bytes(), "video/mp4")
                    return [final_code, final_json, video_ref]
            errors.append(stderr or stdout or f"Manim failed with exit code {return_code}")

        final_json = artifacts.write(
            video_id,
            f"{artifact_namespace}/{scene.id}/final_code.json",
            json.dumps(
                {
                    "scene_id": scene.id,
                    "class_name": class_name,
                    "status": "failed",
                    "final_code": code,
                    "attempts": attempt_records,
                    "errors": errors,
                    "layout_feedback": layout_feedback,
                },
                indent=2,
            ).encode("utf-8"),
            "application/json",
        )
        raise RuntimeError(f"Manim rendering failed for {scene.id}: {errors[-1]}")


class FakeManimRenderer:
    """Deterministic renderer that persists the same artifact shape without Manim."""

    def __init__(self):
        self.provider = FakeManimCodeProvider()

    async def render_scene(
        self,
        *,
        video_id: str,
        scene_plan: ScenePlan,
        scene: PlannedScene,
        artifacts: LocalArtifactStore,
        feedback_enabled: bool = True,
        artifact_namespace: str = "visual",
    ) -> List[ArtifactRef]:
        code = extract_manim_code(await self.provider.generate(build_code_prompt(scene, scene_plan, scene_class_name(scene.id))))
        code_ref = artifacts.write(video_id, f"{artifact_namespace}/{scene.id}/final.py", code.encode("utf-8"), "text/x-python")
        json_ref = artifacts.write(
            video_id,
            f"{artifact_namespace}/{scene.id}/final_code.json",
            json.dumps(
                {"scene_id": scene.id, "status": "rendered", "final_code": code, "attempts": [{"attempt": 1, "code": code}]},
                indent=2,
            ).encode("utf-8"),
            "application/json",
        )
        video_ref = artifacts.write(video_id, f"{artifact_namespace}/{scene.id}/scene.mp4", b"fake scene video artifact", "video/mp4")
        return [code_ref, json_ref, video_ref]
