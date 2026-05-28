# Meta Ads MCP

An MCP server that lets Claude (or any MCP-compatible client) manage your Meta
(Facebook + Instagram) Ads — list campaigns, upload creatives, create ads,
pause/duplicate, and pull insights — through the official Meta Marketing API.

Built specifically so an AI assistant can drop creatives into an existing
campaign without you having to click through Ads Manager.

## What it can do

| Category | Tools |
|----------|-------|
| **Read** | `list_campaigns`, `find_campaign_by_name`, `list_ad_sets`, `list_ads`, `get_ad`, `get_ad_creative` |
| **Upload** | `upload_image_from_url`, `upload_image_from_path` |
| **Create** | `create_link_ad_creative`, `create_placement_customized_creative`, `create_ad`, `create_single_image_ad`, `create_placement_customized_ad` |
| **Manage** | `create_campaign`, `pause_campaign`, `resume_campaign`, `pause_ad_set`, `resume_ad_set`, `pause_ad`, `resume_ad`, `duplicate_ad`, `duplicate_ad_set`, `duplicate_campaign` |
| **Insights** | `get_campaign_insights`, `get_ad_set_insights`, `get_ad_insights`, `get_account_insights` |

## Setup

### 1. Get Meta API credentials (one-time)

You need three values from Meta:

**a) A System User access token with `ads_management` scope**

1. Go to [business.facebook.com](https://business.facebook.com) → **Business Settings** → **Users → System Users**.
2. Create a new System User (admin role).
3. Click **Add Assets** → assign your Ad Account with **Manage campaigns** permission, and the Facebook Page with **Create content** + **Manage Page** permissions.
4. Click **Generate New Token** → select your Meta Developer App (create one at [developers.facebook.com/apps](https://developers.facebook.com/apps) if you don't have one — pick the "Business" type).
5. Tick scopes: `ads_management`, `ads_read`, `business_management`, `pages_read_engagement`, `pages_manage_posts`.
6. Pick **Never** for expiry. Copy the token.

**b) Your Ad Account ID** — visible in the Ads Manager URL as `act=...` (e.g. `act_47599739`).

**c) Your Facebook Page ID** — visible in **Page Settings → Page info**, or by calling `GET https://graph.facebook.com/v21.0/me/accounts?access_token=YOUR_TOKEN`.

### 2. Install the server

```bash
git clone https://github.com/donaldman1997/marketing-skill.git
cd marketing-skill
git checkout claude/meta-ads-creative-upload-PRClS

# With uv (recommended)
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Configure credentials

```bash
cp .env.example .env
# Edit .env and paste in META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID
```

### 4. Wire it into Claude Code

Add to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/marketing-skill", "run", "meta-ads-mcp"],
      "env": {
        "META_ACCESS_TOKEN": "EAA...",
        "META_AD_ACCOUNT_ID": "act_47599739",
        "META_PAGE_ID": "1234567890"
      }
    }
  }
}
```

Restart Claude Code. The tools appear as `mcp__meta-ads__*`.

## Example: uploading the "More Time, Less Stress" creatives

Once the server is running, ask Claude:

> Find the "More Time Less Stress" campaign, list its ad sets, then add a new ad to the active ad set with these three images (one per aspect ratio), this primary text, and the registration link.

Behind the scenes Claude calls:

1. `find_campaign_by_name("More Time Less Stress")` → campaign ID
2. `list_ad_sets(campaign_id)` → pick the active ad set
3. `upload_image_from_path("./square_1x1.png")` → feed_hash
4. `upload_image_from_path("./story_9x16.png")` → story_hash
5. `upload_image_from_path("./portrait_4x5.png")` → portrait_hash
6. `create_placement_customized_ad(adset_id=..., ad_name="MTLS — 3rd June webinar",
   primary_text="What if the reason your business feels harder...",
   headline="More Time, Less Stress — Free Live Workshop",
   description="Wed 3rd June, 10am UK · Live on Zoom",
   link_url="https://your-registration-link",
   feed_image_hash=..., story_image_hash=..., portrait_image_hash=...,
   call_to_action="SIGN_UP", status="PAUSED")`

The ad is created in `PAUSED` state by default — review it in Ads Manager
before unpausing. Flip `status="ACTIVE"` to launch immediately.

## Safety defaults

- **All create/duplicate calls default to `status="PAUSED"`** so nothing
  starts spending without you reviewing it.
- Mutating calls hit the live Meta API — there's no sandbox toggle.
- The server reads credentials from environment only; nothing is logged.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check meta_ads_mcp tests
```

## License

MIT
