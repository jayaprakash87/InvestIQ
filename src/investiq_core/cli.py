"""Offline, vendor-independent CLI for the InvestIQ public research toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .workflow import build_synthetic_bundle, validate_bundle


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False, sort_keys=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="investiq",
        description="Offline, evidence-aware investment research (no live prices or advice).",
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
        else:
            data = json.loads(args.file.read_text(encoding="utf-8"))
            print(_json(validate_bundle(data, basis=args.basis)))
    except (OSError, KeyError, ValueError, TypeError, OverflowError) as exc:
        print(f"InvestIQ validation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
