"""SRPM build and import operations for downstream-release."""

import subprocess

from pathlib import Path


FEDPKG_BIN = "/usr/bin/fedpkg"


def generate_srpm(repo_dir: Path) -> Path:
    """Run fedpkg srpm in an already-cloned upstream repo and return the SRPM path."""
    subprocess.run(  # noqa: S603
        [FEDPKG_BIN, "srpm"],
        cwd=repo_dir,
        check=True,
    )

    srpms = list(repo_dir.glob("*.src.rpm"))
    if not srpms:
        msg = f"No .src.rpm found in {repo_dir} after fedpkg srpm"
        raise FileNotFoundError(msg)

    return srpms[0]


def import_srpm(
    repo_dir: Path,
    srpm_path: Path,
    offline: bool = False,
    skip_diffs: bool = False,
) -> None:
    """Import an SRPM into an already-cloned dist-git checkout.

    Runs ``fedpkg import`` which unpacks the SRPM and stages all changes
    in the working tree, ready for a subsequent commit.

    Args:
        repo_dir: Path to the dist-git repository checkout.
        srpm_path: Absolute path to the ``.src.rpm`` file to import.
        offline: When ``True``, passes ``--offline`` to skip uploading
            the tarball to the lookaside cache. Useful for local testing.
        skip_diffs: When ``True``, passes ``--skip-diffs`` to suppress
            interactive diff prompts during import.
    """
    cmd = [FEDPKG_BIN, "import"]
    if offline:
        cmd.append("--offline")
    if skip_diffs:
        cmd.append("--skip-diffs")
    cmd.append(str(srpm_path))

    subprocess.run(cmd, cwd=repo_dir, check=True)  # noqa: S603
