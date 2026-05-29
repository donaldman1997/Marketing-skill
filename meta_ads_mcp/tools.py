"""Tool implementations exposed via the MCP server.

Each function here is registered as an MCP tool in `server.py`. Functions return
plain dicts/lists that serialize cleanly over the MCP wire format.
"""

from __future__ import annotations

import json
from typing import Any

from meta_ads_mcp import client

DEFAULT_INSIGHT_FIELDS = [
    "spend",
    "impressions",
    "reach",
    "clicks",
    "ctr",
    "cpc",
    "cpm",
    "actions",
    "cost_per_action_type",
    "frequency",
]


# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


def list_campaigns(status: str | None = None, limit: int = 50) -> list[dict]:
    """List campaigns in the configured ad account.

    Args:
        status: Optional effective status filter, e.g. "ACTIVE", "PAUSED".
        limit: Max number of campaigns to return.
    """
    params: dict[str, Any] = {
        "fields": (
            "id,name,objective,status,effective_status,buying_type,"
            "daily_budget,lifetime_budget,created_time,start_time,stop_time"
        ),
        "limit": min(limit, 100),
    }
    if status:
        params["effective_status"] = json.dumps([status.upper()])
    return client.paginate(f"{client.ad_account_id()}/campaigns", params, limit=limit)


def find_campaign_by_name(name: str) -> list[dict]:
    """Find campaigns whose name contains the given substring (case-insensitive)."""
    needle = name.lower().strip()
    all_campaigns = list_campaigns(limit=200)
    return [c for c in all_campaigns if needle in c.get("name", "").lower()]


