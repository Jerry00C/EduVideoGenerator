"""A deterministic in-process pipeline used until external providers are added."""

from __future__ import annotations

import asyncio
from typing import List, Optional, Union

from .artifacts import LocalArtifactStore
from .audio import FakeTTSProvider, TTSProvider, generate_segment_audio
from .chemistry import ChemistryVerifier, FakeGPTReasoner, ReasonerProvider
from .pedagogy import FakePedagogyAdapter, PedagogyProvider
from .scene_planning import FakeScenePlanner, ScenePlannerProvider
from .domain import (
    ArtifactRef,
    JobStatus,
    PipelineStageName,
    ReasoningOutput,
    StageContext,
    StageError,
    StageResult,
    StageResultStatus,
    VideoResponse,
    utc_now,
)
from .repository import SQLiteJobRepository


class FakePipeline:
    stages = [
        PipelineStageName.CHEMISTRY_REASONING,
        PipelineStageName.CHEMISTRY_VERIFICATION,
        PipelineStageName.PEDAGOGY_ADAPTATION,
        PipelineStageName.SCRIPT_SCENE_PLANNING,
        PipelineStageName.AUDIO_GENERATION,
        PipelineStageName.VISUAL_GENERATION,
        PipelineStageName.SCENE_COMPOSITION,
        PipelineStageName.QUALITY_CHECKING,
        PipelineStageName.UPLOADING,
        PipelineStageName.COMPLETED,
    ]

    def __init__(
        self,
        repository: SQLiteJobRepository,
        artifacts: LocalArtifactStore,
        reasoner: Optional[ReasonerProvider] = None,
        verifier: Optional[ChemistryVerifier] = None,
        pedagogy: Optional[PedagogyProvider] = None,
        scene_planner: Optional[ScenePlannerProvider] = None,
        tts_provider: Optional[TTSProvider] = None,
        max_correction_attempts: int = 2,
    ):
        self.repository = repository
        self.artifacts = artifacts
        self.reasoner = reasoner or FakeGPTReasoner()
        self.verifier = verifier or ChemistryVerifier()
        self.pedagogy = pedagogy or FakePedagogyAdapter()
        self.scene_planner = scene_planner or FakeScenePlanner()
        self.tts_provider = tts_provider or FakeTTSProvider()
        self.max_correction_attempts = max_correction_attempts

    async def run(self, job: VideoResponse) -> None:
        job.transition(JobStatus.PROCESSING)
        self.repository.update(job)
        files: List[ArtifactRef] = []

        chemistry_files = await self.run_chemistry(job)
        if chemistry_files is None:
            return
        files.extend(chemistry_files)

        lesson_files = await self.run_lesson(job)
        if lesson_files is None:
            return
        files.extend(lesson_files)

        for stage in self.stages[4:]:
            job.current_stage = stage
            if stage == PipelineStageName.UPLOADING:
                job.transition(JobStatus.UPLOADING)
            try:
                result = await self.execute_stage(job, stage)
            except Exception as exc:
                self.fail(job, stage, exc)
                return
            if result.status == StageResultStatus.FAILED:
                self.fail(job, stage, result.errors[0])
                return
            files.extend(result.artifacts)
            self.repository.update(job)

        final_artifact = next(file for file in files if file.path == "final.mp4")
        manifest = self.artifacts.manifest(job.id, files, final_artifact.artifact_id)
        job.artifact_id = manifest.artifact_id
        job.video_posted_at = utc_now()
        job.transition(JobStatus.COMPLETED)
        self.repository.update(job)

    async def run_chemistry(self, job: VideoResponse) -> Optional[List[ArtifactRef]]:
        corrections: List[str] = []
        for attempt in range(1, self.max_correction_attempts + 2):
            job.attempt_count = attempt
            job.current_stage = PipelineStageName.CHEMISTRY_REASONING
            try:
                reasoning = await self.reasoner.generate(job.question, corrections)
                reasoning_artifact = self.artifacts.write(
                    job.id,
                    "reasoning.json",
                    reasoning.model_dump_json(indent=2).encode("utf-8"),
                    "application/json",
                )
                job.current_stage = PipelineStageName.CHEMISTRY_VERIFICATION
                verification = await self.verifier.verify(reasoning, attempt)
                verification_artifact = self.artifacts.write(
                    job.id,
                    "verification.json",
                    verification.model_dump_json(indent=2).encode("utf-8"),
                    "application/json",
                )
                self.repository.update(job)
            except Exception as exc:
                self.fail(job, PipelineStageName.CHEMISTRY_REASONING, exc)
                return None

            if verification.status.value == "pass":
                return [reasoning_artifact, verification_artifact]

            corrections = verification.required_corrections
            if attempt > self.max_correction_attempts:
                self.fail(
                    job,
                    PipelineStageName.CHEMISTRY_VERIFICATION,
                    StageError(
                        code="verification_failed",
                        message="Chemistry verification failed after correction attempts",
                        details={"corrections": corrections, "attempts": attempt},
                    ),
                )
                return None
        return None

    async def run_lesson(self, job: VideoResponse) -> Optional[List[ArtifactRef]]:
        try:
            reasoning = self._read_reasoning(job)
            job.current_stage = PipelineStageName.PEDAGOGY_ADAPTATION
            pedagogy = await self.pedagogy.adapt(
                reasoning,
                learner_level=job.learner_level,
                target_duration_seconds=job.target_duration_seconds,
            )
            pedagogy_artifact = self.artifacts.write(
                job.id,
                "pedagogy.json",
                pedagogy.model_dump_json(indent=2).encode("utf-8"),
                "application/json",
            )
            job.current_stage = PipelineStageName.SCRIPT_SCENE_PLANNING
            scene_plan = await self.scene_planner.plan(
                reasoning,
                pedagogy,
                target_duration_seconds=job.target_duration_seconds,
            )
            scene_artifact = self.artifacts.write(
                job.id,
                "scene_plan.json",
                scene_plan.model_dump_json(indent=2).encode("utf-8"),
                "application/json",
            )
            self.repository.update(job)
            return [pedagogy_artifact, scene_artifact]
        except Exception as exc:
            self.fail(job, job.current_stage or PipelineStageName.PEDAGOGY_ADAPTATION, exc)
            return None

    def _read_reasoning(self, job: VideoResponse):
        path = self.artifacts.resolve(job.id, "reasoning.json")
        return ReasoningOutput.model_validate_json(path.read_text(encoding="utf-8"))

    async def execute_stage(self, job: VideoResponse, stage: PipelineStageName) -> StageResult:
        await asyncio.sleep(0)
        if "fail" in job.question.lower() and stage == PipelineStageName.CHEMISTRY_VERIFICATION:
            return StageResult(
                stage=stage,
                status=StageResultStatus.FAILED,
                errors=[StageError(code="fake_failure", message="Fake verification failure")],
                started_at=utc_now(),
                completed_at=utc_now(),
            )

        if stage == PipelineStageName.AUDIO_GENERATION:
            scene_plan = self._read_scene_plan(job)
            audio_artifacts = await generate_segment_audio(
                video_id=job.id,
                scene_plan=scene_plan,
                artifacts=self.artifacts,
                provider=self.tts_provider,
            )
            relative_path = f"stages/{stage.value}.json"
            stage_artifact = self.artifacts.write(
                job.id,
                relative_path,
                (f'{{"stage":"{stage.value}","segment_count":{len(audio_artifacts)}}}').encode("utf-8"),
                "application/json",
            )
            return StageResult(
                stage=stage,
                status=StageResultStatus.SUCCEEDED,
                artifacts=[*audio_artifacts, stage_artifact],
                started_at=utc_now(),
                completed_at=utc_now(),
            )

        relative_path = f"stages/{stage.value}.json"
        content = (f'{{"stage":"{stage.value}","video_id":"{job.id}"}}').encode("utf-8")
        artifact = self.artifacts.write(job.id, relative_path, content, "application/json")
        artifacts = [artifact]
        if stage == PipelineStageName.COMPLETED:
            artifacts.append(self.artifacts.write(job.id, "final.mp4", b"fake video artifact", "video/mp4"))
        return StageResult(
            stage=stage,
            status=StageResultStatus.SUCCEEDED,
            artifacts=artifacts,
            started_at=utc_now(),
            completed_at=utc_now(),
        )

    def _read_scene_plan(self, job: VideoResponse):
        from .domain import ScenePlan

        path = self.artifacts.resolve(job.id, "scene_plan.json")
        return ScenePlan.model_validate_json(path.read_text(encoding="utf-8"))

    def fail(
        self,
        job: VideoResponse,
        stage: PipelineStageName,
        error: Union[Exception, StageError],
    ) -> None:
        job.current_stage = stage
        job.error = error if isinstance(error, StageError) else StageError(code="pipeline_error", message=str(error))
        job.transition(JobStatus.FAILED)
        self.repository.update(job)
