"""MCP server registration. Wires the `tools` module functions to FastMCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from meta_ads_mcp import tools

mcp = FastMCP("meta-ads")

# Read
mcp.tool()(tools.list_campaigns)
mcp.tool()(tools.find_campaign_by_name)
mcp.tool()(tools.list_ad_sets)
mcp.tool()(tools.list_ads)
mcp.tool()(tools.get_ad)
mcp.tool()(tools.get_ad_creative)

# Image upload
mcp.tool()(tools.upload_image_from_url)
mcp.tool()(tools.upload_image_from_path)

# Creative + ad creation
mcp.tool()(tools.create_link_ad_creative)
mcp.tool()(tools.create_placement_customized_creative)
mcp.tool()(tools.create_ad)
mcp.tool()(tools.create_single_image_ad)
mcp.tool()(tools.create_placement_customized_ad)

# Management
mcp.tool()(tools.create_campaign)
mcp.tool()(tools.pause_campaign)
mcp.tool()(tools.resume_campaign)
mcp.tool()(tools.pause_ad_set)
mcp.tool()(tools.resume_ad_set)
mcp.tool()(tools.pause_ad)
mcp.tool()(tools.resume_ad)
mcp.tool()(tools.duplicate_ad)
mcp.tool()(tools.duplicate_ad_set)
mcp.tool()(tools.duplicate_campaign)

# Insights
mcp.tool()(tools.get_campaign_insights)
mcp.tool()(tools.get_ad_set_insights)
mcp.tool()(tools.get_ad_insights)
mcp.tool()(tools.get_account_insights)
