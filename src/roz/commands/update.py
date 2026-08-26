"""Stage 3: create Bodhi updates (skips rawhide)."""

import argparse

from roz.workflows import WORKFLOW_MAP


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "update",
        help="Stage 3: create Bodhi updates (skips rawhide).",
    )
    parser.add_argument(
        "--project",
        choices=list(WORKFLOW_MAP),
        required=True,
        help="Project to update (e.g. goose).",
    )
    parser.add_argument(
        "--type",
        choices=["enhancement", "bugfix", "security"],
        default="enhancement",
        dest="update_type",
        help="Bodhi update type (default: enhancement).",
    )
    parser.add_argument(
        "--bugs",
        action="append",
        help="Related bug IDs. May be repeated.",
    )
    parser.add_argument(
        "--severity",
        choices=["unspecified", "low", "medium", "high", "urgent"],
        default="unspecified",
        help="Bodhi severity (default: unspecified).",
    )
    parser.add_argument(
        "--branch",
        action="append",
        dest="branches",
        metavar="BRANCH",
        help="Limit to specific branch(es). May be repeated. Default: all.",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> None:
    WORKFLOW_MAP[args.project].update(
        update_type=args.update_type,
        severity=args.severity,
        bugs=args.bugs,
        branches=args.branches,
    )
