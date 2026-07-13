from __future__ import annotations

import argparse
from pathlib import Path

from repo_detective.agent import DetectiveAgent
from repo_detective.reporters import render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-detective",
        description="Investigate a codebase and produce a prioritized health report.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Repository to investigate")
    parser.add_argument("-o", "--output", type=Path, help="Write the report to a file")
    parser.add_argument("--json", action="store_true", help="Render machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = DetectiveAgent(args.path).run()
    except ValueError as error:
        raise SystemExit(str(error)) from error
    rendered = render_json(report) if args.json else render_markdown(report)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(rendered, end="")
    return 0

