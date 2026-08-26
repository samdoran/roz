"""Goose workflow: Fedora/EPEL release automation for goose."""

import subprocess

from pathlib import Path

from roz import forge
from roz import git
from roz import srpm
from roz.workflows.protocol import WorkflowProtocol


def _generate_vendor_tarball(repo_dir: Path) -> None:
    """Run a make target in the given directory.

    Args:
        repo_dir: Path to the directory containing the Makefile.
    """
    subprocess.run(
        ["/usr/bin/make", "vendor-tarball"],
        cwd=repo_dir,
        check=True,
    )


COMMIT_MESSAGE = "Rebase for goose {version}"
RELEASE_TOOL_URL = "https://github.com/rhel-lightspeed/roz"

DIST_GIT_BRANCHES = {
    "pagure": ["rawhide", "f44", "f43", "epel9", "epel10", "epel10.2"],
    "gitlab": ["ext-rhel-10.2", "ext-rhel-9.8"],
}

UPSTREAM_REPO_URL = "git@github.com:rhel-lightspeed/goose.git"

DIST_GIT_URLS = {
    "pagure": "https://src.fedoraproject.org/rpms/goose",
    "gitlab": "https://gitlab.com/redhat/rhel/rpms/goose",
}


class GooseWorkflow(WorkflowProtocol):
    """Release workflow for the goose project."""

    def propose(
        self,
        forge_name: str,
        version: str,
        offline: bool = False,
        yes: bool = False,
        keep: bool = False,
        branches: list[str] = DIST_GIT_BRANCHES["pagure"],
        resolves: list[str] | None = None,
    ) -> None:
        """Clone upstream, build an SRPM, and open dist-git PRs for each target branch.

        Clones the goose upstream repository, generates a vendor tarball, and
        builds an SRPM. Then, for each target branch, imports the SRPM into the
        dist-git worktree, commits, pushes to the user's fork, and opens a pull
        request against the upstream dist-git project.

        Args:
            forge_name: Key into :attr:`DIST_GIT_URLS` / :attr:`DIST_GIT_BRANCHES`
                (e.g. ``'pagure'`` or ``'gitlab'``).
            version: Upstream version string being released (e.g. ``'1.2.3'``).
            offline: When ``True``, skip the lookaside-cache tarball upload during
                ``fedpkg import`` (useful for air-gapped or test environments).
            yes: When ``True``, pass ``--skip-diffs`` to ``fedpkg import``,
                suppressing interactive diff prompts.
            keep: When ``True``, preserve temporary clone directories after the
                run completes (useful for post-mortem debugging).
            branches: Dist-git branches to target. Defaults to all branches
                defined for *forge_name* in :attr:`DIST_GIT_BRANCHES`. Raises
                :exc:`SystemExit` if any unknown branch is supplied.
            resolves: Bug or ticket identifiers to append as ``Resolve: <id>``
                trailers in the commit message (e.g. ``['rhbz#12345', 'RSPEED-12345']``).
        """
        with git.clone(UPSTREAM_REPO_URL, branch="main", keep=keep) as upstream_dir:
            _generate_vendor_tarball(upstream_dir)
            srpm_path = srpm.generate_srpm(upstream_dir)

        self._open_pull_request(branches, version, forge_name, srpm_path, keep, offline, yes, resolves)

    def _open_pull_request(
        self,
        branches: list[str],
        version: str,
        forge_name: str,
        srpm_path: Path,
        keep: bool = False,
        offline: bool = False,
        yes: bool = False,
        resolves: list[str] | None = None,
    ):
        """Import an SRPM into dist-git and open a pull request for each branch.

        For each target branch, checks out the branch in the dist-git clone,
        creates a ``roz/<version>/<branch>`` source branch, imports the SRPM,
        commits, pushes to the user's fork, and opens a pull request against
        the upstream dist-git project. Prints the PR URL for each branch on
        success.

        Args:
            branches: Dist-git branches to process (already validated by the
                caller).
            version: Upstream version string being released (e.g. ``'1.2.3'``).
            forge_name: Key into :attr:`DIST_GIT_URLS` selecting the target
                forge (e.g. ``'pagure'`` or ``'gitlab'``).
            srpm_path: Filesystem path to the pre-built ``.src.rpm`` file.
            keep: When ``True``, preserve the temporary dist-git clone directory
                after the run completes (useful for debugging).
            offline: When ``True``, skip the lookaside-cache tarball upload
                during ``fedpkg import``.
            yes: When ``True``, pass ``--skip-diffs`` to ``fedpkg import``,
                suppressing interactive diff prompts.
            resolves: Bug or ticket identifiers to append as ``Resolve: <id>``
                trailers in the commit message.
        """
        commit_message = COMMIT_MESSAGE.format(version=version)
        # Build commit message, appending `Resolve:` trailers when provided.
        if resolves:
            trailers = "\n".join(f"Resolve: {ticket}" for ticket in resolves)
            commit_message = f"{commit_message}\n\n{trailers}"

        url = DIST_GIT_URLS[forge_name]
        project = forge.get_project(url)
        fork_push_url = forge.get_fork_push_url(project)
        fork_username = forge.get_fork_username(project)

        # We use branches[0] as a way to clone a valid branch for the project, being either the one specified in
        # `--branches <branch>`, or one of the valid set of branches for the forge.
        #
        # We also use shallow=False because we need to push a new commit for the desired branches after
        # we are done importing the srpm contents.
        with git.clone(url, branch=branches[0], single_branch=False, shallow=False, keep=keep) as distgit_dir:
            for branch in branches:
                source_branch = f"roz/{version}/{branch}"

                git.checkout(distgit_dir, branch)
                git.create_branch(distgit_dir, source_branch)
                srpm.import_srpm(distgit_dir, srpm_path, offline=offline, skip_diffs=yes)
                git.commit(distgit_dir, commit_message)
                git.push(distgit_dir, fork_push_url, source_branch)

                pr = forge.open_pr(
                    project=project,
                    title=f"Release {project.repo} {version} for {branch}",
                    body=(
                        f"Automated downstream release of goose {version}.\n\nGenerated by [roz]({{RELEASE_TOOL_URL}})"
                    ),
                    target_branch=branch,
                    source_branch=source_branch,
                    fork_username=fork_username,
                )
                if pr:
                    print(f"[{branch}] PR #{pr.id}: {pr.url}")

    def build(
        self,
        branches: list[str] | None,
    ) -> None:
        """Stage 2: kick off Koji builds for merged PRs."""
        raise NotImplementedError("build stage is not yet implemented for goose.")

    def update(
        self,
        update_type: str,
        severity: str,
        bugs: list[str] | None,
        branches: list[str] | None,
    ) -> None:
        """Stage 3: create Bodhi updates."""
        raise NotImplementedError("update stage is not yet implemented for goose.")
