import pytest

from meta_ads_mcp import client


def test_ad_account_id_adds_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "47599739")
    assert client.ad_account_id() == "act_47599739"


def test_ad_account_id_keeps_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "act_47599739")
    assert client.ad_account_id() == "act_47599739"


def test_missing_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    with pytest.raises(client.MetaConfigError):
        client.access_token()


def test_get_attaches_token_and_uses_versioned_base(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/campaigns?access_token=test-token&limit=10",
        json={"data": [{"id": "1", "name": "Test"}]},
    )
    result = client.get("act_123/campaigns", {"limit": 10})
    assert result == {"data": [{"id": "1", "name": "Test"}]}


def test_post_raises_meta_api_error_on_400(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/ads",
        status_code=400,
        json={"error": {"message": "bad creative"}},
    )
    with pytest.raises(client.MetaAPIError) as excinfo:
        client.post("act_123/ads", data={"name": "X"})
    assert excinfo.value.status_code == 400
    assert "bad creative" in str(excinfo.value)


def test_paginate_follows_next_link(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/campaigns?access_token=test-token",
        json={
            "data": [{"id": "1"}],
            "paging": {"next": "https://graph.facebook.com/v21.0/page2?access_token=test-token"},
        },
    )
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/page2?access_token=test-token",
        json={"data": [{"id": "2"}]},
    )
    items = client.paginate("act_123/campaigns")
    assert [i["id"] for i in items] == ["1", "2"]


def test_paginate_respects_limit(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/campaigns?access_token=test-token",
        json={
            "data": [{"id": "1"}, {"id": "2"}, {"id": "3"}],
            "paging": {"next": "https://graph.facebook.com/v21.0/page2?access_token=test-token"},
        },
    )
    items = client.paginate("act_123/campaigns", limit=2)
    assert [i["id"] for i in items] == ["1", "2"]


def test_post_strips_none_values(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/ads",
        json={"id": "ad_1"},
    )
    client.post("act_123/ads", data={"name": "X", "daily_budget": None})
    request = httpx_mock.get_requests()[-1]
    body = request.content.decode()
    assert "daily_budget" not in body
    assert "name=X" in body
