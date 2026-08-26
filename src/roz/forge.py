"""Forge-agnostic PR operations via ogr."""

import logging

from urllib.parse import urlparse

from ogr.abstract import GitProject
from ogr.abstract import PullRequest
from ogr.factory import get_service_class
from ogr.services.pagure import PagureService

from roz.credentials import get_token


logger = logging.getLogger(__name__)


def _get_service(url: str):
    """Instantiate the appropriate ogr GitService for the given project URL.

    Args:
        url: Full HTTPS URL of the dist-git project.

    Returns:
        An authenticated ogr GitService instance.

    Raises:
        NotImplementedError: For forges not yet supported (e.g. GitLab).
    """
    service_cls = get_service_class(url)
    parsed = urlparse(url)
    instance_url = f"{parsed.scheme}://{parsed.hostname}"

    if issubclass(service_cls, PagureService):
        token = get_token("pagure")
        return PagureService(token=token, instance_url=instance_url)

    # GitLab — planned, not yet implemented
    raise NotImplementedError(
        f"No service implementation for {service_cls.__name__!r}. GitLab support is not yet implemented."
    )


def get_project(url: str) -> GitProject:
    """Return the GitProject for the given forge URL.

    Supports Pagure today; GitLab is a planned extension.

    Args:
        url: Full HTTPS URL of the dist-git project,
            e.g. ``'https://src.fedoraproject.org/rpms/goose'``.

    Returns:
        A :class:`~ogr.abstract.GitProject` ready for API operations.
    """
    service = _get_service(url)
    return service.get_project_from_url(url)


def get_fork_push_url(project: GitProject) -> str:
    """Get or create the user's fork and return its SSH push URL.

    Creates the fork automatically if it does not yet exist.

    Args:
        project: The upstream dist-git project.

    Returns:
        SSH URL of the user's fork, suitable for ``git push``.
    """
    fork = project.get_fork(create=True)
    if fork is None:
        raise RuntimeError(f"Could not get or create a fork for {project.full_repo_name!r}.")
    urls = fork.get_git_urls()
    return urls.get("ssh") or urls["git"]


def get_fork_username(project: GitProject) -> str | None:
    """Return the authenticated username for fork-based forges, or ``None``.

    On Pagure, PRs originate from a personal fork, so the fork owner's
    username must be supplied to :func:`open_pr`. On direct-push forges
    (e.g. GitLab) no fork username is needed, and this returns ``None``.

    Args:
        project: An ogr GitProject, as returned by :func:`get_project`.

    Returns:
        Username string for fork-based forges, ``None`` otherwise.
    """
    if isinstance(project.service, PagureService):
        return project.service.user.get_username()
    return None


def open_pr(
    project: GitProject,
    title: str,
    body: str,
    target_branch: str,
    source_branch: str,
    fork_username: str | None = None,
) -> PullRequest:
    """Open a pull request on any supported forge.

    Args:
        project: Target dist-git project.
        title: PR title.
        body: PR description body.
        target_branch: Branch to merge into (e.g. ``'rawhide'``).
        source_branch: Branch containing the changes
            (e.g. ``'downstream-release/1.2.3/rawhide'``).
        fork_username: Owner of the source fork. Required for Pagure;
            pass ``None`` for direct-push forges such as GitLab.

    Returns:
        The newly created :class:`~ogr.abstract.PullRequest`.
    """
    pr = project.create_pr(
        title=title,
        body=body,
        target_branch=target_branch,
        source_branch=source_branch,
        fork_username=fork_username,
    )
    logger.info("Opened PR #%d: %s", pr.id, pr.url)
    return pr
