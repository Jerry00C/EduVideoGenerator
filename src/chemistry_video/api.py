"""FastAPI application for the chemistry video service."""

from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from .artifacts import LocalArtifactStore
from .audio import OpenAITTSProvider, TTSProvider
from .composition import FFmpegSceneComposer, SceneComposer
from .manim_rendering import (
    ManimRenderer,
    ManimRendererProvider,
    OpenAIManimCodeProvider,
    OpenAIVisualCritic,
)
from .chemistry import (
    ChemistryVerifier,
    GPTReasoner,
    OpenAIResponsesClient,
    ReasonerProvider,
)
from .pedagogy import GPTPedagogyAdapter, PedagogyProvider
from .scene_planning import GPTScenePlanner, ScenePlannerProvider
from .domain import JobStatus, VideoRequest, VideoResponse, utc_now
from .pipeline import FakePipeline
from .repository import SQLiteJobRepository

load_dotenv()


class VideoService:
    def __init__(
        self,
        database_path: Path,
        artifact_root: Path,
        reasoner: Optional[ReasonerProvider] = None,
        verifier: Optional[ChemistryVerifier] = None,
        pedagogy: Optional[PedagogyProvider] = None,
        scene_planner: Optional[ScenePlannerProvider] = None,
        tts_provider: Optional[TTSProvider] = None,
        visual_renderer: Optional[ManimRendererProvider] = None,
        scene_composer: Optional[SceneComposer] = None,
    ):
        self.repository = SQLiteJobRepository(database_path)
        self.artifacts = LocalArtifactStore(artifact_root)
        if reasoner is None and verifier is None and os.getenv("OPENAI_API_KEY"):
            client = OpenAIResponsesClient()
            reasoner = GPTReasoner(client)
            verifier = ChemistryVerifier()
            pedagogy = GPTPedagogyAdapter(client)
            scene_planner = GPTScenePlanner(client)
            tts_provider = OpenAITTSProvider()
            visual_renderer = ManimRenderer(
                OpenAIManimCodeProvider(),
                critic=OpenAIVisualCritic(),
            )
            scene_composer = FFmpegSceneComposer()
        self.pipeline = FakePipeline(
            self.repository,
            self.artifacts,
            reasoner,
            verifier,
            pedagogy,
            scene_planner,
            tts_provider,
            visual_renderer,
            scene_composer,
        )
        self.tasks: set[asyncio.Task[None]] = set()

    def create_job(self, request: VideoRequest) -> VideoResponse:
        job = VideoResponse(
            id=f"vid_{uuid.uuid4().hex[:12]}",
            question=request.question,
            learner_level=request.learner_level,
            target_duration_seconds=request.duration_seconds,
            status=JobStatus.QUEUED,
            job_created_at=utc_now(),
        )
        self.repository.create(job)
        task = asyncio.create_task(self.pipeline.run(job))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return job

    async def shutdown(self) -> None:
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)


def create_app(
    database_path: Path = Path("data/jobs.sqlite3"),
    artifact_root: Path = Path("artifacts"),
    reasoner: Optional[ReasonerProvider] = None,
    verifier: Optional[ChemistryVerifier] = None,
    pedagogy: Optional[PedagogyProvider] = None,
    scene_planner: Optional[ScenePlannerProvider] = None,
    tts_provider: Optional[TTSProvider] = None,
    visual_renderer: Optional[ManimRendererProvider] = None,
    scene_composer: Optional[SceneComposer] = None,
) -> FastAPI:
    service = VideoService(
        database_path,
        artifact_root,
        reasoner,
        verifier,
        pedagogy,
        scene_planner,
        tts_provider,
        visual_renderer,
        scene_composer,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await service.shutdown()

    app = FastAPI(title="Chemistry Video Service", lifespan=lifespan)
    app.state.service = service

    @app.post("/videos", response_model=VideoResponse, status_code=202)
    async def create_video(request: VideoRequest) -> VideoResponse:
        return service.create_job(request)

    @app.get("/videos", response_model=List[VideoResponse])
    async def list_videos() -> List[VideoResponse]:
        return service.repository.list()

    @app.get("/videos/{video_id}", response_model=VideoResponse)
    async def get_video(video_id: str) -> VideoResponse:
        job = service.repository.get(video_id)
        if job is None:
            raise HTTPException(status_code=404, detail="video not found")
        return job

    @app.get("/videos/{video_id}/artifact")
    async def get_artifact(video_id: str) -> FileResponse:
        job = service.repository.get(video_id)
        if job is None:
            raise HTTPException(status_code=404, detail="video not found")
        if job.status != JobStatus.COMPLETED or not job.artifact_id:
            raise HTTPException(status_code=404, detail="artifact not available")
        path = service.artifacts.resolve(video_id, "final.mp4")
        if not path.is_file():
            raise HTTPException(status_code=404, detail="artifact not available")
        return FileResponse(path, media_type="video/mp4", filename="final.mp4")

    return app


app = create_app()
