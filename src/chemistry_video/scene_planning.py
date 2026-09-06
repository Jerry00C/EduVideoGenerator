"""GPT-backed structured visual and narration planning."""

from __future__ import annotations

import json
from typing import Optional, Protocol

from .chemistry import StructuredCompletionClient
from .domain import (
    AudioPlan,
    PedagogyPlan,
    PlannedScene,
    ReasoningOutput,
    SceneNarrationSegment,
    ScenePlan,
    VisualBeat,
)


SCENE_PLANNING_DEVELOPER_PROMPT = """You are the Script and Scene Planner for a short chemistry educational video.

Transform the supplied input into a production-ready scene plan for TTS, captions,
visual generation, and later audio/video composition. The JSON schema supplied by
the caller is authoritative. Use only fields supported by that schema; do not add
fields such as spoken_text, display_latex, timing, lifecycle, or narration_order
unless they exist in the schema.

SOURCE OF TRUTH
1. VERIFIED_CHEMISTRY is the only source of scientific facts. Do not infer,
   embellish, or import facts from general knowledge.
2. PEDAGOGY_PLAN controls teaching order, emphasis, misconceptions, and recap.
3. When the sources conflict, omit the unsupported claim and explain the problem
   in planning_warnings. If a coherent scientifically correct plan cannot be made,
   set status to \"planning_blocked\" and explain the blocking issue in
   planning_warnings.
4. Copy source IDs exactly from the supplied inputs. Every narration or visual that
   communicates a scientific claim must include the relevant source_ids.

NARRATION
5. Follow the pedagogy sequence and keep each scene focused on one teaching purpose.
6. Write for the supplied learner level and age range in clear, natural English.
7. Split narration into TTS-friendly segments of one main idea, normally 8-25 words.
   A short transition or recap may be shorter when necessary.
8. The `text` field is spoken narration and must contain no performance directions,
   markup, raw LaTeX, timestamps, or stage directions. Caption text is not a
   separate schema field, so keep `text` concise enough to caption faithfully.
9. Preserve every qualification needed for scientific accuracy. Do not turn an
   analogy into a literal model, and do not introduce unsupported examples,
   equations, molecules, quantities, or experiment instructions.
10. The sum of narration words should be close to the target speaking budget:
    target_duration_seconds * target_words_per_minute / 60. Prefer 90-110 percent
    of that budget, unless the verified content is too limited; report a shortfall
    in planning_warnings instead of padding with repetition.

VISUALS
11. Every narration segment must have at least one visual beat, and every visual
    beat must reference an existing narration segment in the same scene.
12. Use exactly one `visual_type` from available_visual_components. Prefer a
    structured chemistry component over generic text when one is available.
13. Make each visual beat implementable without code: state what appears, what is
    highlighted or changed, and what remains visible. Use `action` for this concise
    instruction, not for Manim or renderer code.
14. Use `trigger_phrase` only as an exact substring of its narration `text`.
    Use the segment's first meaningful phrase when no later cue is required.
15. Keep on-screen text short, accurate, and within the supplied caption limits.
    Never put raw LaTeX in on-screen text; use plain text unless a latex_equation
    component is selected and the schema supports the notation.
16. Avoid decorative movement and unsafe demonstrations. Keep a visual compatible
    with the next beat by describing transformations rather than impossible resets.

DURATION AND OUTPUT
17. Set target_duration_seconds from the input. Scene duration and total duration
    are planning estimates; actual generated TTS duration is authoritative later.
18. Include all narration segment IDs exactly once in audio_plan.segment_ids and in
    the order spoken. Use unique IDs for scenes, narration segments, and visual beats.
19. Use the supplied voice style and speaking rate in audio_plan when possible.
20. Return only JSON that validates against SCENE_PLAN_SCHEMA. Do not wrap it in
    Markdown or add commentary."""


