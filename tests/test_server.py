from meta_ads_mcp import server

EXPECTED_TOOLS = {
    "list_campaigns",
    "find_campaign_by_name",
    "list_ad_sets",
    "list_ads",
    "get_ad",
    "get_ad_creative",
    "upload_image_from_url",
    "upload_image_from_path",
    "create_link_ad_creative",
    "create_placement_customized_creative",
    "create_ad",
    "create_single_image_ad",
    "create_placement_customized_ad",
    "create_campaign",
    "pause_campaign",
    "resume_campaign",
    "pause_ad_set",
    "resume_ad_set",
    "pause_ad",
    "resume_ad",
    "duplicate_ad",
    "duplicate_ad_set",
    "duplicate_campaign",
    "get_campaign_insights",
    "get_ad_set_insights",
    "get_ad_insights",
    "get_account_insights",
}


def test_server_registers_all_tools() -> None:
    """Smoke test that FastMCP accepted every tool registration."""
    import asyncio

    registered = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in registered}
    missing = EXPECTED_TOOLS - names
    assert not missing, f"Missing tool registrations: {missing}"
