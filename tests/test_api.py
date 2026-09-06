import asyncio
import json
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

from chemistry_video.api import create_app
from chemistry_video.chemistry import ChemistryVerifier, FakeGPTReasoner


@pytest_asyncio.fixture
async def client(tmp_path: Path):
    app = create_app(
        tmp_path / "jobs.sqlite3",
        tmp_path / "artifacts",
        reasoner=FakeGPTReasoner(),
        verifier=ChemistryVerifier(),
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.service.shutdown()


async def wait_for_status(client: httpx.AsyncClient, video_id: str, expected: str):
    for _ in range(100):
        response = await client.get(f"/videos/{video_id}")
        if response.json()["status"] == expected:
            return response.json()
        await asyncio.sleep(0.001)
    pytest.fail(f"job did not reach {expected}")


@pytest.mark.asyncio
async def test_create_video_runs_fake_pipeline_and_retrieves_artifact(client, tmp_path):
    response = await client.post("/videos", json={"question": "How does pH work?"})

    assert response.status_code == 202
    video_id = response.json()["id"]
    assert response.json()["status"] == "queued"

    job = await wait_for_status(client, video_id, "completed")
    assert job["artifact_id"] == f"{video_id}:manifest"
    assert job["current_stage"] == "completed"
    stage_files = list((tmp_path / "artifacts" / video_id / "stages").glob("*.json"))
    assert len(stage_files) == 7
    assert (tmp_path / "artifacts" / video_id / "reasoning.json").is_file()
    assert (tmp_path / "artifacts" / video_id / "verification.json").is_file()
    assert (tmp_path / "artifacts" / video_id / "pedagogy.json").is_file()
    assert (tmp_path / "artifacts" / video_id / "scene_plan.json").is_file()
    scene_plan = json.loads((tmp_path / "artifacts" / video_id / "scene_plan.json").read_text())
    audio_files = list((tmp_path / "artifacts" / video_id / "audio").glob("*.mp3"))
    segment_count = sum(len(scene["narration_segments"]) for scene in scene_plan["scenes"])
    assert len(audio_files) == segment_count
    visual_code_files = list((tmp_path / "artifacts" / video_id / "visual").glob("*/final_code.json"))
    visual_video_files = list((tmp_path / "artifacts" / video_id / "visual").glob("*/scene.mp4"))
    draft_video_files = list((tmp_path / "artifacts" / video_id / "draft_visual").glob("*/scene.mp4"))
    composed_video_files = list((tmp_path / "artifacts" / video_id / "scene_composition").glob("*/draft_scene.mp4"))
    composed_audio_files = list((tmp_path / "artifacts" / video_id / "scene_composition").glob("*/audio/*.mp3"))
    assert len(visual_code_files) == len(scene_plan["scenes"])
    assert len(visual_video_files) == len(scene_plan["scenes"])
    assert len(draft_video_files) == len(scene_plan["scenes"])
    assert len(composed_video_files) == len(scene_plan["scenes"])
    assert len(composed_audio_files) == segment_count
    composition = json.loads((tmp_path / "artifacts" / video_id / "scene_composition" / "composition.json").read_text())
    assert composition["status"] == "succeeded"
    assert all(scene["status"] == "composed" for scene in composition["scenes"])
    manifest = json.loads((tmp_path / "artifacts" / video_id / "artifact_manifest.json").read_text())
    manifest_paths = {file["path"] for file in manifest["files"]}
    assert all(path.relative_to(tmp_path / "artifacts" / video_id).as_posix() in manifest_paths for path in draft_video_files)

    artifact = await client.get(f"/videos/{video_id}/artifact")
    assert artifact.status_code == 200
    assert artifact.headers["content-type"] == "video/mp4"
    assert artifact.content == b"fake video artifact"


@pytest.mark.asyncio
async def test_list_videos_and_persistence(client, tmp_path):
    created = await client.post("/videos", json={"question": "What is a mole?"})
    video_id = created.json()["id"]
    await wait_for_status(client, video_id, "completed")

    response = await client.get("/videos")
    assert response.status_code == 200
    assert [job["id"] for job in response.json()] == [video_id]

    second_app = create_app(
        tmp_path / "jobs.sqlite3",
        tmp_path / "other-artifacts",
        reasoner=FakeGPTReasoner(),
        verifier=ChemistryVerifier(),
    )
    transport = httpx.ASGITransport(app=second_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as second_client:
        persisted = await second_client.get(f"/videos/{video_id}")
    await second_app.state.service.shutdown()
    assert persisted.status_code == 200
    assert persisted.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_failed_job_has_error_and_no_artifact(client):
    created = await client.post("/videos", json={"question": "fail this pipeline"})
    video_id = created.json()["id"]

    job = await wait_for_status(client, video_id, "failed")
    assert job["error"]["code"] == "verification_failed"
    assert job["attempt_count"] == 3

    artifact = await client.get(f"/videos/{video_id}/artifact")
    assert artifact.status_code == 404


@pytest.mark.asyncio
async def test_failed_visual_stage_writes_stage_error_artifact(tmp_path):
    class FailingRenderer:
        async def render_scene(self, **kwargs):
            raise RuntimeError("ffmpeg could not open draft scene")

    app = create_app(
        tmp_path / "jobs.sqlite3",
        tmp_path / "artifacts",
        reasoner=FakeGPTReasoner(),
        verifier=ChemistryVerifier(),
        visual_renderer=FailingRenderer(),
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        created = await test_client.post("/videos", json={"question": "A question"})
        video_id = created.json()["id"]
        job = await wait_for_status(test_client, video_id, "failed")
    await app.state.service.shutdown()

    stage = json.loads((tmp_path / "artifacts" / video_id / "stages" / "draft_rendering.json").read_text())
    assert job["current_stage"] == "draft_rendering"
    assert stage["status"] == "failed"
    assert stage["error"] == "ffmpeg could not open draft scene"


@pytest.mark.asyncio
async def test_missing_video_returns_404(client):
    response = await client.get("/videos/vid_missing")
    artifact = await client.get("/videos/vid_missing/artifact")

    assert response.status_code == 404
    assert artifact.status_code == 404


@pytest.mark.asyncio
async def test_artifact_is_unavailable_while_job_is_processing(client):
    created = await client.post("/videos", json={"question": "A question"})
    video_id = created.json()["id"]

    response = await client.get(f"/videos/{video_id}/artifact")
    assert response.status_code == 404
    await wait_for_status(client, video_id, "completed")
