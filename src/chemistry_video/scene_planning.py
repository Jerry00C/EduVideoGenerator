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

Transform the supplied PEDAGOGY_PLAN and VERIFIED_CHEMISTRY into a production-ready sequence of narrated scenes.

Rules:
1. Follow the teaching order in PEDAGOGY_PLAN.
2. Use only claims supported by VERIFIED_CHEMISTRY.
3. Attach source_ids to every narration segment containing a scientific claim.
4. Write natural narration appropriate for the specified teenage learner level.
5. Keep narration concise and conversational.
6. Define what appears, changes, and disappears on screen.
7. Prefer explanatory visuals over decorative visuals.
8. Never represent an analogy as a literal scientific model.
9. Use LaTeX for displayed equations.
10. Use chemically valid notation from the verified input.
11. Keep each scene focused on one teaching purpose.
12. Split narration into short TTS-friendly segments.
13. Treat durations as estimates only. Actual TTS timing will become authoritative later.
14. Do not generate Manim code. Produce implementation-independent visual instructions.
15. Do not request unsafe experiment demonstrations.
16. Ensure the complete plan fits the target duration.
17. If the supplied material is insufficient or contradictory, return planning_blocked.
Produce only JSON matching SCENE_PLAN_SCHEMA."""


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
                "resolution": "1920x1080",
                "visual_style": "clean educational animation",
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
