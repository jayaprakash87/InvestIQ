"""PR4 contract: model neutrality, SEC-only data, fail-closed citations and BYOK."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from investiq_core.ai_research import (
    AiResearchCoordinator,
    ModelFailure,
    OpenAIResponseModel,
    validate_answer,
)
from investiq_core.evidence import ValueUnit
from investiq_core.fundamentals import AnnualMetricFact
from investiq_core.market import IssuerId

CIK = "0000012345"
DOC_ID = "sec:0000012345-26-000007:120:1234567890abcdef"
FACT_ID = "sec-fact:0000012345-26-000007:revenue"


def answer(doc_id=DOC_ID):
    return {
        "overview": "The filing excerpts describe the stated products but leave material gaps.",
        "findings": [{
            "claim": "The issuer discusses a competitive market.",
            "evidence_ids": [doc_id],
        }],
        "bear_case": {
            "claim": "Customer concentration could undermine the thesis.",
            "evidence_ids": [doc_id],
        },
        "open_questions": ["How concentrated are revenues by customer?"],
    }


class FakeDocument:
    def __init__(self, *, empty=False):
        self.calls = []
        self.empty = empty

    async def inspect(self, issuer, *, topic):
        self.calls.append((issuer.value, topic))
        return {
            "document": {
                "form": "10-K", "accession": "0000012345-26-000007",
                "filed_on": "2026-03-04",
                "source_url": "https://www.sec.gov/Archives/edgar/data/12345/"
                              "000001234526000007/annual.htm",
            },
            "passages": [] if self.empty else [{
                "evidence_id": DOC_ID, "excerpt": "Issuer reports competition and risks.",
                "topic": "risks",
            }],
        }


class FakeFacts:
    def __init__(self):
        self.calls = []

    async def get_annual_metrics(self, request):
        self.calls.append(request)
        return (
            AnnualMetricFact(
                issuer=request.issuer, metric="revenue", value=Decimal("3500000"),
                unit=ValueUnit.MONEY, currency="USD",
                period_start=date(2024, 1, 1), period_end=date(2024, 12, 31),
                accession="0000012345-26-000007", filed_on=date(2026, 3, 4),
                source_reference=(
                    "https://data.sec.gov/api/xbrl/companyfacts/CIK0000012345.json"
                ),
                taxonomy="us-gaap", tag="Revenues", retrieved_at=datetime.now(UTC),
            ),
        )


class FakeResearchModel:
    def __init__(self, response=None):
        self.calls = []
        self.response = response if response is not None else answer()

    async def generate(self, *, instructions, evidence, question):
        self.calls.append({"instructions": instructions, "evidence": evidence, "question": question})
        return self.response


def run(coordinator):
    return asyncio.run(coordinator.run(
        cik=CIK, contact="Research research@example.org",
        model_key="fake-super-secret", model_name="gpt-4.1-mini",
        question="What are the business strengths and risks?",
    ))


def coordinator(*, empty=False, response=None):
    filing = FakeDocument(empty=empty)
    facts = FakeFacts()
    model = FakeResearchModel(response)
    service = AiResearchCoordinator(
        evidence_factory=lambda contact: filing,
        fundamentals_factory=lambda contact: facts,
        model_factory=lambda key, model_name: model,
    )
    return service, filing, facts, model


def test_ai_sends_only_approved_sec_evidence_and_builds_citations_from_sources():
    engine, filing, facts, model = coordinator()
    result = run(engine)
    assert result["mode"] == "ai_assisted_sec_limited_not_verified"
    assert result["model_executed"] is True
    assert result["analysis"]["findings"][0]["evidence_ids"] == [DOC_ID]
    assert result["analysis"]["bear_case"]["evidence_ids"] == [DOC_ID]
    assert DOC_ID in result["source_records"]
    assert FACT_ID in result["source_records"]
    assert result["source_records"][DOC_ID]["source_url"].startswith("https://www.sec.gov/")
    assert result["source_records"][FACT_ID]["source_url"].startswith("https://data.sec.gov/")
    assert filing.calls == [(CIK, "all")]
    assert facts.calls[0].issuer == IssuerId("SEC_CIK", CIK)
    assert len(model.calls) == 1
    prompt = model.calls[0]
    assert "UNTRUSTED DATA" in prompt["instructions"]
    assert "twelvedata" not in json.dumps(prompt).lower()
    assert "fake-super-secret" not in json.dumps(prompt)
    assert "research@example.org" not in json.dumps(prompt)
    assert "3500000" in json.dumps(prompt["evidence"])
    assert "Model" not in json.dumps(prompt["evidence"])
    assert result["source_records"][DOC_ID]["excerpt"] == "Issuer reports competition and risks."


def test_no_eligible_passages_means_no_facts_or_model_request():
    engine, _, facts, model = coordinator(empty=True)
    with pytest.raises(ModelFailure, match="No eligible"):
        run(engine)
    assert facts.calls == []
    assert model.calls == []


@pytest.mark.parametrize("bad", [
    answer("sec:made-up"),
    {**answer(), "findings": []},
    {**answer(), "bear_case": {"claim": "Unknown", "evidence_ids": ["bogus"]}},
    {**answer(), "overview": "x" * 700},
    {**answer(), "open_questions": []},
    {**answer(), "extra": "hidden"},
])
def test_invalid_or_fabricated_model_output_fails_closed(bad):
    engine, _, _, model = coordinator(response=bad)
    with pytest.raises(ModelFailure):
        run(engine)
    assert len(model.calls) == 1


def test_validator_allows_unattributed_counter_thesis_as_hypothesis_only():
    raw = answer()
    raw["bear_case"]["evidence_ids"] = []
    assert validate_answer(raw, {DOC_ID})["bear_case"]["evidence_ids"] == []


def test_strict_model_configuration_and_private_api_key():
    with pytest.raises(ValueError):
        OpenAIResponseModel(api_key="a\nsecret")
    with pytest.raises(ValueError):
        OpenAIResponseModel(api_key="safe-key-of-length", model="arbitrary-provider")
    model = OpenAIResponseModel(api_key="test-secret-key", model="gpt-4.1-mini")
    assert model.model == "gpt-4.1-mini"
    assert "test-secret-key" not in repr(model)


def test_model_request_has_no_tools_retention_or_arbitrary_endpoint():
    model = OpenAIResponseModel(api_key="private-model-key")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, count):
            assert count == 64001
            return json.dumps({
                "status": "completed",
                "output": [{"type": "message", "content": [{
                    "type": "output_text", "text": json.dumps(answer()),
                }]}],
            }).encode()

    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://api.openai.com/v1/responses"
            assert request.get_method() == "POST"
            assert timeout == 35
            assert request.get_header("Authorization") == "Bearer private-model-key"
            payload = json.loads(request.data)
            assert payload["store"] is False
            assert payload["tool_choice"] == "none"
            assert payload["max_output_tokens"] <= 1300
            assert payload["text"]["format"]["strict"] is True
            assert "private-model-key" not in json.dumps(payload)
            return Response()

    with patch("investiq_core.ai_research.build_opener", return_value=Opener()):
        result = model._post({
            "model": model.model, "store": False, "tool_choice": "none",
            "max_output_tokens": 1300,
            "instructions": "Safe bounded instructions",
            "input": '{"some":"SEC evidence"}',
            "text": {"format": {"type": "json_schema", "strict": True}},
        })
    assert result == answer()


def test_model_http_error_does_not_reflect_key_or_provider_body():
    model = OpenAIResponseModel(api_key="private-model-key")

    class Opener:
        def open(self, request, timeout):
            raise HTTPError(request.full_url, 401, "private-model-key", {}, None)

    with patch("investiq_core.ai_research.build_opener", return_value=Opener()):
        with pytest.raises(ModelFailure) as err:
            model._post({"input": "bounded"})
    assert "private-model-key" not in str(err.value)
    assert "credential" in str(err.value)


def test_question_must_be_bounded_before_provider_calls():
    engine, filing, _, model = coordinator()
    with pytest.raises(ModelFailure):
        asyncio.run(engine.run(
            cik=CIK, contact="Research research@example.org",
            model_key="fake-key", model_name="gpt-4.1-mini",
            question="x" * 500,
        ))
    assert filing.calls == []
    assert model.calls == []
