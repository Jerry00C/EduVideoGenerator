"""Text-to-speech providers and segmented audio artifact generation."""

from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Optional, Protocol

from .artifacts import LocalArtifactStore
from .domain import ArtifactRef, SceneNarrationSegment, ScenePlan


TTS_TEACHER_INSTRUCTIONS = """Speak as a friendly, calm, and knowledgeable high-school chemistry teacher addressing teenagers aged thirteen to eighteen.

Use a clear, natural, conversational voice. Sound curious and encouraging, but not childish, theatrical, overly excited, or robotic.

Speak at a moderate educational pace. Articulate chemical terms, numbers, units, element names, and letter names carefully. Use natural pauses after definitions, important comparisons, and questions.

Keep the tone and speaking pace consistent with adjacent narration segments. Begin speaking immediately without adding an introduction. Read only the supplied text. Do not add, remove, summarize, explain, or rephrase any words."""


class TTSProvider(Protocol):
    async def synthesize(
        self,
        *,
        text: str,
        voice_style: str,
        speaking_rate: str,
    ) -> bytes:
        """Return encoded audio bytes for one narration segment."""


class OpenAITTSProvider:
    """OpenAI Speech API adapter; it performs no segmentation or composition."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        voice: Optional[str] = None,
    ):
        from openai import AsyncOpenAI

        self.model = model or os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
        self.voice = voice or os.getenv("OPENAI_TTS_VOICE", "alloy")
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def synthesize(
        self,
        *,
        text: str,
        voice_style: str,
        speaking_rate: str,
    ) -> bytes:
        response = await self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
            instructions=(
                f"{TTS_TEACHER_INSTRUCTIONS}\n\n"
                f"Requested voice style: {voice_style}. Requested speaking rate: {speaking_rate}."
            ),
        )
        return response.content


class FakeTTSProvider:
    """Deterministic provider for tests and local development."""

    def __init__(self):
        self.requests: List[Dict[str, str]] = []

    async def synthesize(
        self,
        *,
        text: str,
        voice_style: str,
        speaking_rate: str,
    ) -> bytes:
        self.requests.append(
            {"text": text, "voice_style": voice_style, "speaking_rate": speaking_rate}
        )
        digest = hashlib.sha256(
            f"{text}\0{voice_style}\0{speaking_rate}".encode("utf-8")
        ).hexdigest()
        return f"FAKE-MP3:{digest}".encode("ascii")


def _narration_segments(scene_plan: ScenePlan) -> Dict[str, SceneNarrationSegment]:
    segments = {
        segment.id: segment
        for scene in scene_plan.scenes
        for segment in scene.narration_segments
    }
    if len(segments) != sum(len(scene.narration_segments) for scene in scene_plan.scenes):
        raise ValueError("narration segment IDs must be unique")
    return segments


async def generate_segment_audio(
    *,
    video_id: str,
    scene_plan: ScenePlan,
    artifacts: LocalArtifactStore,
    provider: TTSProvider,
) -> List[ArtifactRef]:
    """Synthesize and persist one audio artifact for each planned segment."""

    segments = _narration_segments(scene_plan)
    missing = [segment_id for segment_id in scene_plan.audio_plan.segment_ids if segment_id not in segments]
    if missing:
        raise ValueError(f"audio plan references missing narration segments: {missing}")

    generated: List[ArtifactRef] = []
    for segment_id in scene_plan.audio_plan.segment_ids:
        if "/" in segment_id or "\\" in segment_id or segment_id in {".", ".."}:
            raise ValueError(f"invalid narration segment ID for an artifact path: {segment_id}")
        segment = segments[segment_id]
        audio = await provider.synthesize(
            text=segment.text,
            voice_style=scene_plan.audio_plan.voice_style,
            speaking_rate=scene_plan.audio_plan.speaking_rate,
        )
        generated.append(
            artifacts.write(
                video_id,
                f"audio/{segment_id}.mp3",
                audio,
                "audio/mpeg",
            )
        )
    return generated