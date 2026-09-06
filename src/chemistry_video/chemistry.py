"""Chemistry reasoning and verification boundaries."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Protocol, Sequence

from chempy import balance_stoichiometry
from pint import UnitRegistry
from rdkit import Chem
from sympy import simplify, sympify

from .domain import (
    MoleculeReference,
    ReasoningOutput,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)


SAFETY_SYSTEM_PROMPT = (
    "You create educational chemistry content for teenagers. Do not provide dangerous "
    "experiments, hazardous procedural guidance, sexual content, violent content, or "
    "instructions that could cause harm. Keep explanations age-appropriate and safe."
)

STABLE_CHEMISTRY_REASONER_PROMPT = """You are the Chemistry Reasoner for an educational video system.
Produce a scientifically accurate explanation for learners from entry level through high-school chemistry.
Requirements:
- Answer the exact question.
- Include the concepts and reasoning needed to support the answer.
- Define symbols used in equations.
- Preserve units and significant figures in calculations.
- State important assumptions and misconceptions.
- Use available calculation or chemistry tools when they improve correctness.
- Do not invent facts, reaction products, constants, or references.
- If the question is ambiguous, unsupported, or missing essential information, report that clearly.
- For every molecule, set `name` to a readable label and `smiles` to a valid SMILES string. Never put a prose description in `smiles`.
Do not create narration, scenes, animations, or video instructions. Produce only the chemistry content required by the output schema."""


def strict_json_schema(model_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Make a Pydantic schema compatible with OpenAI strict structured output."""
    schema = json.loads(json.dumps(model_schema))

    def normalize(node: Any) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "object" and "properties" in node:
            properties = node["properties"]
            node["required"] = list(properties.keys())
            node["additionalProperties"] = False
            for property_schema in properties.values():
                normalize(property_schema)
        if node.get("type") == "array":
            normalize(node.get("items"))
        for definition in node.get("$defs", {}).values():
            normalize(definition)

    normalize(schema)
    return schema

class StructuredCompletionClient(Protocol):
    async def complete_json(
        self,
        *,
        input: List[Dict[str, str]],
        schema: Dict[str, Any],
        model: str,
        reasoning_effort: str,
        verbosity: str,
    ) -> Any:
        """Return provider JSON for the requested schema."""
        ...


class ReasonerProvider(Protocol):
    async def generate(
        self, question: str, corrections: Sequence[str] = ()
    ) -> ReasoningOutput:
        """Generate strictly validated chemistry reasoning."""
        ...


