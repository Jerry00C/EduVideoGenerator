import asyncio

from chemistry_video.chemistry import FakeGPTReasoner
from chemistry_video.pedagogy import FakePedagogyAdapter
from chemistry_video.scene_planning import FakeScenePlanner


async def verified_reasoning():
    return await FakeGPTReasoner().generate("How does pH work?")


def test_pedagogy_adapter_preserves_bounded_verified_content():
    reasoning = asyncio.run(verified_reasoning())
    plan = asyncio.run(FakePedagogyAdapter().adapt(reasoning))

    assert plan.learner_level == "high_school"
    assert plan.learning_objectives == reasoning.learning_objectives[:3]
    assert plan.key_takeaways == reasoning.key_takeaways[:3]
    assert len(plan.misconceptions) <= 2


def test_scene_planner_creates_referenced_narration_and_visual_scenes():
    reasoning = asyncio.run(verified_reasoning())
    pedagogy = asyncio.run(FakePedagogyAdapter().adapt(reasoning))
    scene_plan = asyncio.run(FakeScenePlanner().plan(reasoning, pedagogy))

    assert len(scene_plan.scenes) == 2
    assert len(scene_plan.audio_plan.segment_ids) == 2
    assert all(scene.visual_beats for scene in scene_plan.scenes)
    assert scene_plan.estimated_total_duration_seconds == 240