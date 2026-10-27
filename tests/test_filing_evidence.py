"""PR 3 SEC 10-K evidence contracts: precise excerpts, fail-closed selection."""

from __future__ import annotations

import asyncio
import hashlib

import pytest

from investiq_core.filing_evidence import (
    SEC_ARCHIVE_ORIGIN,
    SEC_SUBMISSIONS_ORIGIN,
    SecFilingEvidenceProvider,
    extract_filing_text,
    select_annual_document,
    select_passages,
)
from investiq_core.market import IssuerId
from investiq_core.ports import ProviderFailure, ProviderFailureCode

CIK = IssuerId("SEC_CIK", "0000012345")
ACCESSION = "0000012345-26-000007"
DOC = "annual10k.htm"
METADATA = {
    "cik": 12345,
    "filings": {"recent": {
        "accessionNumber": ["0000012345-26-000010", ACCESSION],
        "form": ["10-Q", "10-K"],
        "filingDate": ["2026-06-14", "2026-03-04"],
        "primaryDocument": ["quarterly.htm", DOC],
    }},
}
BUSINESS = (
    "Our business operations include a fictional example that sells industrial "
    "equipment to commercial customers across several regions. We discuss "
    "operations, products and services as part of this illustrative report."
)
RISKS = (
    "Risk factors include fierce competition and uncertainty relating to "
    "industrial investment cycles. We face customer concentration exposure "
    "and potentially volatile demand in this purely fictional annual report."
)
MANAGEMENT = (
    "Management's discussion explains results of operations, the expected "
    "capital expenditures and liquidity position, along with limitations "
    "and uncertainties of these invented historical statements."
)
HTML = (
    "<html><head><script>hidden business risk operations</script>"
    "<style>body{risk: 1}</style></head><body>"
    "<p>Table of contents.</p>"
    "<p>" + BUSINESS + "</p><div>" + RISKS + "</div>"
    "<p>" + MANAGEMENT + "</p></body></html>"
)


class JsonFixture:
    def __init__(self, result=METADATA):
        self.result = result
        self.calls = []

    async def get_json(self, url, *, headers):
        self.calls.append((url, headers))
        return self.result


class HtmlFixture:
    def __init__(self, result=HTML):
        self.result = result
        self.calls = []

    async def get_html(self, url, *, headers):
        self.calls.append((url, headers))
        return self.result


def run(provider, topic="risks"):
    return asyncio.run(provider.inspect(CIK, topic=topic))


def test_metadata_uses_only_same_cik_recent_10k_primary_document():
    doc = select_annual_document(METADATA, issuer=CIK)
    assert doc.form == "10-K"
    assert doc.accession == ACCESSION
    assert doc.filed_on.isoformat() == "2026-03-04"
    assert doc.url == SEC_ARCHIVE_ORIGIN + "12345/000001234526000007/annual10k.htm"
    assert doc.metadata_url == SEC_SUBMISSIONS_ORIGIN + "CIK0000012345.json"


@pytest.mark.parametrize("document_name", [
    "../other.htm", "folder/file.htm", "file.pdf", ".hidden.htm",
    "index.htm?redirect=https://bad.test", "file..hidden.htm",
])
def test_bad_filing_document_path_fails_closed(document_name):
    bad = {
        **METADATA,
        "filings": {"recent": {
            "accessionNumber": [ACCESSION],
            "form": ["10-K"],
            "filingDate": ["2026-03-04"],
            "primaryDocument": [document_name],
        }},
    }
    with pytest.raises(ValueError, match="No supported"):
        select_annual_document(bad, issuer=CIK)


def test_bad_metadata_cik_and_lengths_fail_closed():
    with pytest.raises(ValueError, match="issuer"):
        select_annual_document({**METADATA, "cik": 12346}, issuer=CIK)
    incomplete = {
        **METADATA, "filings": {"recent": {
            "form": ["10-K"], "filingDate": ["2026-03-04"],
            "accessionNumber": [ACCESSION],
        }},
    }
    with pytest.raises(ValueError, match="incomplete"):
        select_annual_document(incomplete, issuer=CIK)


