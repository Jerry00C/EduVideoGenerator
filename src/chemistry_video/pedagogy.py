"""GPT-backed, bounded pedagogy adaptation."""

from __future__ import annotations

import json
from typing import Optional, Protocol

from .chemistry import StructuredCompletionClient
from .domain import PedagogyPlan, ReasoningOutput


PEDAGOGY_DEVELOPER_PROMPT = """You are the Pedagogy Adapter for a chemistry educational-video system.
Transform verified chemistry content into a clear lesson plan for teenagers at the specified learner level.
Use only claims in VERIFIED_CHEMISTRY. Do not introduce facts, equations, values, or assumptions.
Preserve the source_ids of every verified claim used. Start with intuition, explain terms before use,
teach one main idea at a time, use simple accurate language, address supplied misconceptions,
avoid dangerous experiments, fit the requested duration, and set clarification_required to true
if the verified information is insufficient. Produce only JSON matching PEDAGOGY_PLAN_SCHEMA."""


class PedagogyProvider(Protocol):
    async def adapt(self, reasoning: ReasoningOutput, learner_level: str = "high_school", target_duration_seconds: int = 240) -> PedagogyPlan:
        ...


class GPTPedagogyAdapter:
    def __init__(self, client: StructuredCompletionClient, model: Optional[str] = None):
        self.client = client
        self.model = model or "gpt-5.5"

    async def adapt(self, reasoning: ReasoningOutput, learner_level: str = "high_school", target_duration_seconds: int = 240) -> PedagogyPlan:
        verified = {
            "concepts": [{"id": f"concept_{i}", "claim": claim} for i, claim in enumerate(reasoning.concepts)],
            "reasoning_steps": [{"id": f"reasoning_{i}", "claim": claim} for i, claim in enumerate(reasoning.reasoning_steps)],
            "equations": reasoning.equations,
            "reactions": reasoning.reactions,
            "molecules": [molecule.model_dump(mode="json") for molecule in reasoning.molecules],
            "misconceptions": [{"id": f"misconception_{i}", "statement": claim} for i, claim in enumerate(reasoning.common_misconceptions)],
            "key_takeaways": reasoning.key_takeaways,
        }
        payload = {
            "question": reasoning.question,
            "learner": {"level": learner_level, "approximate_age_range": "13-18", "assumed_prerequisites": []},
            "video": {"target_duration_seconds": target_duration_seconds},
            "verified_chemistry": verified,
        }
        raw = await self.client.complete_json(
            input=[
                {"role": "system", "content": "Return only safe, structured educational content."},
                {"role": "developer", "content": PEDAGOGY_DEVELOPER_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            schema=PedagogyPlan.model_json_schema(),
            model=self.model,
            reasoning_effort="medium",
            verbosity="low",
        )
        return PedagogyPlan.model_validate(raw)


class FakePedagogyAdapter:
    async def adapt(self, reasoning: ReasoningOutput, learner_level: str = "high_school", target_duration_seconds: int = 240) -> PedagogyPlan:
        return PedagogyPlan(
            learner_level=learner_level,
            explanation=reasoning.concepts[0] if reasoning.concepts else "Start with the main idea.",
            learning_objectives=reasoning.learning_objectives[:3],
            misconceptions=reasoning.common_misconceptions[:2],
            key_takeaways=reasoning.key_takeaways[:3],
            source_ids=[f"concept_{i}" for i, _ in enumerate(reasoning.concepts)],
        )