def list_ad_sets(
    campaign_id: str,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List ad sets within a campaign."""
    params: dict[str, Any] = {
        "fields": (
            "id,name,campaign_id,status,effective_status,"
            "daily_budget,lifetime_budget,billing_event,optimization_goal,"
            "targeting,start_time,end_time"
        ),
        "limit": min(limit, 100),
    }
    if status:
        params["effective_status"] = json.dumps([status.upper()])
    return client.paginate(f"{campaign_id}/adsets", params, limit=limit)


def list_ads(
    adset_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List ads. Provide either adset_id, campaign_id, or neither (account-level)."""
    if adset_id and campaign_id:
        raise ValueError("Pass adset_id OR campaign_id, not both.")
    parent = adset_id or campaign_id or client.ad_account_id()
    params: dict[str, Any] = {
        "fields": "id,name,adset_id,campaign_id,status,effective_status,creative,created_time",
        "limit": min(limit, 100),
    }
    if status:
        params["effective_status"] = json.dumps([status.upper()])
    return client.paginate(f"{parent}/ads", params, limit=limit)


def get_ad(ad_id: str) -> dict:
    """Return full details for a single ad, including the creative spec."""
    return client.get(
        ad_id,
        {
            "fields": (
                "id,name,adset_id,campaign_id,status,effective_status,"
                "creative{id,name,object_story_spec,asset_feed_spec,image_hash,"
                "object_type,body,title,call_to_action_type,link_url}"
            ),
        },
    )


def get_ad_creative(creative_id: str) -> dict:
    """Return full details for a single ad creative."""
    return client.get(
        creative_id,
        {
            "fields": (
                "id,name,object_story_spec,asset_feed_spec,image_hash,object_type,"
                "body,title,call_to_action_type,link_url,thumbnail_url"
            ),
        },
    )


# ---------------------------------------------------------------------------
# Image upload tools
# ---------------------------------------------------------------------------


def _extract_image_hash(payload: dict) -> dict:
    """Normalize the /adimages response into {name, hash, url}."""
    images = payload.get("images") or {}
    if not images:
        return payload
    name, info = next(iter(images.items()))
    return {"name": name, "hash": info.get("hash"), "url": info.get("url")}


def upload_image_from_url(image_url: str, name: str | None = None) -> dict:
    """Upload an image to the ad account's image library by URL.

    Returns a dict with the image hash that you pass to creative-creation tools.
    """
    data: dict[str, Any] = {"url": image_url}
    if name:
        data["name"] = name
    payload = client.post(f"{client.ad_account_id()}/adimages", data=data)
    return _extract_image_hash(payload)


def upload_image_from_path(file_path: str, name: str | None = None) -> dict:
    """Upload an image to the ad account's image library from a local file path."""
    payload = client.upload_image_multipart(file_path, field_name=name)
    return _extract_image_hash(payload)


# ---------------------------------------------------------------------------
# Creative + ad creation tools
# ---------------------------------------------------------------------------


def _build_link_data(
    image_hash: str,
    message: str,
    headline: str,
    description: str,
    link_url: str,
    call_to_action: str = "SIGN_UP",
) -> dict:
    return {
        "image_hash": image_hash,
        "message": message,
        "name": headline,
        "description": description,
        "link": link_url,
        "call_to_action": {
            "type": call_to_action,
            "value": {"link": link_url},
        },
    }


def create_link_ad_creative(
    name: str,
    image_hash: str,
    message: str,
    headline: str,
    description: str,
    link_url: str,
    call_to_action: str = "SIGN_UP",
) -> dict:
    """Create a single-image link ad creative tied to the configured Page."""
    spec = {
        "page_id": client.page_id(),
        "link_data": _build_link_data(
            image_hash, message, headline, description, link_url, call_to_action
        ),
    }
    return client.post(
        f"{client.ad_account_id()}/adcreatives",
        data={
            "name": name,
            "object_story_spec": json.dumps(spec),
        },
    )


def create_placement_customized_creative(
    name: str,
    message: str,
    headline: str,
    description: str,
    link_url: str,
    feed_image_hash: str,
    story_image_hash: str,
    portrait_image_hash: str | None = None,
    call_to_action: str = "SIGN_UP",
) -> dict:
    """Create a single creative that swaps the image based on placement.

    - feed_image_hash (1:1)      → Facebook & Instagram feed
    - portrait_image_hash (4:5)  → Instagram feed (preferred if provided)
    - story_image_hash (9:16)    → Stories & Reels
    """
    images: list[dict] = [
        {"hash": feed_image_hash, "adlabels": [{"name": "feed"}]},
        {"hash": story_image_hash, "adlabels": [{"name": "story"}]},
    ]
    rules: list[dict] = [
        {
            "image_label": {"name": "feed"},
            "customization_spec": {
                "publisher_platforms": ["facebook", "instagram"],
                "facebook_positions": ["feed"],
                "instagram_positions": ["stream"],
            },
        },
        {
            "image_label": {"name": "story"},
            "customization_spec": {
                "publisher_platforms": ["facebook", "instagram"],
                "facebook_positions": ["story"],
                "instagram_positions": ["story", "reels"],
            },
        },
    ]
    if portrait_image_hash:
        images.append({"hash": portrait_image_hash, "adlabels": [{"name": "portrait"}]})
        # Override Instagram stream with the 4:5 variant — portrait wins where it overlaps.
        rules.insert(
            1,
            {
                "image_label": {"name": "portrait"},
                "customization_spec": {
                    "publisher_platforms": ["instagram"],
                    "instagram_positions": ["stream"],
                },
            },
        )

    asset_feed_spec = {
        "images": images,
        "bodies": [{"text": message}],
        "titles": [{"text": headline}],
        "descriptions": [{"text": description}],
        "link_urls": [{"website_url": link_url}],
        "ad_formats": ["SINGLE_IMAGE"],
        "call_to_action_types": [call_to_action],
        "asset_customization_rules": rules,
    }
    object_story_spec = {"page_id": client.page_id()}

    return client.post(
        f"{client.ad_account_id()}/adcreatives",
        data={
            "name": name,
            "object_story_spec": json.dumps(object_story_spec),
            "asset_feed_spec": json.dumps(asset_feed_spec),
        },
    )


def create_ad(
    adset_id: str,
    ad_name: str,
    creative_id: str,
    status: str = "PAUSED",
) -> dict:
    """Create an ad in the given ad set using an existing creative."""
    return client.post(
        f"{client.ad_account_id()}/ads",
        data={
            "name": ad_name,
            "adset_id": adset_id,
            "status": status.upper(),
            "creative": json.dumps({"creative_id": creative_id}),
        },
    )


def create_single_image_ad(
    adset_id: str,
    ad_name: str,
    primary_text: str,
    headline: str,
    description: str,
    link_url: str,
    image_hash: str,
    call_to_action: str = "SIGN_UP",
    status: str = "PAUSED",
) -> dict:
    """Create a creative + ad in one call. Returns {"creative": ..., "ad": ...}."""
    creative = create_link_ad_creative(
        name=f"{ad_name} — creative",
        image_hash=image_hash,
        message=primary_text,
        headline=headline,
        description=description,
        link_url=link_url,
        call_to_action=call_to_action,
    )
    ad = create_ad(adset_id, ad_name, creative["id"], status)
    return {"creative": creative, "ad": ad}


def create_placement_customized_ad(
    adset_id: str,
    ad_name: str,
    primary_text: str,
    headline: str,
    description: str,
    link_url: str,
    feed_image_hash: str,
    story_image_hash: str,
    portrait_image_hash: str | None = None,
    call_to_action: str = "SIGN_UP",
    status: str = "PAUSED",
) -> dict:
    """Create a creative with per-placement images + an ad in one call."""
    creative = create_placement_customized_creative(
        name=f"{ad_name} — creative",
        message=primary_text,
        headline=headline,
        description=description,
        link_url=link_url,
        feed_image_hash=feed_image_hash,
        story_image_hash=story_image_hash,
        portrait_image_hash=portrait_image_hash,
        call_to_action=call_to_action,
    )
    ad = create_ad(adset_id, ad_name, creative["id"], status)
    return {"creative": creative, "ad": ad}


# ---------------------------------------------------------------------------
# Management tools
# ---------------------------------------------------------------------------


def create_campaign(
    name: str,
    objective: str,
    status: str = "PAUSED",
    special_ad_categories: list[str] | None = None,
    buying_type: str = "AUCTION",
    daily_budget_cents: int | None = None,
    lifetime_budget_cents: int | None = None,
) -> dict:
    """Create a new campaign.

    Objective is one of the OUTCOME_* values:
      OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT,
      OUTCOME_LEADS, OUTCOME_APP_PROMOTION, OUTCOME_SALES.

    Budgets are in the account's currency, in minor units (cents/pence).
    """
    data: dict[str, Any] = {
        "name": name,
        "objective": objective.upper(),
        "status": status.upper(),
        "buying_type": buying_type.upper(),
        "special_ad_categories": json.dumps(special_ad_categories or []),
    }
    if daily_budget_cents is not None:
        data["daily_budget"] = daily_budget_cents
    if lifetime_budget_cents is not None:
        data["lifetime_budget"] = lifetime_budget_cents
    return client.post(f"{client.ad_account_id()}/campaigns", data=data)


def _set_status(node_id: str, status: str) -> dict:
    return client.post(node_id, data={"status": status.upper()})


def pause_campaign(campaign_id: str) -> dict:
    return _set_status(campaign_id, "PAUSED")


def resume_campaign(campaign_id: str) -> dict:
    return _set_status(campaign_id, "ACTIVE")


def pause_ad_set(adset_id: str) -> dict:
    return _set_status(adset_id, "PAUSED")


def resume_ad_set(adset_id: str) -> dict:
    return _set_status(adset_id, "ACTIVE")


def pause_ad(ad_id: str) -> dict:
    return _set_status(ad_id, "PAUSED")


def resume_ad(ad_id: str) -> dict:
    return _set_status(ad_id, "ACTIVE")


def duplicate_ad(
    source_ad_id: str,
    target_adset_id: str | None = None,
    rename_suffix: str = " — copy",
    status_option: str = "PAUSED",
) -> dict:
    """Duplicate an ad via the /copies endpoint, optionally into a different ad set."""
    data: dict[str, Any] = {
        "status_option": status_option.upper(),
        "rename_options": json.dumps({"rename_suffix": rename_suffix}),
    }
    if target_adset_id:
        data["adset_id"] = target_adset_id
    return client.post(f"{source_ad_id}/copies", data=data)


def duplicate_ad_set(
    source_adset_id: str,
    target_campaign_id: str | None = None,
    rename_suffix: str = " — copy",
    deep_copy: bool = True,
    status_option: str = "PAUSED",
) -> dict:
    """Duplicate an ad set, optionally into a different campaign and including ads."""
    data: dict[str, Any] = {
        "deep_copy": deep_copy,
        "status_option": status_option.upper(),
        "rename_options": json.dumps({"rename_suffix": rename_suffix}),
    }
    if target_campaign_id:
        data["campaign_id"] = target_campaign_id
    return client.post(f"{source_adset_id}/copies", data=data)


def duplicate_campaign(
    source_campaign_id: str,
    rename_suffix: str = " — copy",
    deep_copy: bool = True,
    status_option: str = "PAUSED",
) -> dict:
    """Duplicate a campaign (with ad sets and ads if deep_copy=True)."""
    data: dict[str, Any] = {
        "deep_copy": deep_copy,
        "status_option": status_option.upper(),
        "rename_options": json.dumps({"rename_suffix": rename_suffix}),
    }
    return client.post(f"{source_campaign_id}/copies", data=data)


# ---------------------------------------------------------------------------
# Insights / reporting tools
# ---------------------------------------------------------------------------


def _insights(
    object_id: str,
    date_preset: str,
    fields: list[str] | None,
    breakdowns: list[str] | None,
    time_increment: str | None,
) -> list[dict]:
    params: dict[str, Any] = {
        "fields": ",".join(fields or DEFAULT_INSIGHT_FIELDS),
        "date_preset": date_preset,
    }
    if breakdowns:
        params["breakdowns"] = ",".join(breakdowns)
    if time_increment:
        params["time_increment"] = time_increment
    return client.paginate(f"{object_id}/insights", params)


def get_campaign_insights(
    campaign_id: str,
    date_preset: str = "last_7d",
    fields: list[str] | None = None,
    breakdowns: list[str] | None = None,
    time_increment: str | None = None,
) -> list[dict]:
    """Return insights for a campaign. date_preset examples: today, yesterday,
    last_7d, last_14d, last_30d, this_month, last_month, maximum."""
    return _insights(campaign_id, date_preset, fields, breakdowns, time_increment)


def get_ad_set_insights(
    adset_id: str,
    date_preset: str = "last_7d",
    fields: list[str] | None = None,
    breakdowns: list[str] | None = None,
    time_increment: str | None = None,
) -> list[dict]:
    return _insights(adset_id, date_preset, fields, breakdowns, time_increment)


def get_ad_insights(
    ad_id: str,
    date_preset: str = "last_7d",
    fields: list[str] | None = None,
    breakdowns: list[str] | None = None,
    time_increment: str | None = None,
) -> list[dict]:
    return _insights(ad_id, date_preset, fields, breakdowns, time_increment)


def get_account_insights(
    date_preset: str = "last_7d",
    fields: list[str] | None = None,
    breakdowns: list[str] | None = None,
    time_increment: str | None = None,
) -> list[dict]:
    """Account-level rollup of spend, impressions, clicks, etc."""
    return _insights(client.ad_account_id(), date_preset, fields, breakdowns, time_increment)
