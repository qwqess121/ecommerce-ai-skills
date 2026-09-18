---
name: sys-amazon-ads
description: Guide for using the Marketplace Ad Pros MCP server to manage and analyze Amazon Advertising accounts. Use when working with Amazon Ads campaigns, performance reports, bid/budget recommendations, keyword research, or product data through the MCP tools.
---

# Amazon Ads MCP Server Guide

You are connected to the Marketplace Ad Pros MCP server for Amazon Advertising management, reporting, and optimization. This guide explains how to use the available tools effectively.

## Key Concepts

- **Integration**: A connection to an Amazon Advertising account. Has an `integration_id` (UUID).
- **Account/Profile**: An advertising profile within an integration. Has both an internal `account_id` (UUID) and a numeric `profile_id`. Most tools accept either.
- **Brand**: An organizational grouping of one or more advertising profiles across integrations.
- **Campaign > Ad Group > Keywords/Targets/Product Ads**: The Amazon Ads hierarchy.

## Getting Started

Always begin by identifying the user's context:

1. Call `whoami` to confirm the authenticated user and their plan status.
2. Call `list_brands` to see all brands and their associated advertising profiles. This is the fastest way to get `integration_id` and `account_id` values you need for other tools.
3. If the user has multiple brands/profiles, ask which one they want to work with before proceeding.

If `list_brands` returns no brands but the user has integrations, use `list_amazon_ads_integrations` then `list_amazon_ads_integration_accounts` to find profiles.

## Tool Selection Guide

### Performance Data & Reporting (most common)

**`ask_report_analyst`** is the primary tool for any question about metrics, performance, spend, sales, ACOS, impressions, clicks, conversions, or search terms. It queries historical report data stored in the system.

When to use:
- "How are my campaigns performing?"
- "What are my top products by sales?"
- "Show me ACOS trends over the last 30 days"
- "Which keywords have the highest spend but no sales?"
- "What are my best search terms?"
- "Compare this month vs last month"

How to write good questions for the analyst:
- Be specific about the date range: "For the last 14 days (February 2 to February 15, 2026)..."
- Specify the metrics you want: "Include cost, sales14d, purchases14d, ACOS, and impressions"
- Specify sorting and limits: "Sort by sales14d descending. Top 20."
- Name the entity type: "...best performing products/ASINs..." or "...top keywords..." or "...search terms..."

Example questions:
```
"For the last 14 days, show me the best performing products/ASINs by total sales14d. Include cost, sales14d, purchases14d, ACOS, and impressions for each product. Sort by sales14d descending. Top 20."

"For the last 7 days, which keywords have spend > $10 but zero sales14d? Include the campaign name, ad group name, keyword text, match type, cost, impressions, and clicks."

"Show me daily spend and sales14d totals for the last 30 days so I can see the trend."

"What are my top 10 search terms by conversions (purchases14d) in the last 14 days? Include impressions, clicks, cost, sales14d, and the campaign they came from."
```

Scoping options for `ask_report_analyst`:
- **Single profile**: Pass `integration_id` + `account_id`
- **Single brand**: Pass `brand_id` to query across all profiles in that brand
- **Multiple brands**: Pass `brand_ids` array
- **Multiple profiles**: Pass `account_ids` array
- **Multiple integrations**: Pass `integration_ids` array
- Only `question` is required; scope params are optional but recommended for accuracy.

### Campaign Structure & Browsing

Use `list_resource_types` to discover all available resource types and their filter schemas. Then use `list_resources` with a `resource_type` to browse data.

Common resource types:

| Resource Type | Description | Key Filters |
|---|---|---|
| `sp_campaigns` | Sponsored Products campaigns | `state`, `name_filter` |
| `sp_ad_groups` | SP ad groups | `campaign_id` (required) |
| `sp_keywords` | SP keyword targets | `campaign_id` (required), `ad_group_id` |
| `sp_targets` | SP product/category targets | `campaign_id` (required), `ad_group_id` |
| `sp_product_ads` | SP product ads | `campaign_id` (required), `ad_group_id` |
| `sb_campaigns` | Sponsored Brands campaigns | `state`, `name_filter` |
| `sb_ad_groups` | SB ad groups | `campaign_id` (required) |
| `sb_keywords` | SB keyword targets | `campaign_id` (required) |
| `dsp_advertisers` | DSP advertisers (agency profiles only) | `next_token` |
| `dsp_campaigns` | DSP campaigns | `advertiser_id` (required), `state_filter` |
| `dsp_ad_groups` | DSP ad groups | `advertiser_id` (required), `campaign_id` |
| `dsp_targets` | DSP targeting rules | `advertiser_id` (required), `ad_group_id` (required) |
| `dsp_creatives` | DSP ad creatives | `advertiser_id` (required) |

All resource types require `integration_id` + `account_id`. Results capped at 100 items per page. Use `next_token` from the response to paginate.

#### DSP Hierarchy

DSP resources follow this drill-down hierarchy — each level requires the parent's ID:

1. **Advertisers** (`dsp_advertisers`) — list all DSP advertisers under an agency profile
2. **Campaigns** (`dsp_campaigns`) — requires `advertiser_id` from step 1
3. **Ad Groups** (`dsp_ad_groups`) — requires `advertiser_id`, optionally `campaign_id` to filter
4. **Targets** (`dsp_targets`) — requires `advertiser_id` + `ad_group_id` from step 3
5. **Creatives** (`dsp_creatives`) — requires `advertiser_id` (at advertiser level, not campaign)

DSP profiles have `account_type: "agency"`. Only agency profiles can access DSP resources.

### Recommendations

