"""CLI entry point for downstream-release."""

import argparse

from roz.commands import build
from roz.commands import propose
from roz.commands import update


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="downstream-release",
        description="Fedora/EPEL release automation for goose.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip diff prompts (passes --skip-diffs to fedpkg import).",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep temporary worktree directories after completion (for debugging).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    propose.register(sub)
    build.register(sub)
    update.register(sub)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.handler(args)
