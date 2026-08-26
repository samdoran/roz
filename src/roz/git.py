"""Git operations for downstream-release."""

import subprocess
import tempfile

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


GIT_BIN = "/usr/bin/git"


@contextmanager
def clone(
    repo_url: str,
    branch: str = "main",
    single_branch: bool = True,
    shallow: bool = True,
    keep: bool = False,
) -> Generator[Path]:
    """Clone a repo into a temporary directory and yield its path.

    The temporary directory — and everything in it — is cleaned up
    when the context manager exits, unless *keep* is ``True``.

    Args:
        repo_url: URL of the repository to clone.
        branch: Branch to clone. Defaults to ``"main"``.
        single_branch: When ``True`` (default), passes ``--single-branch``
            to clone only the specified branch. Set to ``False`` to fetch
            all remote branches (needed when checking out multiple branches
            from the same clone, e.g. dist-git).
        shallow: When ``True`` (default), passes ``--depth 1`` to create a
            shallow clone. Set to ``False`` for a full clone — required when
            the clone will be used as a push source, since git does not allow
            pushing from a shallow repository.
        keep: When ``True``, the temporary directory is not deleted on exit
            and its path is printed so it can be inspected for debugging.
    """
    with tempfile.TemporaryDirectory(prefix="downstream-release-", delete=not keep) as tmpdir:
        repo_dir = Path(tmpdir) / "repo"

        cmd = [GIT_BIN, "clone"]
        if shallow:
            cmd += ["--depth", "1"]
        if single_branch:
            cmd += ["--branch", branch]
        else:
            cmd += ["--no-single-branch", "--branch", branch]
        cmd += [repo_url, str(repo_dir)]

        subprocess.run(cmd, cwd=repo_dir.parent, check=True)  # noqa: S603

        if keep:
            print(f"[keep] Worktree preserved at: {tmpdir}")

        yield repo_dir


def checkout(repo_dir: Path, branch: str) -> None:
    """Check out a branch in an existing local repository.

    Args:
        repo_dir: Path to the local git repository.
        branch: Name of the remote branch to check out locally.
    """
    subprocess.run(  # noqa: S603
        [GIT_BIN, "checkout", branch],
        cwd=repo_dir,
        check=True,
    )


def create_branch(repo_dir: Path, branch: str) -> None:
    """Create and switch to a new branch from the current HEAD.

    Args:
        repo_dir: Path to the local git repository.
        branch: Name of the new branch to create
            (e.g. ``"downstream-release/1.2.3/rawhide"``).
    """
    subprocess.run(  # noqa: S603
        [GIT_BIN, "checkout", "-b", branch],
        cwd=repo_dir,
        check=True,
    )


def commit(repo_dir: Path, message: str) -> None:
    """Stage all changes and create a commit.

    Args:
        repo_dir: Path to the local git repository.
        message: Commit message.
    """
    subprocess.run(  # noqa: S603
        [GIT_BIN, "add", "-A"],
        cwd=repo_dir,
        check=True,
    )
    subprocess.run(  # noqa: S603
        [GIT_BIN, "commit", "-m", message],
        cwd=repo_dir,
        check=True,
    )


def push(repo_dir: Path, fork_url: str, source_branch: str) -> None:
    """Push the current HEAD to a branch on a remote fork.

    Args:
        repo_dir: Path to the local git repository.
        fork_url: URL of the fork to push to.
        source_branch: Remote branch name to push to
            (e.g. ``"downstream-release/1.2.3/rawhide"``).
    """
    subprocess.run(  # noqa: S603
        [GIT_BIN, "push", fork_url, f"HEAD:{source_branch}"],
        cwd=repo_dir,
        check=True,
    )