class ScenePlannerProvider(Protocol):
    async def plan(
        self,
        reasoning: ReasoningOutput,
        pedagogy: PedagogyPlan,
        target_duration_seconds: int = 240,
    ) -> ScenePlan:
        ...


class GPTScenePlanner:
    def __init__(self, client: StructuredCompletionClient, model: Optional[str] = None):
        self.client = client
        self.model = model or "gpt-5.5"

    async def plan(self, reasoning: ReasoningOutput, pedagogy: PedagogyPlan, target_duration_seconds: int = 240) -> ScenePlan:
        payload = {
            "question": reasoning.question,
            "learner": {
                "level": pedagogy.learner_level,
                "approximate_age_range": "13-18",
            },
            "video": {
                "target_duration_seconds": target_duration_seconds,
                "target_words_per_minute": 135,
                "resolution": "1920x1080",
                "visual_style": "clean educational animation",
                "max_caption_characters_per_line": 42,
                "max_caption_lines": 2,
            },
            "tts_constraints": {
                "language": "en",
                "voice_style": "friendly and clear teenage science tutor",
                "audio_format": "mp3",
            },
            "verified_chemistry": reasoning.model_dump(mode="json"),
            "pedagogy_plan": {
                "learning_objectives": pedagogy.learning_objectives,
                "teaching_sequence": [pedagogy.explanation],
                "analogies": [],
                "misconceptions_to_correct": pedagogy.misconceptions,
                "recap_points": pedagogy.key_takeaways,
            },
            "available_visual_components": [
                "title",
                "text",
                "atom_diagram",
                "electron_dot_diagram",
                "molecule_diagram",
                "energy_graph",
                "latex_equation",
                "comparison_table",
            ],
        }
        raw = await self.client.complete_json(
            input=[
                {"role": "system", "content": "Return only safe, structured educational content."},
                {"role": "developer", "content": SCENE_PLANNING_DEVELOPER_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            schema=ScenePlan.model_json_schema(),
            model=self.model,
            reasoning_effort="medium",
            verbosity="low",
        )
        return ScenePlan.model_validate(raw)


class FakeScenePlanner:
    async def plan(self, reasoning: ReasoningOutput, pedagogy: PedagogyPlan, target_duration_seconds: int = 240) -> ScenePlan:
        scenes = [
            PlannedScene(
                id="scene_01",
                purpose="Introduce the central question",
                pedagogy_beat_ids=["beat_01"],
                estimated_duration_seconds=18,
                narration_segments=[
                    SceneNarrationSegment(id="narration_01", text=reasoning.question)
                ],
                visual_beats=[
                    VisualBeat(
                        id="visual_01",
                        trigger_narration_id="narration_01",
                        trigger_phrase=reasoning.question,
                        action="Show the chemistry question and highlight its central idea.",
                        visual_type="title",
                    )
                ],
            ),
            PlannedScene(
                id="scene_02",
                purpose="Explain the verified chemistry",
                pedagogy_beat_ids=["beat_02"],
                estimated_duration_seconds=35,
                narration_segments=[
                    SceneNarrationSegment(
                        id="narration_02",
                        text=pedagogy.explanation,
                        source_ids=pedagogy.source_ids,
                    )
                ],
                visual_beats=[
                    VisualBeat(
                        id="visual_02",
                        trigger_narration_id="narration_02",
                        trigger_phrase="central idea",
                        action="Reveal the verified explanation with supporting chemistry notation.",
                        visual_type="text",
                        source_ids=pedagogy.source_ids,
                    )
                ],
            ),
        ]
        return ScenePlan(
            title=reasoning.question,
            target_duration_seconds=target_duration_seconds,
            scenes=scenes,
            audio_plan=AudioPlan(
                voice_style="friendly, calm and curious",
                speaking_rate="moderate",
                segment_ids=["narration_01", "narration_02"],
            ),
            estimated_total_duration_seconds=target_duration_seconds,
        )
