import json
import re
from urllib.parse import parse_qs

import pytest

from meta_ads_mcp import tools


def _form(httpx_mock) -> dict:
    req = httpx_mock.get_requests()[-1]
    parsed = parse_qs(req.content.decode())
    return {k: v[0] for k, v in parsed.items()}


_CAMPAIGNS_URL_RE = re.compile(r"https://graph\.facebook\.com/v21\.0/act_123/campaigns\?.*")
_INSIGHTS_URL_RE = re.compile(r"https://graph\.facebook\.com/v21\.0/act_123/insights\?.*")


def test_list_campaigns_uses_account_path(httpx_mock) -> None:
    httpx_mock.add_response(
        url=_CAMPAIGNS_URL_RE,
        json={"data": [{"id": "c1", "name": "MTLS"}]},
    )
    result = tools.list_campaigns(limit=10)
    assert result == [{"id": "c1", "name": "MTLS"}]


def test_find_campaign_by_name_matches_case_insensitive(httpx_mock) -> None:
    httpx_mock.add_response(
        url=_CAMPAIGNS_URL_RE,
        json={
            "data": [
                {"id": "c1", "name": "More Time Less Stress"},
                {"id": "c2", "name": "Other Campaign"},
            ]
        },
    )
    result = tools.find_campaign_by_name("more time")
    assert [c["id"] for c in result] == ["c1"]


def test_upload_image_from_url_extracts_hash(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/adimages",
        json={"images": {"square": {"hash": "abc123", "url": "https://cdn/.../sq.png"}}},
    )
    result = tools.upload_image_from_url("https://cdn/.../sq.png", name="square")
    assert result == {"name": "square", "hash": "abc123", "url": "https://cdn/.../sq.png"}


def test_create_link_ad_creative_posts_object_story_spec(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/adcreatives",
        json={"id": "creative_1"},
    )
    tools.create_link_ad_creative(
        name="Test creative",
        image_hash="HASH",
        message="primary text",
        headline="Headline",
        description="Description",
        link_url="https://example.com",
    )
    body = _form(httpx_mock)
    assert body["name"] == "Test creative"
    spec = json.loads(body["object_story_spec"])
    assert spec["page_id"] == "999"
    link = spec["link_data"]
    assert link["image_hash"] == "HASH"
    assert link["message"] == "primary text"
    assert link["name"] == "Headline"
    assert link["description"] == "Description"
    assert link["link"] == "https://example.com"
    assert link["call_to_action"]["type"] == "SIGN_UP"
    assert link["call_to_action"]["value"]["link"] == "https://example.com"


def test_create_placement_customized_creative_includes_all_three_images(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/adcreatives",
        json={"id": "creative_2"},
    )
    tools.create_placement_customized_creative(
        name="Multi-placement creative",
        message="msg",
        headline="head",
        description="desc",
        link_url="https://example.com",
        feed_image_hash="FEED",
        story_image_hash="STORY",
        portrait_image_hash="PORTRAIT",
    )
    body = _form(httpx_mock)
    afs = json.loads(body["asset_feed_spec"])
    hashes = {img["hash"] for img in afs["images"]}
    assert hashes == {"FEED", "STORY", "PORTRAIT"}
    labels = {img["adlabels"][0]["name"] for img in afs["images"]}
    assert labels == {"feed", "story", "portrait"}
    assert afs["bodies"] == [{"text": "msg"}]
    assert afs["titles"] == [{"text": "head"}]
    assert afs["call_to_action_types"] == ["SIGN_UP"]


def test_create_placement_customized_creative_omits_portrait_when_none(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/adcreatives",
        json={"id": "creative_3"},
    )
    tools.create_placement_customized_creative(
        name="Two-placement",
        message="msg",
        headline="head",
        description="desc",
        link_url="https://example.com",
        feed_image_hash="FEED",
        story_image_hash="STORY",
    )
    body = _form(httpx_mock)
    afs = json.loads(body["asset_feed_spec"])
    labels = {img["adlabels"][0]["name"] for img in afs["images"]}
    assert labels == {"feed", "story"}


def test_create_ad_defaults_to_paused(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/ads",
        json={"id": "ad_1"},
    )
    tools.create_ad(adset_id="as_1", ad_name="ad", creative_id="cr_1")
    body = _form(httpx_mock)
    assert body["status"] == "PAUSED"
    assert body["adset_id"] == "as_1"
    assert json.loads(body["creative"]) == {"creative_id": "cr_1"}


def test_pause_ad_set_posts_status(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/as_1",
        json={"success": True},
    )
    tools.pause_ad_set("as_1")
    body = _form(httpx_mock)
    assert body["status"] == "PAUSED"


def test_duplicate_ad_targets_other_adset(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/ad_42/copies",
        json={"copied_ad_id": "ad_99"},
    )
    tools.duplicate_ad(source_ad_id="ad_42", target_adset_id="as_2")
    body = _form(httpx_mock)
    assert body["adset_id"] == "as_2"
    assert body["status_option"] == "PAUSED"
    assert json.loads(body["rename_options"])["rename_suffix"] == " — copy"


def test_create_campaign_serializes_special_ad_categories(httpx_mock) -> None:
    httpx_mock.add_response(
        url="https://graph.facebook.com/v21.0/act_123/campaigns",
        json={"id": "c_new"},
    )
    tools.create_campaign(
        name="Test",
        objective="OUTCOME_LEADS",
        daily_budget_cents=5000,
    )
    body = _form(httpx_mock)
    assert body["objective"] == "OUTCOME_LEADS"
    assert body["status"] == "PAUSED"
    assert body["buying_type"] == "AUCTION"
    assert json.loads(body["special_ad_categories"]) == []
    assert body["daily_budget"] == "5000"


def test_get_account_insights_defaults_fields(httpx_mock) -> None:
    httpx_mock.add_response(
        url=_INSIGHTS_URL_RE,
        json={"data": [{"spend": "10.00"}]},
    )
    result = tools.get_account_insights()
    assert result == [{"spend": "10.00"}]
    req = httpx_mock.get_requests()[-1]
    assert "date_preset=last_7d" in str(req.url)
    assert "spend" in str(req.url)


def test_list_ads_rejects_both_filters() -> None:
    with pytest.raises(ValueError):
        tools.list_ads(adset_id="as_1", campaign_id="c_1")
