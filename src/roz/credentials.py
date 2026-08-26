"""Token resolution for downstream-release forges."""

import os

import keyring


KEYRING_SERVICE = "downstream-release"


def get_token(forge: str) -> str:
    """Resolve the auth token for the given forge name.

    Lookup order:
    1. System keyring  (keyring set downstream-release <forge>)
    2. Environment variable  (<FORGE>_TOKEN)

    Args:
        forge: Forge identifier, e.g. ``'pagure'`` or ``'gitlab'``.

    Returns:
        The auth token string.

    Raises:
        RuntimeError: When no token is found in either location.
    """
    token = keyring.get_password(KEYRING_SERVICE, forge)
    if token:
        return token

    env_key = f"{forge.upper()}_TOKEN"
    token = os.environ.get(env_key)
    if token:
        return token

    raise RuntimeError(
        f"No token found for forge {forge!r}.\n"
        f"Store it in the system keyring:  keyring set {KEYRING_SERVICE} {forge}\n"
        f"Or export the environment variable:  {env_key}=<token>"
    )
