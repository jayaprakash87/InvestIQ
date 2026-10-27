"""InvestIQ CLI: offline demo/replay and explicit BYOK connected issuer research."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .connected_cli import replay, run_research
from .ports import ProviderFailure
from .workflow import build_synthetic_bundle, validate_bundle


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False, sort_keys=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investiq",
        description="Evidence-aware research: offline examples/replay; optional BYOK connected access.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Create and validate a fictional research bundle")
    demo.add_argument("--output", type=Path, help="Write the synthetic bundle as JSON")

    check = commands.add_parser("validate", help="Validate an offline research bundle")
    check.add_argument("file", type=Path, help="Local JSON bundle")
    check.add_argument(
        "--basis", choices=("public", "recorded"), default="public",
        help="Publicly available or actually recorded at the historical cutoff",
    )
    connected = commands.add_parser(
        "research",
        help="Fetch one issuer's annual SEC facts and BYOK quote (network, explicit consent)",
    )
    connected.add_argument("--symbol", required=True, help="Exact provider-listed ticker")
    connected.add_argument("--venue", required=True, help="Exchange ISO MIC, e.g. XNAS")
    connected.add_argument("--currency", required=True, help="Quote currency, e.g. USD")
    connected.add_argument("--cik", required=True, help="Known SEC CIK, not inferred from ticker")
    connected.add_argument(
        "--listing-source", required=True,
        help="Researcher's independently checked issuer-to-listing reference",
    )
    connected.add_argument(
        "--listing-from", required=True, help="Effective date YYYY-MM-DD for that mapping",
    )
    connected.add_argument(
        "--max-age-minutes", required=True, type=int,
        help="User-chosen maximum age of quote's market event (1..1440); not feed entitlement",
    )
    connected.add_argument(
        "--confirm-share-basis", action="store_true",
        help="Assert EPS/share class and price split basis were independently checked",
    )
    connected.add_argument(
        "--basis-rationale", help="Why the annual EPS and quote share basis are comparable",
    )
    connected.add_argument("--save-dir", type=Path, help="EXPLICIT private decision save")
    connected.add_argument("--thesis-id", help="Safe local thesis ID, used only with --save-dir")
    connected.add_argument("--thesis-statement", help="Researcher's authored thesis")
    connected.add_argument("--revision-reason", help="Reason for recording the decision")
    connected.add_argument("--revision", type=int, default=1, help="Thesis revision (default 1)")
    connected.add_argument(
        "--stage", choices=("researching", "watching", "challenged", "archived"),
        help="Saved thesis stage; requires --save-dir",
    )

    historical = commands.add_parser(
        "replay", help="Reproduce a private saved research decision OFFLINE, without API keys"
    )
    historical.add_argument("--store-dir", type=Path, required=True)
    historical.add_argument("--thesis-id", required=True)
    historical.add_argument("--revision", required=True, type=int)
    historical.add_argument(
        "--format", choices=("summary", "markdown", "manifest"), default="summary"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "demo":
            bundle = build_synthetic_bundle()
            validate_bundle(bundle, basis="recorded")
            serialized = _json(bundle) + "\n"
            if args.output:
                args.output.write_text(serialized, encoding="utf-8")
                print(f"Created synthetic research bundle: {args.output}")
            else:
                print(serialized, end="")
        elif args.command == "research":
            print(_json(run_research(args)))
        elif args.command == "replay":
            print(replay(args.store_dir, args.thesis_id, args.revision, format=args.format), end="")
        else:
            data = json.loads(args.file.read_text(encoding="utf-8"))
            print(_json(validate_bundle(data, basis=args.basis)))
    except ProviderFailure as exc:
        # Provider errors are sanitized by adapters. Never expose the key or URL.
        print(f"InvestIQ provider error ({exc.code.value}): {exc}", file=sys.stderr)
        return 2
    except (OSError, KeyError, ValueError, TypeError, OverflowError, json.JSONDecodeError) as exc:
        print(f"InvestIQ validation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
