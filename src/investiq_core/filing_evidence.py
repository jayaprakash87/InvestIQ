"""Bounded, attributable SEC 10-K passages for investor-controlled research.

This is deterministic keyword-based retrieval, NOT AI interpretation, legal
item-level section validation, or proof that an excerpt supports a thesis.
No raw filing is cached/saved; only small excerpts reach the local UI.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html.parser import HTMLParser
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from .adapters._errors import translate_error
from .adapters._http import (
    JsonTransport,
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
    UrllibJsonTransport,
    _RejectRedirect,
)
from .market import IssuerId
from .ports import ProviderFailure, ProviderFailureCode

SEC_SUBMISSIONS_ORIGIN = "https://data.sec.gov/submissions/"
SEC_ARCHIVE_ORIGIN = "https://www.sec.gov/Archives/edgar/data/"
MAX_DOCUMENT_BYTES = 8_000_000
MAX_EXTRACTED_CHARS = 3_000_000
_TOPIC_WORDS: dict[str, tuple[str, ...]] = {
    "business": ("business", "operations", "products", "services", "customers"),
    "risks": ("risk", "risks", "competition", "uncertainty", "exposure"),
    "management": ("management", "results", "operations", "liquidity", "capital"),
}
_FAILURES = (
    TransportInvalidResponseError,
    TransportStatusError,
    TransportTimeoutError,
    TransportUnavailableError,
)
_DOCUMENT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,180}\.(?:htm|html|txt)", re.IGNORECASE)
_ACCESSION = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}")


@dataclass(frozen=True, slots=True)
class FilingDocument:
    cik: str
    accession: str
    form: str
    filed_on: date
    filename: str
    url: str
    metadata_url: str


@dataclass(frozen=True, slots=True)
class EvidencePassage:
    evidence_id: str
    topic: str
    excerpt: str
    extracted_start: int
    extracted_end: int
    excerpt_sha256: str


class FilingHtmlTransport(Protocol):
    async def get_html(self, url: str, *, headers: dict[str, str]) -> str: ...


class UrllibFilingHtmlTransport:
    """Exact SEC HTTPS document host; no redirects and bounded response size."""

    async def get_html(self, url: str, *, headers: dict[str, str]) -> str:
        if not url.startswith(SEC_ARCHIVE_ORIGIN):
            raise TransportInvalidResponseError("Unexpected filing document host")
        return await asyncio.to_thread(self._read, url, headers)

    @staticmethod
    def _read(url: str, headers: dict[str, str]) -> str:
        req = Request(
            url, method="GET",
            headers={"Accept": "text/html,text/plain", "Accept-Encoding": "identity", **headers},
        )
        try:
            with build_opener(_RejectRedirect()).open(req, timeout=12) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(
                    t in content_type
                    for t in ("text/html", "text/plain", "application/xhtml+xml")
                ):
                    raise TransportInvalidResponseError("Unexpected filing content type")
                raw = response.read(MAX_DOCUMENT_BYTES + 1)
        except HTTPError as exc:
            raise TransportStatusError(exc.code) from None
        except TimeoutError:
            raise TransportTimeoutError() from None
        except (URLError, OSError):
            raise TransportUnavailableError() from None
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise TransportInvalidResponseError("Filing exceeds bounded response limit")
        try:
            # Avoid attributing silently repaired characters as exact evidence.
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise TransportInvalidResponseError("Filing text encoding not supported") from None


def select_annual_document(payload: Any, *, issuer: IssuerId) -> FilingDocument:
    """Select newest recent 10-K primary HTML document; reject malformed metadata."""
    if issuer.namespace != "SEC_CIK" or not re.fullmatch(r"[0-9]{10}", issuer.value):
        raise ValueError("Expected normalized SEC CIK")
    if not isinstance(payload, dict):
        raise TypeError("SEC submissions must be an object")
    raw_cik = payload.get("cik")
    if type(raw_cik) is int:
        cik = raw_cik
    elif isinstance(raw_cik, str) and re.fullmatch(r"[0-9]{1,10}", raw_cik):
        cik = int(raw_cik)
    else:
        raise ValueError("Invalid SEC submissions CIK")
    if cik != int(issuer.value):
        raise ValueError("Submissions issuer does not match selected CIK")
    filings = payload.get("filings")
    recent = filings.get("recent") if isinstance(filings, dict) else None
    if not isinstance(recent, dict):
        raise TypeError("SEC submissions recent filings missing")
    keys = ("accessionNumber", "form", "filingDate", "primaryDocument")
    arrays = [recent.get(k) for k in keys]
    if not all(isinstance(a, list) for a in arrays):
        raise ValueError("SEC submissions filing metadata incomplete")
    if len({len(a) for a in arrays}) != 1 or len(arrays[0]) > 500_000:
        raise ValueError("SEC submissions filing metadata lengths disagree")
    candidates: list[FilingDocument] = []
    for acc, form, filed, filename in zip(*arrays):
        if form != "10-K":
            continue
        if not isinstance(acc, str) or _ACCESSION.fullmatch(acc) is None:
            raise ValueError("SEC annual accession invalid")
        if not isinstance(filed, str):
            raise TypeError("SEC annual filing date invalid")
        try:
            filed_on = date.fromisoformat(filed)
        except ValueError:
            raise ValueError("SEC annual filing date invalid") from None
        if (
            not isinstance(filename, str)
            or _DOCUMENT_NAME.fullmatch(filename) is None
            or ".." in filename
        ):
            # A PDF, a path, or an unexpected document extension cannot be
            # silently substituted with a different exhibit or filing.
            continue
        cik_value = str(int(issuer.value))
        url = (
            f"{SEC_ARCHIVE_ORIGIN}{cik_value}/{acc.replace('-', '')}/{filename}"
        )
        candidates.append(FilingDocument(
            cik=issuer.value, accession=acc, form="10-K", filed_on=filed_on,
            filename=filename, url=url,
            metadata_url=f"{SEC_SUBMISSIONS_ORIGIN}CIK{issuer.value}.json",
        ))
    if not candidates:
        raise ValueError("No supported 10-K primary HTML in SEC recent submissions")
    return max(candidates, key=lambda d: (d.filed_on, d.accession))


class _HtmlText(HTMLParser):
    """Render normalized, non-executable text from SEC inline-XBRL HTML."""

    _BREAKS = frozenset({
        "div", "p", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
        "section", "table", "blockquote",
    })
    _HIDDEN = frozenset({"script", "style", "noscript", "svg", "head"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._HIDDEN:
            self.ignored.append(tag)
        if not self.ignored and tag in self._BREAKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._HIDDEN and tag in self.ignored:
            # Ignore content up to the matching ignored closing element.
            index = len(self.ignored) - 1 - self.ignored[::-1].index(tag)
            self.ignored = self.ignored[:index]
        if not self.ignored and tag in self._BREAKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored:
            self.parts.append(data)


def extract_filing_text(html: str) -> str:
    """Stable normalized text; exact excerpts refer to offsets in THIS text."""
    if not isinstance(html, str) or not html.strip() or len(html) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document empty or exceeds supported extraction size")
    parser = _HtmlText()
    try:
        parser.feed(html)
        parser.close()
    except (ValueError, AssertionError):
        raise ValueError("Filing HTML could not be parsed") from None
    lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).split("\n")]
    text = "\n".join(line for line in lines if line)
    if not 500 <= len(text) <= MAX_EXTRACTED_CHARS:
        raise ValueError("Document text is too short or too large to qualify")
    return text


def select_passages(
    text: str, *, topic: str, accession: str, max_passages: int = 4
) -> tuple[EvidencePassage, ...]:
    """Return bounded exact substrings selected by visible keywords, not AI."""
    if topic not in _TOPIC_WORDS or type(max_passages) is not int or not 1 <= max_passages <= 6:
        raise ValueError("Unsupported evidence topic or passage limit")
    if not isinstance(text, str) or len(text) > MAX_EXTRACTED_CHARS:
        raise ValueError("Unqualified document text")
    needles = _TOPIC_WORDS[topic]
    ranked: list[tuple[int, int, str]] = []
    cursor = 0
    seen: set[str] = set()
    for line in text.split("\n"):
        position = cursor
        cursor += len(line) + 1
        if not 130 <= len(line) <= 5_000:
            continue
        lower = line.casefold()
        if lower in seen or "table of contents" in lower:
            continue
        # Word boundaries, not arbitrary substring: e.g. risk != brisk.
        hits = sum(bool(re.search(r"\b" + w + r"\b", lower)) for w in needles)
        if hits:
            seen.add(lower)
            ranked.append((hits, position, line))
    ranked.sort(key=lambda p: (-p[0], p[1]))
    passages: list[EvidencePassage] = []
    for _, start, paragraph in ranked[:max_passages]:
        excerpt = paragraph[:700]
        digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
        passages.append(EvidencePassage(
            evidence_id=f"sec:{accession}:{start}:{digest[:16]}",
            topic=topic, excerpt=excerpt, extracted_start=start,
            extracted_end=start + len(excerpt), excerpt_sha256=digest,
        ))
    return tuple(passages)


class SecFilingEvidenceProvider:
    """SEC 10-K candidate document + on-demand exact passage inspection."""

    def __init__(
        self,
        *, user_agent: str, json_transport: JsonTransport | None = None,
        html_transport: FilingHtmlTransport | None = None,
        min_interval_seconds: float = 1.0,
    ) -> None:
        if (
            not isinstance(user_agent, str) or not 8 <= len(user_agent) <= 200
            or not user_agent.isascii() or "@" not in user_agent
            or "\r" in user_agent or "\n" in user_agent
        ):
            raise ValueError("SEC requires a declared User-Agent contact")
        if not isinstance(min_interval_seconds, (float, int)) or not 0.2 <= min_interval_seconds <= 60:
            raise ValueError("Invalid SEC pacing interval")
        self._user_agent = user_agent
        self._json = json_transport or UrllibJsonTransport(max_bytes=8_000_000)
        self._html = html_transport or UrllibFilingHtmlTransport()
        self._delay = min_interval_seconds

    async def inspect(self, issuer: IssuerId, *, topic: str) -> dict[str, Any]:
        if topic not in _TOPIC_WORDS:
            raise ValueError("Unknown document research topic")
        if issuer.namespace != "SEC_CIK" or re.fullmatch(r"[0-9]{10}", issuer.value) is None:
            raise ValueError("Expected normalized SEC issuer CIK")
        url = f"{SEC_SUBMISSIONS_ORIGIN}CIK{issuer.value}.json"
        try:
            payload = await self._json.get_json(
                url, headers={"User-Agent": self._user_agent}
            )
        except _FAILURES as exc:
            raise translate_error("SEC EDGAR", exc) from None
        try:
            doc = select_annual_document(payload, issuer=issuer)
        except (ValueError, TypeError):
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.MISSING_DATA,
                "No supported recent 10-K primary HTML filing document",
            ) from None
        # SEC published fair-access guidance; never issue simultaneous SEC
        # requests on this operation, or bulk crawl. Delay after submissions.
        await asyncio.sleep(self._delay)
        try:
            html = await self._html.get_html(
                doc.url, headers={"User-Agent": self._user_agent}
            )
        except _FAILURES as exc:
            raise translate_error("SEC EDGAR", exc) from None
        try:
            text = extract_filing_text(html)
            passages = select_passages(text, topic=topic, accession=doc.accession)
        except (ValueError, TypeError):
            raise ProviderFailure(
                "SEC EDGAR", ProviderFailureCode.INVALID_RESPONSE,
                "SEC filing text could not be safely extracted",
            ) from None
        return {
            "mode": "filing_passage_inspection_not_ai",
            "issuer": issuer.value,
            "topic": topic,
            "document": {
                "form": doc.form, "accession": doc.accession,
                "filed_on": doc.filed_on.isoformat(), "source_url": doc.url,
                "metadata_url": doc.metadata_url,
                "extraction_basis": "normalized_HTML_text",
                "document_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            },
            "passages": [{
                "evidence_id": p.evidence_id, "topic": p.topic,
                "excerpt": p.excerpt,
                "extracted_start": p.extracted_start,
                "extracted_end": p.extracted_end,
                "excerpt_sha256": p.excerpt_sha256,
            } for p in passages],
            "retrieved_at": datetime.now(UTC).isoformat(),
            "limitations": [
                "Keyword-matched filing excerpts are not verified SEC Item sections.",
                "Extracted-text offsets are not original HTML byte positions.",
                "A citation identifies a retrieved passage, not proof of any investment claim.",
                "Selected document is a recent 10-K; historical pagination and amendments are unsupported.",
                "Full filing text is not stored; this response is for inspection only.",
            ],
        }
