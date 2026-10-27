"""Opt-in connected CLI commands; never run providers from import or replay.

The listing relationship is explicitly user asserted. Neither ticker-to-CIK
mapping nor market-data entitlements are silently inferred.
"""

from __future__ import annotations

import asyncio
import os
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from .adapters.sec_companyfacts import SecCompanyFactsProvider
from .adapters.sec_edgar import SecEdgarFilingProvider
from .adapters.twelve_data import TwelveDataQuoteProvider
from .application.connected_data import ConnectedDataService
from .application.connected_research import (
    CompanyResearchRequest,
    CompanyResearchResult,
    ConnectedResearchService,
)
from .evidence import InstrumentId
from .market import IssuerId, IssuerListing
from .research_snapshot import REPLAY_METHOD, capture_research_snapshot, replay_snapshot
from .snapshot_store import LocalSnapshotStore, export_snapshot_json, render_snapshot_markdown
from .thesis import ThesisSnapshot, ThesisStage


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(f"Connected research requires the {name} environment variable")
    return value


def _cik(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{1,10}", value) is None:
        raise ValueError("CIK must be one to ten decimal digits, supplied by the researcher")
    number = int(value)
    if number == 0:
        raise ValueError("SEC CIK cannot be zero")
    return f"{number:010d}"


def _build_service() -> ConnectedResearchService:
    """Factory isolated so acceptance tests can inject real adapters with fake HTTP."""
    quote_key = _env("TWELVE_DATA_API_KEY")
    sec_contact = _env("INVESTIQ_SEC_USER_AGENT")
    data = ConnectedDataService(
        quote_provider=TwelveDataQuoteProvider(api_key=quote_key),
        filing_provider=SecEdgarFilingProvider(user_agent=sec_contact),
        principal_scope="local-single-researcher",
    )
    return ConnectedResearchService(
        data=data,
        fundamentals=SecCompanyFactsProvider(user_agent=sec_contact),
    )


def _research_request(args: Any) -> CompanyResearchRequest:
    if type(args.max_age_minutes) is not int or not 1 <= args.max_age_minutes <= 1440:
        raise ValueError("max-age-minutes must be between 1 and 1440")
    confirmed = args.confirm_share_basis
    if confirmed != bool(args.basis_rationale):
        raise ValueError("--confirm-share-basis and --basis-rationale must be used together")
    source = args.listing_source
    if (
        not isinstance(source, str) or not source.strip()
        or any(char in source for char in ("\r", "\n"))
    ):
        raise ValueError("--listing-source must identify the researcher's verification source")
    try:
        start = date.fromisoformat(args.listing_from)
    except ValueError:
        raise ValueError("--listing-from must be an ISO calendar date") from None
    if start > datetime.now(UTC).date():
        raise ValueError("listing cannot become effective in the future")
    listing = IssuerListing(
        issuer=IssuerId("SEC_CIK", _cik(args.cik)),
        instrument=InstrumentId(args.symbol, args.venue, args.currency),
        effective_from=start,
        source_reference=source,
        verified_at=datetime.now(UTC),
    )
    return CompanyResearchRequest(
        listing=listing, max_quote_age=timedelta(minutes=args.max_age_minutes),
        analyst_confirmed_share_basis=confirmed,
        share_basis_rationale=args.basis_rationale,
    )


def _save_requested(args: Any) -> bool:
    fields = (
        args.save_dir, args.thesis_id, args.thesis_statement,
        args.revision_reason, args.stage,
    )
    if args.save_dir is None:
        if any(x is not None for x in fields[1:]) or args.revision != 1:
            raise ValueError("thesis options require an explicit --save-dir")
        return False
    if not (args.thesis_id and args.thesis_statement and args.revision_reason):
        raise ValueError(
            "Saving requires --thesis-id, --thesis-statement and --revision-reason"
        )
    if type(args.revision) is not int or not 1 <= args.revision <= 99999999:
        raise ValueError("revision must be a positive number")
    return True


def _render_current(result: CompanyResearchResult) -> dict[str, Any]:
    """Expose a viewed price without copying entitlement tokens or provider URLs."""
    q = result.quote.quote
    return {
        "mode": "connected_current_view_not_saved",
        "issuer": result.issuer,
        "symbol": q.instrument.ticker,
        "venue": q.instrument.venue,
        "currency": q.currency,
        "quote": {
            "price": str(q.price),
            "kind": q.kind.value,
            "source": q.provider,
            "market_event_at": q.event_at.isoformat(),
            "received_at": q.received_at.isoformat(),
            "timeliness": q.timeliness.value,
            "market_session": q.session.value,
            "adjustment": q.adjustment.value,
            "freshness": result.quote.freshness.value,
            "snapshot_right": q.rights.snapshot.value,
        },
        "annual_facts": [
            {
                "metric": item.metric,
                "value": str(item.value),
                "unit": item.unit.value,
                "currency": item.currency,
                "fiscal_start": item.period_start.isoformat(),
                "fiscal_end": item.period_end.isoformat(),
                "filing_date": item.filed_on.isoformat(),
                "accession": item.accession,
                "source_reference": item.source_reference,
            }
            for item in result.annual_facts
        ],
        "reported_annual_pe_proxy": (
            str(result.annual_pe_proxy) if result.annual_pe_proxy is not None else None
        ),
        "warnings": list(result.warnings),
    }


async def research(args: Any) -> dict[str, Any]:
    """One connected read; optional explicit, license-gated local decision save."""
    should_save = _save_requested(args)
    request = _research_request(args)
    result = await _build_service().analyze(request, refresh=True)
    response = _render_current(result)
    if should_save:
        # The store is created only after a successful connected analysis.
        root = Path(args.save_dir)
        store = LocalSnapshotStore(root)
        parent = None
        if args.revision > 1:
            parent = store.load(args.thesis_id, args.revision - 1).thesis.digest
        saved_at = datetime.now(UTC)
        thesis = ThesisSnapshot(
            thesis_id=args.thesis_id, revision=args.revision,
            instrument=request.listing.instrument,
            as_of=result.observed_at, recorded_at=saved_at,
            method_version=REPLAY_METHOD,
            stage=ThesisStage(args.stage or ThesisStage.RESEARCHING.value),
            statement=args.thesis_statement,
            revision_reason=args.revision_reason,
            parent_digest=parent,
        )
        snap = capture_research_snapshot(result, request, thesis, saved_at=saved_at)
        destination = store.save(snap)
        response["saved_decision"] = {
            "path": str(destination),
            "digest_sha256": snap.digest,
            "revision": snap.thesis.revision,
            "quote_retained": snap.quote is not None,
            "note": (
                "Snapshot contains only entitled quote inputs; "
                "UNKNOWN/DENIED price rights omit price-derived replay."
            ),
        }
    return response


def replay(store_dir: Path, thesis_id: str, revision: int, *, format: str) -> str:
    """Offline only: importing the snapshot is a strict no-network operation."""
    snapshot = LocalSnapshotStore(store_dir).load(thesis_id, revision)
    if format == "markdown":
        return render_snapshot_markdown(snapshot) + "\n"
    if format == "manifest":
        return export_snapshot_json(snapshot)
    if format != "summary":
        raise ValueError("unsupported replay output format")
    outcome = replay_snapshot(snapshot)
    import json

    return json.dumps(
        {
            "mode": "offline_replay_no_provider_calls",
            "thesis_id": snapshot.thesis.thesis_id,
            "revision": snapshot.thesis.revision,
            "saved_at": snapshot.saved_at.isoformat(),
            "snapshot_digest": outcome.snapshot_digest,
            "quote_retained": snapshot.quote is not None,
            "reported_annual_pe_proxy": (
                str(outcome.annual_pe_proxy) if outcome.annual_pe_proxy is not None else None
            ),
            "scenario_count": len(outcome.scenarios.outcomes) if outcome.scenarios else 0,
            "warnings": list(outcome.warnings),
        },
        indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n"


def run_research(args: Any) -> dict[str, Any]:
    return asyncio.run(research(args))
