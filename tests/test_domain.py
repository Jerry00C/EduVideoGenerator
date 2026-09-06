from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from chemistry_video.domain import (
    ArtifactManifest,
    ArtifactRef,
    AudioTiming,
    AudioPlan,
    JobStatus,
    PipelineStageName,
    QualityReport,
    QualityStatus,
    ScenePlan,
    StageError,
    StageResult,
    StageResultStatus,
    VideoRequest,
    VideoResponse,
    PlannedScene,
    SceneNarrationSegment,
    VisualBeat,
    can_transition,
)


NOW = datetime.now(timezone.utc)


def artifact(artifact_id: str = "audio-1") -> ArtifactRef:
    return ArtifactRef(
        artifact_id=artifact_id,
        path=f"audio/{artifact_id}.wav",
        media_type="audio/wav",
    )


def test_video_request_applies_safe_defaults_and_duration_bounds():
    request = VideoRequest(question="How does the pH scale work?")

    assert request.learner_level == "high_school"
    assert request.duration_seconds == 240
    assert request.output_width == 1920
    assert request.output_height == 1080

    with pytest.raises(ValidationError):
        VideoRequest(question="short", duration_seconds=179)


def test_video_response_allows_only_valid_lifecycle_transitions():
    job = VideoResponse(
        id="vid_123",
        question="How does the pH scale work?",
        status=JobStatus.QUEUED,
        job_created_at=NOW,
    )

    job.transition(JobStatus.PROCESSING)
    job.current_stage = PipelineStageName.VISUAL_GENERATION
    job.transition(JobStatus.UPLOADING)
    job.transition(JobStatus.COMPLETED)
    assert job.status == JobStatus.COMPLETED
    assert job.current_stage == PipelineStageName.VISUAL_GENERATION

    with pytest.raises(ValueError, match="invalid job transition"):
        job.transition(JobStatus.PROCESSING)


def test_transition_matrix_rejects_terminal_and_skipped_states():
    assert can_transition(JobStatus.QUEUED, JobStatus.PROCESSING)
    assert can_transition(JobStatus.PROCESSING, JobStatus.UPLOADING)
    assert can_transition(JobStatus.PROCESSING, JobStatus.FAILED)
    assert can_transition(JobStatus.UPLOADING, JobStatus.COMPLETED)
    assert not can_transition(JobStatus.QUEUED, JobStatus.COMPLETED)
    assert not can_transition(JobStatus.FAILED, JobStatus.QUEUED)
    assert not can_transition(JobStatus.COMPLETED, JobStatus.PROCESSING)


def test_pipeline_stage_names_include_uploading_and_completed():
    assert PipelineStageName.UPLOADING.value == "uploading"
    assert PipelineStageName.COMPLETED.value == "completed"


def test_failed_stage_requires_structured_error():
    with pytest.raises(ValidationError, match="failed stage must contain"):
        StageResult(
            stage="visual_generation",
            status=StageResultStatus.FAILED,
            started_at=NOW,
            completed_at=NOW,
        )

    result = StageResult(
        stage="visual_generation",
        status=StageResultStatus.FAILED,
        errors=[StageError(code="renderer_timeout", message="Renderer timed out", retryable=True)],
        started_at=NOW,
        completed_at=NOW,
    )
    assert result.errors[0].retryable is True


def test_audio_timing_must_match_actual_duration():
    timing = AudioTiming(
        segment_id="narration-1",
        audio_artifact_id="audio-1",
        duration_seconds=4.0,
        start_seconds=2.0,
        end_seconds=6.0,
    )
    assert timing.end_seconds - timing.start_seconds == timing.duration_seconds

    with pytest.raises(ValidationError, match="match the segment duration"):
        AudioTiming(
            segment_id="narration-1",
            audio_artifact_id="audio-1",
            duration_seconds=4.0,
            start_seconds=2.0,
            end_seconds=7.0,
        )


def test_scene_plan_requires_narration_scene_references():
    plan = ScenePlan(
        scenes=[
            PlannedScene(
                id="scene-1",
                purpose="Introduce atoms",
                estimated_duration_seconds=10,
                narration_segments=[
                    SceneNarrationSegment(id="narration-1", text="Atoms have a nucleus.")
                ],
                visual_beats=[
                    VisualBeat(
                        id="visual-1",
                        trigger_narration_id="narration-1",
                        trigger_phrase="nucleus",
                        action="Highlight the nucleus",
                        visual_type="atom_diagram",
                    )
                ],
            )
        ],
        audio_plan=AudioPlan(
            voice_style="calm",
            speaking_rate="moderate",
            segment_ids=["narration-1"],
        ),
        title="Atoms",
        target_duration_seconds=10,
        estimated_total_duration_seconds=10,
    )
    assert plan.scenes[0].narration_segments[0].id == "narration-1"

    with pytest.raises(ValidationError, match="reference a scene narration segment"):
        ScenePlan(
            scenes=[
                PlannedScene(
                    id="scene-1",
                    purpose="A scene",
                    estimated_duration_seconds=10,
                    narration_segments=[
                        SceneNarrationSegment(id="narration-1", text="A sentence.")
                    ],
                    visual_beats=[
                        VisualBeat(
                            id="visual-1",
                            trigger_narration_id="missing-narration",
                            trigger_phrase="missing",
                            action="Show nothing",
                            visual_type="text",
                        )
                    ],
                )
            ],
            audio_plan=AudioPlan(
                voice_style="calm",
                speaking_rate="moderate",
                segment_ids=["narration-1"],
            ),
            title="A scene",
            target_duration_seconds=10,
            estimated_total_duration_seconds=10,
        )


def test_quality_pass_requires_final_video_artifact():
    with pytest.raises(ValidationError, match="final video artifact"):
        QualityReport(
            status=QualityStatus.PASS,
            checks=[{"name": "audio", "status": "pass"}],
            duration_seconds=240,
        )

    report = QualityReport(
        status=QualityStatus.PASS,
        checks=[{"name": "audio", "status": "pass"}],
        duration_seconds=240,
        final_video_artifact_id="video-final",
    )
    assert report.status == QualityStatus.PASS


def test_published_manifest_requires_final_video_and_ordered_timestamps():
    manifest = ArtifactManifest(
        artifact_id="manifest-1",
        video_id="vid_123",
        files=[artifact("video-final")],
        created_at=NOW,
        published_at=NOW + timedelta(seconds=1),
        final_video_artifact_id="video-final",
    )
    assert manifest.published_at is not None

    with pytest.raises(ValidationError, match="published manifest"):
        ArtifactManifest(
            artifact_id="manifest-2",
            video_id="vid_123",
            files=[artifact()],
            created_at=NOW,
            published_at=NOW + timedelta(seconds=1),
        )
