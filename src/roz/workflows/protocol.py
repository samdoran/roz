"""Protocol module for workflow"""

from typing import Protocol


class WorkflowProtocol(Protocol):
    """Interface that every workflow module must satisfy.

    Each workflow encapsulates all project-specific logic for the three
    release stages. The commands layer dispatches into these methods;
    shared utilities (forge, srpm, git) are called from within.
    """

    def propose(
        self,
        forge_name: str,
        version: str,
        offline: bool,
        yes: bool,
        keep: bool,
        branches: list[str],
        resolves: list[str] | None,
    ) -> None:
        """Stage 1: generate SRPM, import SRPM, open dist-git PRs."""
        ...

    def build(
        self,
        branches: list[str] | None,
    ) -> None:
        """Stage 2: kick off Koji builds for merged PRs."""
        ...

    def update(
        self,
        update_type: str,
        severity: str,
        bugs: list[str] | None,
        branches: list[str] | None,
    ) -> None:
        """Stage 3: create Bodhi updates."""
        ...
