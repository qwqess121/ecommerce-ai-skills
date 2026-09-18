---
name: amazon-ads-mcp
description: Guide for using the Marketplace Ad Pros MCP server to manage and analyze Amazon Advertising accounts. Use when working with Amazon Ads campaigns, performance reports, bid/budget recommendations, keyword research, or product data through the MCP tools.
metadata:
  author: marketplace-ad-pros
  version: "1.0"
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

Use these tools to explore what campaigns, ad groups, keywords, and targets exist:

| Tool | Use When |
|------|----------|
| `list_amazon_ads_campaigns` | User wants to see their campaigns, check campaign states, or you need campaign IDs for deeper exploration |
| `list_amazon_ads_campaign_ad_groups` | Need to drill into a campaign's ad groups |
| `list_amazon_ads_campaign_keywords` | Need to see keyword targets in a campaign/ad group |
| `list_amazon_ads_campaign_targets` | Need to see product/category targeting clauses (ASIN targeting, category targeting) |
| `list_amazon_ads_campaign_product_ads` | Need to see which products are advertised in a campaign |

These tools require `integration_id` and `account_id` at minimum. Campaigns require those two. Ad groups, keywords, targets, and product ads also require `campaign_id`. Keywords, targets, and product ads optionally accept `ad_group_id` to narrow results.

All list tools cap results at 100 items. Use `state_filter` (ENABLED, PAUSED, ARCHIVED) to narrow results. Default is typically ENABLED.

### Recommendations

| Tool | Use When |
|------|----------|
| `get_amazon_ads_account_recs` | User wants a general overview of optimization opportunities across bid, budget, and targeting for an account |
| `get_amazon_ads_ad_group_bid_recs` | User wants Amazon's recommended bids for targets in a specific ad group |
| `get_amazon_ads_ad_group_keyword_recs` | User wants new keyword suggestions for an ad group, including impression share data |
| `get_amazon_ads_campaign_budget_rule_recs` | User wants to know about upcoming events (Prime Day, holidays) and suggested budget increases |
| `get_amazon_ads_campaigns_budget_recs` | User wants to check if campaigns are running out of budget, with estimated missed opportunities |

### Product & Brand Info

| Tool | Use When |
|------|----------|
| `get_amazon_ads_product_metadata` | Need product details (title, price, category, BSR, brand, availability) for specific ASINs |
| `list_brands` | See all brands and their associated profiles |
| `create_brand` | Create a new brand to organize profiles under |
| `assign_profiles_to_brand` | Assign or reassign advertising profiles to brands |
| `get_optimization_guide` | Get the agency's playbook/guide for how they optimize campaigns |

## Common Workflows

### "How are my ads doing?" (Account Health Check)
1. `list_brands` to identify the account
2. `ask_report_analyst` with a broad question like "For the last 14 days, show me a summary of total spend, sales14d, ACOS, impressions, and clicks across all campaigns."
3. `get_amazon_ads_account_recs` to surface any optimization recommendations

### "Which campaigns should I optimize?"
1. `list_brands` to get IDs
2. `ask_report_analyst`: "For the last 14 days, show campaigns ranked by spend. Include cost, sales14d, ACOS, impressions, clicks. Top 20."
3. For campaigns with high ACOS or low ROAS, drill in with `list_amazon_ads_campaigns` to get campaign IDs
4. `get_amazon_ads_campaigns_budget_recs` to check if top campaigns are running out of budget

### "Find wasted spend"
1. `ask_report_analyst`: "For the last 30 days, which keywords have cost > $50 but zero sales14d? Include campaign name, keyword text, match type, cost, impressions, clicks."
2. `ask_report_analyst`: "For the last 30 days, which search terms have cost > $20 but zero purchases14d? Include the search term, campaign, cost, clicks."

### "Expand my keyword targeting"
1. `list_amazon_ads_campaigns` to find the campaign
2. `list_amazon_ads_campaign_ad_groups` to find the ad group
3. `get_amazon_ads_ad_group_keyword_recs` for Amazon's keyword suggestions with impression share data
4. `ask_report_analyst`: "What are my top converting search terms in the last 30 days that are not already exact match keywords?"

### "Check product performance"
1. `ask_report_analyst`: "Top 10 ASINs by sales14d in the last 14 days. Include ASIN, cost, sales14d, ACOS, impressions."
2. `get_amazon_ads_product_metadata` with those ASINs to get product details (title, price, BSR, availability)

### "Prepare for an upcoming event (Prime Day, Black Friday)"
1. `list_amazon_ads_campaigns` to identify key campaigns
2. `get_amazon_ads_campaign_budget_rule_recs` for each campaign to see suggested budget increases for upcoming events
3. `ask_report_analyst`: "Show me performance during last year's Prime Day period (July 11-12, 2025) vs the week before. Include spend, sales14d, ACOS."

## Tips

- The `ask_report_analyst` tool is by far the most powerful tool. Use it for any data/metrics question. Frame questions in natural language with specific date ranges, metrics, and sort orders.
- Report data typically has a 2-3 day lag from Amazon. If asked about "today" or "yesterday", note this lag.
- When the user has multiple profiles, always confirm which one before making calls. The system prompt includes the user's profiles with their IDs.
- Most tools require `integration_id` + `account_id`. Get these from `list_brands` first.
- Use `brand_id` scoping on `ask_report_analyst` when the user thinks in terms of brands rather than individual profiles.
- Amazon Ads metrics use "14d" attribution windows (e.g., `sales14d`, `purchases14d`). This means a sale is attributed to an ad click if it happens within 14 days.
- ACOS = Advertising Cost of Sales = (ad spend / ad sales) * 100. Lower is generally better.
- ROAS = Return on Ad Spend = ad sales / ad spend. Higher is better. ROAS = 1/ACOS * 100.