class OpenAIResponsesClient:
    """Small async Responses API adapter; it performs no chemistry logic."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from openai import AsyncOpenAI

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def complete_json(
        self,
        *,
        input: List[Dict[str, str]],
        schema: Dict[str, Any],
        model: str,
        reasoning_effort: str,
        verbosity: str,
    ) -> Any:
        response = await self.client.responses.create(
            model=model,
            reasoning={"effort": reasoning_effort},
            input=input,
            text={
                "verbosity": verbosity,
                "format": {
                    "type": "json_schema",
                    "name": schema.get("title", "structured_output").lower(),
                    "strict": True,
                    "schema": strict_json_schema(schema),
                },
            },
        )
        return json.loads(response.output_text)


class GPTReasoner:
    """GPT adapter that accepts only Pydantic-validated structured output."""

    def __init__(
        self,
        client: StructuredCompletionClient,
        model: Optional[str] = None,
        system_prompt: str = SAFETY_SYSTEM_PROMPT,
        developer_prompt: str = STABLE_CHEMISTRY_REASONER_PROMPT,
    ):
        self.client = client
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.system_prompt = system_prompt
        self.developer_prompt = developer_prompt

    async def generate(
        self, question: str, corrections: Sequence[str] = ()
    ) -> ReasoningOutput:
        user_request = {"question": question}
        if corrections:
            user_request["verifier_corrections"] = list(corrections)
        raw = await self.client.complete_json(
            input=[
                {"role": "system", "content": self.system_prompt},
                {"role": "developer", "content": self.developer_prompt},
                {"role": "user", "content": json.dumps(user_request)},
            ],
            schema=ReasoningOutput.model_json_schema(),
            model=self.model,
            reasoning_effort="medium",
            verbosity="low",
        )
        return ReasoningOutput.model_validate(raw)


class FakeGPTReasoner:
    """Deterministic GPT-shaped provider for tests and local development."""

    def __init__(self):
        self.calls = 0

    async def generate(
        self, question: str, corrections: Sequence[str] = ()
    ) -> ReasoningOutput:
        self.calls += 1
        failing = "fail" in question.lower()
        return ReasoningOutput(
            question=question,
            learning_objectives=["Explain the chemistry concept clearly"],
            concepts=["atoms", "chemical change"],
            equations=["1 + 1 = 2"],
            reactions=["not a reaction"] if failing else ["H2 + O2 -> H2O"],
            molecules=(
                [MoleculeReference(name="invalid molecule", smiles="not-smiles")]
                if failing
                else [MoleculeReference(name="oxygen", smiles="O")]
            ),
            reasoning_steps=["Identify the quantities", "Apply the chemistry relationship"],
            assumptions=list(corrections),
            common_misconceptions=["A coefficient changes the identity of a molecule"],
            key_takeaways=["Chemical equations describe conserved atoms"],
            references=["OpenStax Chemistry"],
        )


class ChemistryVerifier:
    """Runs deterministic chemistry checks without calling an LLM."""

    def __init__(self):
        self.units = UnitRegistry()

    async def verify(self, reasoning: ReasoningOutput, attempt: int) -> VerificationReport:
        checks = self._pydantic_checks(reasoning)
        checks.extend(self._sympy_checks(reasoning.equations))
        checks.extend(self._pint_checks(reasoning.equations))
        checks.extend(self._chempy_checks(reasoning.reactions))
        checks.extend(self._rdkit_checks(reasoning.molecules))
        failures = [check.message for check in checks if check.status == VerificationStatus.FAIL]
        return VerificationReport(
            status=VerificationStatus.FAIL if failures else VerificationStatus.PASS,
            checks=checks,
            required_corrections=failures,
            attempt=attempt,
        )

    def _pydantic_checks(self, reasoning: ReasoningOutput) -> List[VerificationCheck]:
        return [
            VerificationCheck(
                target_id="reasoning",
                check="pydantic_schema",
                status=VerificationStatus.PASS,
                message="ReasoningOutput passed strict Pydantic validation",
            )
        ]

    def _sympy_checks(self, equations: Sequence[str]) -> List[VerificationCheck]:
        checks = []
        for index, equation in enumerate(equations):
            if "=" not in equation:
                continue
            left, right = equation.split("=", 1)
            try:
                valid = simplify(sympify(left) - sympify(right)) == 0
                checks.append(self._check("equation_" + str(index), "sympy", valid, equation))
            except Exception as exc:
                checks.append(self._check("equation_" + str(index), "sympy", False, str(exc)))
        return checks

    def _pint_checks(self, equations: Sequence[str]) -> List[VerificationCheck]:
        checks = []
        for index, equation in enumerate(equations):
            quantities = re.findall(r"(?:\d+(?:\.\d+)?)\s*([A-Za-z]+)", equation)
            if not quantities:
                continue
            try:
                for unit in quantities:
                    self.units.Unit(unit)
                checks.append(self._check("equation_" + str(index), "pint", True, equation))
            except Exception as exc:
                checks.append(self._check("equation_" + str(index), "pint", False, str(exc)))
        return checks

    def _chempy_checks(self, reactions: Sequence[str]) -> List[VerificationCheck]:
        checks = []
        for index, reaction in enumerate(reactions):
            try:
                left, right = reaction.split("->", 1)
                balance_stoichiometry(
                    {item.strip() for item in left.split("+")},
                    {item.strip() for item in right.split("+")},
                )
                checks.append(self._check("reaction_" + str(index), "chempy", True, reaction))
            except Exception as exc:
                checks.append(self._check("reaction_" + str(index), "chempy", False, str(exc)))
        return checks

    def _rdkit_checks(self, molecules: Sequence[MoleculeReference]) -> List[VerificationCheck]:
        checks = []
        for index, molecule in enumerate(molecules):
            valid = Chem.MolFromSmiles(molecule.smiles) is not None
            value = f"{molecule.name} ({molecule.smiles})"
            checks.append(self._check("molecule_" + str(index), "rdkit", valid, value))
        return checks

    @staticmethod
    def _check(target_id: str, name: str, valid: bool, value: str) -> VerificationCheck:
        return VerificationCheck(
            target_id=target_id,
            check=name,
            status=VerificationStatus.PASS if valid else VerificationStatus.FAIL,
            message="validated: " + value if valid else "invalid value: " + value,
        )