def test_document_text_strips_executable_markup_not_source_sentences():
    text = extract_filing_text(HTML)
    assert BUSINESS in text
    assert RISKS in text
    assert MANAGEMENT in text
    assert "hidden business" not in text
    assert "risk: 1" not in text
    passages = select_passages(text, topic="risks", accession=ACCESSION)
    assert passages
    assert any("competition" in item.excerpt for item in passages)
    for item in passages:
        assert text[item.extracted_start:item.extracted_end] == item.excerpt
        assert item.excerpt_sha256 == hashlib.sha256(item.excerpt.encode()).hexdigest()
        assert item.evidence_id.startswith("sec:" + ACCESSION + ":")
        assert len(item.excerpt) <= 700
    with pytest.raises(ValueError, match="topic"):
        select_passages(text, topic="unapproved", accession=ACCESSION)


def test_document_rejects_tiny_broken_and_oversized_text():
    for bad in ("", "<p>Too short</p>", "n" * 8_000_001):
        with pytest.raises(ValueError):
            extract_filing_text(bad)


def test_injected_full_inspection_is_dated_attributable_and_not_ai():
    meta, html = JsonFixture(), HtmlFixture()
    provider = SecFilingEvidenceProvider(
        user_agent="InvestIQ Research research@example.org",
        json_transport=meta, html_transport=html, min_interval_seconds=0.2,
    )
    result = run(provider, "risks")
    assert result["mode"] == "filing_passage_inspection_not_ai"
    assert result["issuer"] == "0000012345"
    assert result["topic"] == "risks"
    assert result["document"]["accession"] == ACCESSION
    assert result["passages"]
    assert "keyword" in result["limitations"][0].lower()
    assert meta.calls[0][0] == SEC_SUBMISSIONS_ORIGIN + "CIK0000012345.json"
    assert html.calls[0][0] == SEC_ARCHIVE_ORIGIN + "12345/000001234526000007/annual10k.htm"
    assert "research@example.org" in meta.calls[0][1]["User-Agent"]
    assert all("excerpt_sha256" in p for p in result["passages"])
    assert HTML not in str(result)  # No full filing body returned


def test_no_supported_recent_10k_surfaces_gap_not_fabrication():
    metadata = {
        **METADATA,
        "filings": {"recent": {
            "accessionNumber": [ACCESSION], "form": ["10-Q"],
            "filingDate": ["2026-03-04"], "primaryDocument": [DOC],
        }},
    }
    transport = JsonFixture(metadata)
    html = HtmlFixture()
    provider = SecFilingEvidenceProvider(
        user_agent="InvestIQ Research research@example.org",
        json_transport=transport, html_transport=html, min_interval_seconds=0.2,
    )
    with pytest.raises(ProviderFailure) as failure:
        run(provider)
    assert failure.value.code == ProviderFailureCode.MISSING_DATA
    assert not html.calls


def test_invalid_filing_html_is_rejected_not_returned_to_agent():
    provider = SecFilingEvidenceProvider(
        user_agent="InvestIQ Research research@example.org",
        json_transport=JsonFixture(), html_transport=HtmlFixture("<p>Too short</p>"),
        min_interval_seconds=0.2,
    )
    with pytest.raises(ProviderFailure) as failure:
        run(provider)
    assert failure.value.code == ProviderFailureCode.INVALID_RESPONSE


def test_no_keyword_match_returns_empty_and_discloses_limits():
    empty = (
        "<html><body><p>" + "This sample deliberately has no topic marker at all. " * 40
        + "</p></body></html>"
    )
    provider = SecFilingEvidenceProvider(
        user_agent="InvestIQ Research research@example.org",
        json_transport=JsonFixture(), html_transport=HtmlFixture(empty),
        min_interval_seconds=0.2,
    )
    result = run(provider, "risks")
    assert result["passages"] == []
    assert result["limitations"]
