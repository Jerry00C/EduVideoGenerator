from pathlib import Path

import pytest

from chemistry_video.artifacts import LocalArtifactStore
from chemistry_video.audio import (
    TTS_TEACHER_INSTRUCTIONS,
    FakeTTSProvider,
    OpenAITTSProvider,
    generate_segment_audio,
)
from chemistry_video.domain import (
    AudioPlan,
    PlannedScene,
    SceneNarrationSegment,
    ScenePlan,
    VisualBeat,
)


def make_scene_plan(segment_ids=("narration-1", "narration-2")):
    segments = [
        SceneNarrationSegment(id=segment_id, text=f"Text for {segment_id}")
        for segment_id in segment_ids
    ]
    return ScenePlan(
        title="Test lesson",
        target_duration_seconds=240,
        scenes=[
            PlannedScene(
                id="scene-1",
                purpose="Explain the concept",
                estimated_duration_seconds=10,
                narration_segments=segments,
                visual_beats=[
                    VisualBeat(
                        id="visual-1",
                        trigger_narration_id=segment_ids[0],
                        trigger_phrase="Text",
                        action="Show the concept",
                        visual_type="text",
                    )
                ],
            )
        ],
        audio_plan=AudioPlan(
            voice_style="friendly tutor",
            speaking_rate="moderate",
            segment_ids=list(segment_ids),
        ),
        estimated_total_duration_seconds=10,
    )


@pytest.mark.asyncio
async def test_fake_tts_is_deterministic_and_generates_one_artifact_per_segment(tmp_path: Path):
    provider = FakeTTSProvider()
    store = LocalArtifactStore(tmp_path)
    plan = make_scene_plan()

    first = await generate_segment_audio(
        video_id="vid_test",
        scene_plan=plan,
        artifacts=store,
        provider=provider,
    )
    second = await provider.synthesize(
        text="Text for narration-1",
        voice_style="friendly tutor",
        speaking_rate="moderate",
    )

    assert [artifact.path for artifact in first] == [
        "audio/narration-1.mp3",
        "audio/narration-2.mp3",
    ]
    assert first[0].media_type == "audio/mpeg"
    assert store.resolve("vid_test", first[0].path).read_bytes() == second
    assert [request["text"] for request in provider.requests[:2]] == [
        "Text for narration-1",
        "Text for narration-2",
    ]


@pytest.mark.asyncio
async def test_segment_audio_rejects_missing_narration_reference(tmp_path: Path):
    plan = make_scene_plan(("narration-1",))
    plan.audio_plan.segment_ids.append("missing")

    with pytest.raises(ValueError, match="missing narration segments"):
        await generate_segment_audio(
            video_id="vid_test",
            scene_plan=plan,
            artifacts=LocalArtifactStore(tmp_path),
            provider=FakeTTSProvider(),
        )


@pytest.mark.asyncio
async def test_openai_tts_sends_teacher_instructions():
    class FakeSpeech:
        def __init__(self):
            self.arguments = None

        async def create(self, **kwargs):
            self.arguments = kwargs
            return type("Response", (), {"content": b"audio"})()

    speech = FakeSpeech()
    provider = OpenAITTSProvider.__new__(OpenAITTSProvider)
    provider.model = "test-model"
    provider.voice = "test-voice"
    provider.client = type(
        "Client",
        (),
        {"audio": type("Audio", (), {"speech": speech})()},
    )()

    result = await provider.synthesize(
        text="An atom is one unit of an element.",
        voice_style="friendly tutor",
        speaking_rate="moderate",
    )

    assert result == b"audio"
    assert speech.arguments["input"] == "An atom is one unit of an element."
    assert TTS_TEACHER_INSTRUCTIONS in speech.arguments["instructions"]
    assert "Requested voice style: friendly tutor." in speech.arguments["instructions"]
    assert "Requested speaking rate: moderate." in speech.arguments["instructions"]
