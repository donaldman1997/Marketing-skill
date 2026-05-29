import os

import pytest


@pytest.fixture(autouse=True)
def _meta_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide deterministic Meta credentials for every test."""
    monkeypatch.setenv("META_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "act_123")
    monkeypatch.setenv("META_PAGE_ID", "999")
    monkeypatch.setenv("META_GRAPH_API_VERSION", "v21.0")
    # Belt-and-braces in case dotenv loaded something already.
    for k in ("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_PAGE_ID"):
        assert os.environ[k]
