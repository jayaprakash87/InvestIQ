"""Private append-only research decision store and safe JSON/Markdown export.

Filesystem storage is explicit, never triggered by live price retrieval.
Local content hashes detect corruption (not malicious rewriting by file owner).
"""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any

from .research_snapshot import ResearchSnapshot, _canonical, replay_snapshot
from .thesis import validate_thesis_history

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
_MAX_BYTES = 2_000_000


def _name(thesis_id: str, revision: int) -> str:
    if not isinstance(thesis_id, str) or _ID.fullmatch(thesis_id) is None:
        raise ValueError("thesis_id must be a safe short filename identifier")
    if type(revision) is not int or not 1 <= revision <= 99999999:
        raise ValueError("revision out of supported range")
    return f"{thesis_id}-{revision:08d}.json"


def export_snapshot_json(snapshot: ResearchSnapshot) -> str:
    if not isinstance(snapshot, ResearchSnapshot):
        raise TypeError("snapshot must be ResearchSnapshot")
    payload = snapshot.to_record()
    result = {"digest_sha256": snapshot.digest, "payload": payload}
    return json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def import_snapshot_json(raw: str) -> ResearchSnapshot:
    if not isinstance(raw, str):
        raise TypeError("snapshot JSON must be text")
    if len(raw.encode("utf-8")) > _MAX_BYTES:
        raise ValueError("snapshot exceeds local size limit")
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key in snapshot")
            result[key] = value
        return result

    document = json.loads(
        raw, object_pairs_hook=no_duplicates,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON value")),
    )
    if not isinstance(document, dict) or set(document) != {"digest_sha256", "payload"}:
        raise ValueError("snapshot envelope must contain digest and payload")
    payload = document["payload"]
    if not isinstance(payload, dict):
        raise TypeError("snapshot payload must be a JSON object")
    digest = document["digest_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("snapshot digest must be SHA-256 hex")
    from hashlib import sha256
    if sha256(_canonical(payload)).hexdigest() != digest:
        raise ValueError("snapshot digest mismatch; saved inputs may have changed")
    snapshot = ResearchSnapshot.from_record(payload)
    if snapshot.to_record() != payload or snapshot.digest != digest:
        raise ValueError("snapshot does not round-trip under current method/schema")
    replay_snapshot(snapshot)  # Reject calculations that cannot replay deterministically.
    return snapshot


def _md(value: str) -> str:
    """Prevent HTML injection and Markdown formatting from arbitrary note fields."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
        .replace("#", "\\#")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def render_snapshot_markdown(snapshot: ResearchSnapshot) -> str:
    """Generate a reproducible, license-respecting offline decision report."""
    replay = replay_snapshot(snapshot)
    instrument = snapshot.thesis.instrument
    parts = [
        f"# InvestIQ research decision: {_md(snapshot.thesis.thesis_id)}",
        "",
        f"- Revision: {snapshot.thesis.revision}",
        f"- Research stage: {_md(snapshot.thesis.stage.value)}",
        f"- Instrument: {instrument.ticker} / {instrument.venue} / {instrument.trading_currency}",
        f"- Issuer: {_md(snapshot.issuer.namespace)}:{_md(snapshot.issuer.value)}",
        f"- Recorded: {snapshot.saved_at.isoformat()}",
        f"- Research cutoff: {snapshot.thesis.as_of.isoformat()}",
        f"- Method: {_md(snapshot.method_version)}",
        f"- Digest: `{snapshot.digest}`",
        "",
        "## Thesis",
        "",
        _md(snapshot.thesis.statement),
        "",
        f"Revision rationale: {_md(snapshot.thesis.revision_reason)}",
        "",
        "## Risks and invalidation conditions",
        "",
        "### Risks",
        "",
    ]
    parts.extend(
        f"- {_md(item)}" for item in snapshot.thesis.risks
    )
    if not snapshot.thesis.risks:
        parts.append("- Not recorded")
    parts.extend(["", "### Conditions that would invalidate the thesis", ""])
    parts.extend(
        f"- {_md(item)}" for item in snapshot.thesis.invalidation_triggers
    )
    if not snapshot.thesis.invalidation_triggers:
        parts.append("- Not recorded")
    parts.extend([
        "",
        "## Retained SEC annual financial evidence",
        "",
        "| Metric | Value | Unit | Period end | Filing date | Accession |",
        "| --- | ---: | --- | --- | --- | --- |",
    ])
    for f in sorted(snapshot.annual_facts, key=lambda x: x.metric):
        parts.append(
            f"| {_md(f.metric)} | {f.value} | {_md(f.unit.value)} "
            f"{_md(f'({f.currency})' if f.currency else '')} | "
            f"{f.period_end.isoformat()} | {f.filed_on.isoformat()} | {_md(f.accession)} |"
        )
    if not snapshot.annual_facts:
        parts.append("| No eligible annual SEC facts retained | — | — | — | — | — |")
    parts.extend(["", "## Retained user scenario assumptions", ""])
    if snapshot.scenarios:
        parts.append(f"- Hypothetical holding period: {snapshot.scenario_years} years")
        for item in snapshot.scenarios:
            parts.append(
                f"- {_md(item.name)}: annual EPS growth {item.annual_eps_growth:.2%}; "
                f"terminal P/E {item.terminal_pe:.4g}; "
                f"subjective weight {item.probability:.2%}"
            )
        parts.append(
            "- These are user-authored assumptions, not independently verified "
            "forecasts. Numerical replay requires separately eligible price and EPS inputs."
        )
    else:
        parts.append("- No hypothetical scenario parameters retained")
    parts.extend(["", "## Price-sensitive analysis", ""])
    if snapshot.quote is None:
        parts.append(
            "Quote price, source event details and all price-derived valuations were "
            "**not retained** because snapshot rights were not explicitly granted."
        )
    else:
        q = snapshot.quote
        parts.extend([
            f"- Retained price: {q.price} {_md(q.currency)} ({_md(q.kind.value)})",
            f"- Source: {_md(q.provider)} / {_md(q.source_reference)}",
            f"- Market event: {q.event_at.isoformat()}",
            f"- Declared timeliness: {_md(q.timeliness.value)}",
            f"- Freshness when captured: {_md(q.freshness_at_capture.value)}",
            "- Not a current/live market price; replay is offline.",
        ])
    if replay.annual_pe_proxy is not None:
        parts.append(f"- Last-reported-annual P/E proxy: {replay.annual_pe_proxy}")
    else:
        parts.append("- Last-reported-annual P/E proxy: unavailable")
    if replay.scenarios is not None:
        parts.extend(["", "### Hypothetical user-supplied scenarios", ""])
        for item in replay.scenarios.outcomes:
            parts.append(
                f"- {_md(item.name)}: terminal price {item.terminal_price:.6g}; "
                f"cumulative price return {item.total_price_return:.2%}; "
                f"assumption weight {item.probability:.0%}"
            )
    parts.extend(["", "## Limitations and disclosures", ""])
    for warning in replay.warnings:
        parts.append(f"- {_md(warning)}")
    parts.extend([
        "",
        (
            "This is a private research decision record, not investment advice. "
            "A SHA-256 content hash is not independent proof of when the decision was made."
        ),
        "",
    ])
    return "\n".join(parts)


class LocalSnapshotStore:
    """Single-user private directory with create-only, non-overwriting files.

    Uses restrictive POSIX permissions where supported. Not designed as a
    multi-writer transaction database or cloud/multi-tenant authorization layer.
    """

    def __init__(self, directory: Path | str):
        self.root = Path(directory)
        if self.root.is_symlink():
            raise ValueError("snapshot directory may not be a symbolic link")
        self.root.mkdir(mode=0o700, parents=False, exist_ok=True)
        self._check_root()

    def _check_root(self) -> None:
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("snapshot storage must be a real directory")
        if os.name == "posix" and stat.S_IMODE(self.root.stat().st_mode) & 0o077:
            raise PermissionError("snapshot directory must be private (chmod 700)")

    def _path(self, thesis_id: str, revision: int) -> Path:
        return self.root / _name(thesis_id, revision)

    def load(self, thesis_id: str, revision: int) -> ResearchSnapshot:
        self._check_root()
        path = self._path(thesis_id, revision)
        if path.is_symlink():
            raise ValueError("snapshot file must not be a symbolic link")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            status = os.fstat(descriptor)
            if not stat.S_ISREG(status.st_mode) or status.st_size > _MAX_BYTES:
                raise ValueError("snapshot must be a bounded regular file")
            if os.name == "posix" and stat.S_IMODE(status.st_mode) & 0o077:
                raise PermissionError("snapshot file must be private (chmod 600)")
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                raw = handle.read(_MAX_BYTES + 1)
            if len(raw) > _MAX_BYTES:
                raise ValueError("snapshot exceeds size limit")
        finally:
            os.close(descriptor)
        snap = import_snapshot_json(raw.decode("utf-8"))
        if snap.thesis.thesis_id != thesis_id or snap.thesis.revision != revision:
            raise ValueError("snapshot identity does not match filename")
        return snap

    def save(self, snapshot: ResearchSnapshot) -> Path:
        """Explicit append-only save; no overwrite, no provider requests."""
        if not isinstance(snapshot, ResearchSnapshot):
            raise TypeError("save requires ResearchSnapshot")
        self._check_root()
        thesis = snapshot.thesis
        destination = self._path(thesis.thesis_id, thesis.revision)
        replay_snapshot(snapshot)
        history = []
        for revision in range(1, thesis.revision):
            previous = self.load(thesis.thesis_id, revision)
            if (
                previous.issuer != snapshot.issuer
                or previous.thesis.instrument != thesis.instrument
                or previous.saved_at > snapshot.saved_at
            ):
                raise ValueError("research revision issuer or chronology mismatch")
            history.append(previous.thesis)
        # The existing ledger validator starts at revision 1 and verifies
        # every ancestor's SHA-256 link. Checking only the direct predecessor
        # would incorrectly reject all third-and-later revisions.
        validate_thesis_history([*history, thesis])
        data = export_snapshot_json(snapshot).encode("utf-8")
        if len(data) > _MAX_BYTES:
            raise ValueError("snapshot exceeds size limit")
        # Create and fsync a 0600 temporary file in this same private folder,
        # then hard-link into place atomically without allowing replacement.
        fd, temporary = tempfile.mkstemp(prefix=".investiq-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as writer:
                writer.write(data)
                writer.flush()
                os.fsync(writer.fileno())
            os.link(temporary, destination)
            if os.name == "posix":
                folder_fd = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(folder_fd)
                finally:
                    os.close(folder_fd)
        finally:
            os.unlink(temporary)
        return destination
