from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from chemistry_video.chemistry import (
    ChemistryVerifier,
    FakeGPTReasoner,
    GPTReasoner,
    strict_json_schema,
)
from chemistry_video.domain import ReasoningOutput, VerificationStatus


class StubStructuredClient:
    def __init__(self, payload):
        self.payload = payload
        self.input = []
        self.options = {}

    async def complete_json(self, *, input, schema, model, reasoning_effort, verbosity):
        self.input = input
        self.options = {
            "schema": schema,
            "model": model,
            "reasoning_effort": reasoning_effort,
            "verbosity": verbosity,
        }
        assert "properties" in schema
        return self.payload


def valid_reasoning_payload():
    return {
        "question": "What is an atom?",
        "learning_objectives": ["Describe an atom"],
        "concepts": ["matter"],
        "equations": ["1 + 1 = 2"],
        "reactions": ["H2 + O2 -> H2O"],
        "molecules": [{"name": "oxygen", "smiles": "O"}],
        "reasoning_steps": ["Identify the parts"],
        "assumptions": [],
        "common_misconceptions": [],
        "key_takeaways": ["Atoms contain subatomic particles"],
        "references": ["OpenStax Chemistry"],
    }


@pytest.mark.asyncio
async def test_gpt_reasoner_validates_provider_output_strictly():
    client = StubStructuredClient(valid_reasoning_payload())
    reasoner = GPTReasoner(client)

    result = await reasoner.generate("What is an atom?")

    assert isinstance(result, ReasoningOutput)
    assert [message["role"] for message in client.input] == ["system", "developer", "user"]
    assert "What is an atom?" in client.input[-1]["content"]
    assert client.options["model"] == "gpt-5.5"
    assert client.options["reasoning_effort"] == "medium"
    assert client.options["verbosity"] == "low"
    assert client.options["schema"]["title"] == "ReasoningOutput"
    strict_schema = strict_json_schema(client.options["schema"])
    assert set(strict_schema["required"]) == set(strict_schema["properties"])

    client.payload["unexpected"] = "reject me"
    with pytest.raises(ValidationError):
        await reasoner.generate("What is an atom?")


@pytest.mark.asyncio
async def test_fake_reasoner_and_verifier_run_deterministic_checks():
    reasoning = await FakeGPTReasoner().generate("How does pH work?")
    report = await ChemistryVerifier().verify(reasoning, attempt=1)

    assert report.status == VerificationStatus.PASS
    assert {check.check for check in report.checks} >= {
        "pydantic_schema",
        "sympy",
        "chempy",
        "rdkit",
    }


@pytest.mark.asyncio
async def test_library_verifier_fails_deterministically():
    reasoning = await FakeGPTReasoner().generate("fail this chemistry")
    report = await ChemistryVerifier().verify(reasoning, attempt=3)

    assert report.status == VerificationStatus.FAIL
    assert report.required_corrections
    assert report.attempt == 3