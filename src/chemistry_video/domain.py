"""Provider-neutral domain models and pipeline interfaces."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    FAILED = "failed"
    COMPLETED = "completed"


class PipelineStageName(str, Enum):
    CHEMISTRY_REASONING = "chemistry_reasoning"
    CHEMISTRY_VERIFICATION = "chemistry_verification"
    PEDAGOGY_ADAPTATION = "pedagogy_adaptation"
    SCRIPT_SCENE_PLANNING = "script_scene_planning"
    AUDIO_GENERATION = "audio_generation"
    VISUAL_GENERATION = "visual_generation"
    SCENE_COMPOSITION = "scene_composition"
    QUALITY_CHECKING = "quality_checking"
    UPLOADING = "uploading"
    COMPLETED = "completed"


class VerificationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class StageResultStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class QualityStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


VALID_JOB_TRANSITIONS = {
    JobStatus.QUEUED: {JobStatus.PROCESSING},
    JobStatus.PROCESSING: {JobStatus.UPLOADING, JobStatus.FAILED},
    JobStatus.UPLOADING: {JobStatus.COMPLETED, JobStatus.FAILED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    """Return whether a job may move from current to target."""
    return target in VALID_JOB_TRANSITIONS[current]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VideoRequest(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    learner_level: str = Field(default="high_school", min_length=1, max_length=80)
    duration_seconds: int = Field(default=240, ge=180, le=300)
    output_width: int = Field(default=1920, ge=1)
    output_height: int = Field(default=1080, ge=1)


class VideoResponse(StrictModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    learner_level: str = Field(default="high_school", min_length=1)
    target_duration_seconds: int = Field(default=240, ge=180, le=300)
    status: JobStatus
    current_stage: Optional[PipelineStageName] = None
    attempt_count: int = Field(default=0, ge=0)
    error: Optional["StageError"] = None
    job_created_at: datetime
    video_posted_at: Optional[datetime] = None
    artifact_id: Optional[str] = None

    def transition(self, target: JobStatus) -> "VideoResponse":
        if not can_transition(self.status, target):
            raise ValueError(f"invalid job transition: {self.status.value} -> {target.value}")
        self.status = target
        return self


class StageError(StrictModel):
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)
    retryable: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class ArtifactRef(StrictModel):
    artifact_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    size_bytes: Optional[int] = Field(default=None, ge=0)
    checksum_sha256: Optional[str] = None


class StageResult(StrictModel):
    stage: PipelineStageName
    status: StageResultStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[ArtifactRef] = Field(default_factory=list)
    errors: List[StageError] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime

    @model_validator(mode="after")
    def validate_result(self) -> "StageResult":
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        if self.status == StageResultStatus.SUCCEEDED and self.errors:
            raise ValueError("a succeeded stage cannot contain errors")
        if self.status == StageResultStatus.FAILED and not self.errors:
            raise ValueError("a failed stage must contain at least one error")
        return self


class StageContext(StrictModel):
    video_id: str = Field(min_length=1)
    attempt: int = Field(default=1, ge=1)
    input_artifacts: List[ArtifactRef] = Field(default_factory=list)


class PipelineStage(Protocol):
    name: PipelineStageName

    async def execute(self, context: StageContext) -> StageResult:
        """Execute one stage without coupling it to an external provider."""
        ...


class MoleculeReference(StrictModel):
    name: str = Field(min_length=1)
    smiles: str = Field(min_length=1)


class ReasoningOutput(StrictModel):
    question: str = Field(min_length=1)
    learning_objectives: List[str] = Field(min_length=1)
    concepts: List[str] = Field(default_factory=list)
    equations: List[str] = Field(default_factory=list)
    reactions: List[str] = Field(default_factory=list)
    molecules: List[MoleculeReference] = Field(default_factory=list)
    reasoning_steps: List[str] = Field(min_length=1)
    assumptions: List[str] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(min_length=1)
    references: List[str] = Field(default_factory=list)


class VerificationCheck(StrictModel):
    target_id: str = Field(min_length=1)
    check: str = Field(min_length=1)
    status: VerificationStatus
    message: str = ""


class VerificationReport(StrictModel):
    status: VerificationStatus
    checks: List[VerificationCheck] = Field(default_factory=list)
    required_corrections: List[str] = Field(default_factory=list)
    attempt: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_report(self) -> "VerificationReport":
        if self.status == VerificationStatus.FAIL and not self.required_corrections:
            raise ValueError("a failed verification requires corrections")
        return self


class PedagogyPlan(StrictModel):
    learner_level: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    learning_objectives: List[str] = Field(min_length=1)
    misconceptions: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(min_length=1)
    clarification_required: bool = False
    source_ids: List[str] = Field(default_factory=list)


class SceneNarrationSegment(StrictModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_ids: List[str] = Field(default_factory=list)


class VisualBeat(StrictModel):
    id: str = Field(min_length=1)
    trigger_narration_id: str = Field(min_length=1)
    trigger_phrase: str = Field(min_length=1)
    action: str = Field(min_length=1)
    visual_type: str = Field(min_length=1)
    on_screen_text: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)


class PlannedScene(StrictModel):
    id: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    pedagogy_beat_ids: List[str] = Field(default_factory=list)
    estimated_duration_seconds: float = Field(gt=0)
    narration_segments: List[SceneNarrationSegment] = Field(min_length=1)
    visual_beats: List[VisualBeat] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_visual_triggers(self) -> "PlannedScene":
        narration_ids = {segment.id for segment in self.narration_segments}
        if any(beat.trigger_narration_id not in narration_ids for beat in self.visual_beats):
            raise ValueError("each visual beat must reference a scene narration segment")
        return self


class AudioPlan(StrictModel):
    voice_style: str = Field(min_length=1)
    speaking_rate: str = Field(min_length=1)
    segment_ids: List[str] = Field(min_length=1)


class ScenePlan(StrictModel):
    status: str = Field(default="ready", min_length=1)
    title: str = Field(min_length=1)
    target_duration_seconds: int = Field(ge=1)
    scenes: List[PlannedScene] = Field(min_length=1)
    audio_plan: AudioPlan
    estimated_total_duration_seconds: float = Field(gt=0)
    planning_warnings: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_plan_references(self) -> "ScenePlan":
        narration_ids = {
            segment.id
            for scene in self.scenes
            for segment in scene.narration_segments
        }
        visual_ids = {
            beat.trigger_narration_id
            for scene in self.scenes
            for beat in scene.visual_beats
        }
        if not visual_ids.issubset(narration_ids):
            raise ValueError("visual beats must reference planned narration")
        if not set(self.audio_plan.segment_ids).issubset(narration_ids):
            raise ValueError("audio plan must reference planned narration")
        return self


class AudioTiming(StrictModel):
    segment_id: str = Field(min_length=1)
    audio_artifact_id: str = Field(min_length=1)
    duration_seconds: float = Field(gt=0)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_timing(self) -> "AudioTiming":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        if abs((self.end_seconds - self.start_seconds) - self.duration_seconds) > 0.05:
            raise ValueError("audio timing must match the segment duration within 50ms")
        return self


class VisualSceneTiming(StrictModel):
    scene_id: str = Field(min_length=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    scene_artifact_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_timing(self) -> "VisualSceneTiming":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        return self


class QualityCheck(StrictModel):
    name: str = Field(min_length=1)
    status: QualityStatus
    message: str = ""


class QualityReport(StrictModel):
    status: QualityStatus
    checks: List[QualityCheck] = Field(min_length=1)
    duration_seconds: float = Field(gt=0)
    final_video_artifact_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_quality_gate(self) -> "QualityReport":
        if self.status == QualityStatus.PASS and not self.final_video_artifact_id:
            raise ValueError("a passing quality report requires the final video artifact")
        return self


class ArtifactManifest(StrictModel):
    artifact_id: str = Field(min_length=1)
    video_id: str = Field(min_length=1)
    files: List[ArtifactRef] = Field(min_length=1)
    created_at: datetime
    published_at: Optional[datetime] = None
    final_video_artifact_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_publication(self) -> "ArtifactManifest":
        if self.published_at and self.published_at < self.created_at:
            raise ValueError("published_at must not precede created_at")
        if self.published_at and not self.final_video_artifact_id:
            raise ValueError("a published manifest requires a final video artifact")
        return self