| Tool | Use When |
|------|----------|
| `get_amazon_ads_account_recs` | General optimization opportunities across bid, budget, targeting |
| `get_amazon_ads_ad_group_bid_recs` | Amazon's recommended bids for targets in a specific ad group |
| `get_amazon_ads_ad_group_keyword_recs` | New keyword suggestions with impression share data |
| `get_amazon_ads_campaign_budget_rule_recs` | Upcoming events (Prime Day, holidays) and suggested budget increases |
| `get_amazon_ads_campaigns_budget_recs` | Check if campaigns are running out of budget with estimated missed opportunities |

### Native Optimization Rules (Budget & Bid Automation)

Use `list_resources`, `create_resources`, `update_resources` with the resource types below to manage Amazon's native automation rules.

| Resource Type | What It Does | Key Limit |
|---|---|---|
| `sp_budget_rules` | SP dayparting/performance budget lifts | Only increases budget |
| `sb_budget_rules` | SB budget lifts (metrics: IS, NTB, ROAS) | Only increases budget |
| `sd_budget_rules` | SD budget lifts (metrics: ACOS, CTR, CVR, ROAS) | Only increases budget |
| `sp_optimization_rules` | SP bid optimization — dayparting bids, performance-based bid lifts | Only INCREMENT (increase); no DELETE — pause via `status` |
| `sb_optimization_rules` | SB CPC cap (beta) — maximize page visits while CPC <= threshold | Scoped to one campaign via entityId |

Common patterns:

- **SCHEDULE rules** (budget or bid): date-ranged or event-based lifts with optional intra-day time windows. Times use the **profile's timezone**.
- **PERFORMANCE rules**: lift when a metric condition is met. SB budget rules use `IS|NTB|ROAS`; SP and SD budget rules use `ACOS|CTR|CVR|ROAS`; SP optimization rules support 10 metrics including `ACOS`, `ROAS`, `CTR`, `CVR`, `CPC`, `SALES`, `SPEND`, etc.
- **Auto-association**: include `campaignIds` in the create payload for budget rules and SP optimization rules to auto-associate after successful creation. SB optimization rules are scoped via `entityId` on the rule itself.

Call `list_resource_types(resource_types=["sp_optimization_rules"], include_schemas=true, include_examples=true)` for full field definitions and example payloads.

### Write Operations

If write access is enabled, you can create and update campaigns, ad groups, keywords, targets, product ads, and negative keywords for SP, SB, and DSP. Use `create_resources` and `update_resources` with the appropriate `resource_type`. Call `list_resource_types` with `include_schemas=true` to see the item schema for each type.

**Important limitations:**
- Campaign state can only be set to **ENABLED** or **PAUSED**. ARCHIVED is not supported via the Amazon Ads API.
- Always confirm changes with the user before executing write operations.
- Product ads require valid ASINs that the advertiser owns.

### Product & Brand Info

| Tool | Use When |
|------|----------|
| `get_amazon_ads_product_metadata` | Product details (title, price, BSR, category) for specific ASINs |
| `list_brands` | See all brands and their profiles |
| `create_brand` / `assign_profiles_to_brand` | Organize profiles into brands |
| `get_optimization_guide` | Campaign optimization playbook and strategy guide |

## Common Workflows

### Account Health Check
1. `list_brands` to identify the account
2. `ask_report_analyst`: "For the last 14 days, summary of total spend, sales14d, ACOS, impressions, clicks across all campaigns."
3. `get_amazon_ads_account_recs` to surface optimization recommendations

### Find Wasted Spend
1. `ask_report_analyst`: "Last 30 days, keywords with cost > $50 but zero sales14d. Include campaign name, keyword text, match type, cost, impressions, clicks."
2. `ask_report_analyst`: "Last 30 days, search terms with cost > $20 but zero purchases14d."

### Filter by Budget or Bid
**Important:** `list_resources` does NOT support filtering by budget or bid amount — it only supports state and name filters. Use `ask_report_analyst` instead.

1. Budget filtering: `ask_report_analyst`: "Campaigns with daily budget greater than 500 in the last 14 days. Include campaign name, budget amount, spend, sales, ACOS."
2. Bid filtering: `ask_report_analyst`: "Keywords with bid less than 5 in the last 14 days. Include keyword text, bid, match type, campaign name, spend, sales."

Note: Report data shows bid/budget at time of report snapshot (2-3 day lag). For current live bid/budget values, use `list_resources` and inspect the returned entity data.

### Keyword Expansion
1. `list_resources(resource_type='sp_campaigns', ...)` then `list_resources(resource_type='sp_ad_groups', ..., filters={'campaign_id': '...'})` to find the ad group
2. `get_amazon_ads_ad_group_keyword_recs` for Amazon's suggestions with impression share
3. `ask_report_analyst`: "Top converting search terms in last 30 days not already exact match keywords"

### Product Performance
1. `ask_report_analyst`: "Top 10 ASINs by sales14d last 14 days. Include ASIN, cost, sales14d, ACOS."
2. `get_amazon_ads_product_metadata` with those ASINs for product details

## Tips

- Report data has a 2-3 day lag from Amazon. Note this if asked about "today" or "yesterday."
- Amazon Ads metrics use 14-day attribution windows (e.g., `sales14d`, `purchases14d`).
- ACOS = (ad spend / ad sales) x 100. Lower is better. ROAS = ad sales / ad spend.
- `list_resources` cannot filter by budget or bid amount. Use `ask_report_analyst` for budget/bid filtering against historical report data.
- Most tools require `integration_id` + `account_id`. Get these from `list_brands` first.
- Use `brand_id` scoping on `ask_report_analyst` when the user thinks in brands rather than profiles.
- When the user has multiple profiles, always confirm which one before proceeding.
