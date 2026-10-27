"""Explicit private thesis decisions via the EXISTING versioned snapshot store.

Browser research provides a current, unlicensed-price view. This adapter
creates a conservative *decision-only* snapshot: researcher-authored thesis,
invalidation conditions and optionally user-authored scenario parameters.
NO vendor quote/price, full filing, AI response or per-share EPS is retained.
The existing store validates history, file permissions, hashes and offline replay.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .evidence import InstrumentId
from .interactive_scenarios import evaluate_hypothetical
from .market import IssuerId
from .research_snapshot import REPLAY_METHOD, ResearchSnapshot, replay_snapshot
from .snapshot_store import (
    LocalSnapshotStore,
    _name,
    export_snapshot_json,
    render_snapshot_markdown,
)
from .thesis import ThesisSnapshot, ThesisStage

_MAX_VERSIONS = 100
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def _line(value: Any, *, label: str, maximum: int) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise ValueError(f"{label} must contain 1–{maximum} characters")
    if any(ord(x) < 32 and x not in "\n\t" for x in value):
        raise ValueError(f"{label} contains unsupported control characters")
    return value.strip()


def _texts(value: Any, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 5:
        raise ValueError(f"{label} must be a list of at most five entries")
    result = tuple(_line(x, label=label, maximum=200) for x in value)
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must not contain duplicates")
    return result


class BrowserDecisionHistory:
    """Opt-in local-only decision workspace; no key/account/cloud dependency."""

    def __init__(self, directory: Path | None):
        self.directory = Path(directory) if directory is not None else None
        if self.directory is not None and not self.directory.is_absolute():
            raise ValueError("Private decision folder must be an absolute path")

    @property
    def enabled(self) -> bool:
        return self.directory is not None

    def _store(self) -> LocalSnapshotStore:
        if self.directory is None:
            raise PermissionError("Research saving is off; launch the app with --research-dir")
        return LocalSnapshotStore(self.directory)

    def _all_snapshots(self, store: LocalSnapshotStore) -> list[dict[str, Any]]:
        """Inspect ALL existing revisions before computing the next revision."""
        store._check_root()
        files = sorted(store.root.iterdir(), key=lambda x: x.name)
        if len(files) > 1000:
            raise ValueError("Private store has too many entries for the local preview")
        records = []
        for item in files:
            match = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9_-]{0,63})-([0-9]{8})\.json", item.name)
            if match is None:
                continue
            decision = store.load(match.group(1), int(match.group(2)))
            records.append(self._summary(decision))
        return records

    def list(self) -> dict[str, Any]:
        store = self._store()
        records = self._all_snapshots(store)
        return {
            "mode": "local_private_history",
            "enabled": True,
            "snapshots": sorted(
                records, key=lambda x: (x["saved_at"], x["thesis_id"], x["revision"]),
                reverse=True,
            )[:_MAX_VERSIONS],
            "retention": (
                "Browser saves omit quotes, AI output, EPS and entry prices; "
                "older qualified CLI snapshots may retain permitted public facts "
                "or explicitly licensed quotes. Inspect quote_retained on each record."
            ),
        }

    @staticmethod
    def _summary(snapshot: ResearchSnapshot) -> dict[str, Any]:
        t = snapshot.thesis
        return {
            "thesis_id": t.thesis_id,
            "revision": t.revision,
            "stage": t.stage.value,
            "statement": t.statement,
            "reason": t.revision_reason,
            "risks": list(t.risks),
            "invalidation_triggers": list(t.invalidation_triggers),
            "symbol": t.instrument.ticker,
            "venue": t.instrument.venue,
            "currency": t.instrument.trading_currency,
            "issuer_cik": snapshot.issuer.value,
            "saved_at": snapshot.saved_at.isoformat(),
            "digest_sha256": snapshot.digest,
            "thesis_digest": t.digest,
            "parent_digest": t.parent_digest,
            "scenario_assumptions_retained": bool(snapshot.scenarios),
            "quote_retained": snapshot.quote is not None,
            "ai_analysis_retained": False,
            "annual_facts_retained": len(snapshot.annual_facts),
        }

    def load(self, thesis_id: str, revision: int) -> dict[str, Any]:
        snap = self._store().load(thesis_id, revision)
        replay = replay_snapshot(snap)
        return {
            **self._summary(snap),
            "mode": "offline_replay_of_private_decision",
            "scenario_assumptions": [
                {"name": s.name, "annual_growth_percent": s.annual_eps_growth * 100,
                 "terminal_pe": s.terminal_pe, "weight_percent": s.probability * 100}
                for s in snap.scenarios
            ],
            "scenario_years": snap.scenario_years,
            "replay_warnings": list(replay.warnings),
            "replay_numerical_price_analysis": (
                replay.annual_pe_proxy is not None or replay.scenarios is not None
            ),
            "reported_annual_pe_proxy": (
                str(replay.annual_pe_proxy)
                if replay.annual_pe_proxy is not None else None
            ),
            "saved_data_scope": (
                "v02_qualified_input_snapshot" if snap.quote is not None or snap.annual_facts
                else "authored_thesis_and_hypothetical_parameters_only"
            ),
        }

    def export(self, thesis_id: str, revision: int, format: str) -> dict[str, str]:
        if format not in ("json", "markdown"):
            raise ValueError("Choose JSON or Markdown export")
        snap = self._store().load(thesis_id, revision)
        contents = (
            export_snapshot_json(snap) if format == "json"
            else render_snapshot_markdown(snap) + "\n"
        )
        return {
            "filename": _name(thesis_id, revision).replace(
                ".json", ".json" if format == "json" else ".md"
            ),
            "format": format,
            "content": contents,
            "privacy_warning": (
                "Contains private user-authored research. Review before redistribution; "
                "this export is not proof of historical authorship or price entitlement."
            ),
        }

    def save(
        self, *, symbol: str, venue: str, cik: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(data, dict) or set(data) != {
            "thesis_id", "statement", "reason", "stage", "risks",
            "invalidation_triggers", "hypothetical",
        }:
            raise ValueError("Unsupported private decision save payload")
        thesis_id = data["thesis_id"]
        _name(thesis_id, 1)  # existing safe filename contract
        if not isinstance(thesis_id, str) or _ID.fullmatch(thesis_id) is None:
            raise ValueError("Unsafe thesis identifier")
        statement = _line(data["statement"], label="Thesis", maximum=1400)
        reason = _line(data["reason"], label="Revision reason", maximum=400)
        stage = ThesisStage(data["stage"])
        risks = _texts(data["risks"], label="Risks")
        triggers = _texts(data["invalidation_triggers"], label="Invalidation conditions")
        scenario_years = None
        scenarios = ()
        if data["hypothetical"] is not None:
            # Validate full input contract, then retain ONLY growth/multiple/weights
            # and holding years. EPS and entry price may represent restricted or
            # incompatible inputs; never persist them through this UI.
            normalized = evaluate_hypothetical(data["hypothetical"])["inputs"]
            from .valuation import ValuationScenario

            scenario_years = normalized["years"]
            scenarios = tuple(
                ValuationScenario(
                    name=s["name"], annual_eps_growth=s["annual_growth_percent"] / 100,
                    terminal_pe=s["terminal_pe"], probability=s["weight_percent"] / 100,
                )
                for s in normalized["scenarios"]
            )
        store = self._store()
        existing = self._all_snapshots(store)
        prior = [
            item for item in existing if item["thesis_id"] == thesis_id
        ]
        if len(prior) >= _MAX_VERSIONS:
            raise ValueError("Thesis revision count exceeds supported preview limit")
        revision = max((x["revision"] for x in prior), default=0) + 1
        previous = store.load(thesis_id, revision - 1) if revision > 1 else None
        instrument = InstrumentId(symbol, venue, "USD")
        if previous is not None and (
            previous.thesis.instrument != instrument
            or previous.issuer != IssuerId("SEC_CIK", cik)
        ):
            raise ValueError("A thesis identifier cannot be reused for another issuer")
        now = datetime.now(UTC)
        thesis = ThesisSnapshot(
            thesis_id=thesis_id, revision=revision, instrument=instrument,
            as_of=now, recorded_at=now, method_version=REPLAY_METHOD,
            stage=stage, statement=statement, revision_reason=reason,
            risks=risks, invalidation_triggers=triggers,
            parent_digest=previous.thesis.digest if previous is not None else None,
        )
        snap = ResearchSnapshot(
            thesis=thesis, saved_at=now, researched_at=now,
            issuer=IssuerId("SEC_CIK", cik), annual_facts=(), quote=None,
            share_basis_confirmed=False, share_basis_rationale=None,
            max_quote_age_seconds="3600",
            scenario_years=scenario_years, scenarios=scenarios,
        )
        store.save(snap)
        return {
            **self._summary(snap),
            "mode": "explicit_private_decision_saved",
            "saved_data_scope": "authored_thesis_and_hypothetical_parameters_only",
            "limitations": [
                "The original quote, EPS/entry-price assumptions and all price-derived outputs were NOT saved.",
                "No AI answer, source-document excerpts or licensed prices were retained.",
                "Hash linking detects accidental corruption, not an adversary or external timestamp.",
                "Reopen and offline replay cannot reconstruct price-only valuations without lawfully retained price inputs.",
            ],
        }
