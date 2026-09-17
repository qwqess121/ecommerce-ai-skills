---
name: sys-amazon-dsp
description: "Analyze Amazon DSP campaigns via the Marketplace Ad Pros MCP server: line items, halo sales, NTB, reach, frequency, audiences. Use when asked about DSP or programmatic ads."
---

# Amazon DSP Skill

DSP (Demand-Side Platform) is Amazon's programmatic ad platform. It runs separately from Sponsored Ads and exposes a different metric set focused on reach, frequency, video, audience prospecting, and new-to-brand acquisition. This skill covers how to use our MCP DSP tools and how to answer the questions DSP advertisers actually care about.

## Hard prerequisites — check these first

DSP is not available on every account. Before answering any DSP question:

1. **DSP requires an agency profile.** DSP resources only exist under profiles where `account_type == "agency"`. If the user's profiles are all seller or vendor type, they don't have DSP through this MCP.
2. **List integrations and find the agency profile.** Use `list_amazon_ads_integrations` then `list_amazon_ads_integration_accounts`. Filter for `account_type: "agency"`. If none exist, tell the user DSP isn't connected and stop — don't fabricate data.
3. **Confirm which advertiser to scope to.** A single agency profile typically owns many `dsp_advertisers`. Always pin the scope before answering performance questions; aggregating across advertisers usually combines unrelated brands.

## The drill-down hierarchy (this is non-obvious)

DSP resources nest. **Each level requires the parent's ID**, and the API errors when a parent is missing:

```
agency profile (account_id)
  -> dsp_advertisers              requires: nothing beyond account scope
     -> dsp_campaigns             requires: advertiser_id
        -> dsp_ad_groups          requires: advertiser_id [+ campaign_id to filter]
           -> dsp_targets         requires: advertiser_id + ad_group_id
        -> dsp_creatives          requires: advertiser_id   (creative library is at advertiser level, not campaign)
```

When the user asks "show me targets in campaign X", you still need the `ad_group_id` because targets are scoped at the ad-group level. Walk down the hierarchy with `list_resources` rather than guessing IDs.

Use `list_resource_types(resource_types=["dsp_campaigns"], include_schemas=true)` to see the exact filter and field schema for any DSP resource type.

## Tool selection

| Question type | Tool |
|---|---|
| "How is DSP performing?" / spend / sales / ROAS / NTB | `ask_report_analyst` with a DSP report type |
| "Show me my line items / campaigns / ad groups / creatives" | `list_resources` with the relevant `dsp_*` resource type |
| "Pull data for one specific creative or target" | `list_resources` with the parent IDs in `filters` |

`ask_report_analyst` is the workhorse for DSP performance questions. The structural `list_resources` calls are mostly for browsing — they return live API state, not historical metrics.

## DSP report types — pick the right one

`ask_report_analyst` accepts a `report_type` hint. DSP exposes several reports, each with different available metrics:

| Report | What it answers | Key fields |
|---|---|---|
| `dsp_campaign_performance` | Headline performance by campaign / order / line item | `totalCost`, `impressions`, `clickThroughs`, `totalSales14d`, `totalPurchases14d`, `totalNewToBrandPurchases14d`, `dpv14d`, `eCPM`, `eCPC`, `totalROAS14d` |
| `dsp_products` | Per-ASIN attribution (Promoted vs Halo) | `amazonStandardId`, `parentASIN`, `asinConversionType`, `featuredASIN`, `totalSales14d`, `totalPurchases14d`, `dpv14d` |
| `dsp_campaign_creative` | Creative-level performance (size, type, video vs display) | `creativeName`, `creativeType`, `creativeSize`, plus standard metrics |
| `dsp_geography` | Country-level breakdown | `country`, `impressions`, `clickThroughs`, `totalCost`, `totalSales14d`. **Note: `eCPM`, `eCPC`, `totalROAS14d` are NOT in the geography report — compute client-side.** |
| `dsp_audience` | Reach metrics per line item. **SUMMARY only** — one row per line item over the entire window, no time series. Purchase metrics aren't available here. | `impressions`, `clickThroughs`, `totalCost`, `dpv14d`, `reach` (where available) |
| `dsp_conversion_source` | Sales split by conversion source (Amazon Retail vs other) and attribution type | `conversionSourceName`, `conversionSourceOwner`, `conversionSourceAttributionType`, `totalPurchases14d`, `totalSales14d` |

When the user asks a performance question, name the report type explicitly in your `ask_report_analyst` call so the analyst routes correctly. Example phrasing: "...using the `dsp_campaign_performance` report..."

## DSP-specific metrics worth understanding

These show up in DSP and rarely elsewhere — explain them when relevant:

- **`totalNewToBrandPurchases14d`** — purchases by customers who hadn't bought from this brand in the last 12 months. Divide by `totalPurchases14d` to get **NTB%**, the cleanest prospecting signal DSP exposes.
- **Halo vs Promoted** (`asinConversionType`) — Promoted = the ASIN you actually advertised. Halo = other ASINs the same shopper bought after seeing your ad. High halo = DSP is lifting your whole catalog, not just the featured products.
- **`featuredASIN`** ('Y' / 'N') — whether this ASIN was selected for featuring in the line item. Comparing featured vs non-featured tells you if your ASIN selection is working.
- **`dpv14d`** (detail page views, 14-day attribution) — DSP's mid-funnel signal. High DPV with low purchases means the creative is doing its job but the listing or price isn't converting.
- **Reach / frequency** — DSP attributes uniquely to households. Time-series isn't always available; treat reach reports as snapshots.
- **`totalROAS14d`** — total sales / total cost. Note this is **14-day attribution**, not click-only. For agency reporting, compare against the brand's stated attribution window.

## Common workflows

### Monthly top-line health check

> "For <brand>, show DSP performance over the last 30 days using the `dsp_campaign_performance` report. Include `totalCost`, `totalSales14d`, `totalPurchases14d`, `impressions`, `clickThroughs`, `eCPM`, `eCPC`, `totalROAS14d`, and `dpv14d`."

Use this as a first call for any DSP question. Confirms data is flowing and gives a baseline.

### Which ASINs is DSP actually moving?

> "For <brand>, top 20 ASINs by `totalSales14d` over the last 30 days using the `dsp_products` report. Include `amazonStandardId`, `parentASIN`, `brandName`, `totalPurchases14d`, `totalSales14d`, `dpv14d`, `totalNewToBrandPurchases14d`. Sort by `totalSales14d` desc."

Then ask the follow-up: "break out by `asinConversionType` (Promoted vs Halo)" to surface the halo effect.

### Find the prospecting line items

> "Last 30 days, line items where `totalNewToBrandPurchases14d` is more than 40% of `totalPurchases14d`. Include `lineItemName`, `totalPurchases14d`, `totalNewToBrandPurchases14d`, NTB%, `totalCost`."

Lead with these in any "where is DSP working" conversation — NTB is the metric Amazon Sponsored Ads can't match.

### High-DPV, low-purchase diagnosis (funnel gap)

> "Line items with `dpv14d > 500` but `totalPurchases14d < 10` over the last 30 days using `dsp_campaign_performance`."

Then cross-reference with `dsp_products` for the same ASINs. If the issue shows at the line-item level, it's an audience problem. If it shows at the ASIN level, it's a listing/price problem.

### Country breakdown for multi-market brands

> "Last 30 days, break out DSP performance by country using the `dsp_geography` report. Include `impressions`, `clickThroughs`, `totalCost`, `totalSales14d`, `dpv14d`. Compute CTR and implied ROAS per country client-side."

Reminder: the geography report doesn't expose ROAS / eCPM / eCPC directly — compute them.

### Video vs Display split

> "Last 30 days using the `dsp_campaign_creative` report, compare `creativeType` Video vs Display. Aggregate impressions, clickThroughs, totalCost, totalSales14d. Compute CTR and CVR per type."

Don't reduce video and display to a single ROAS — they answer different funnel questions (reach/awareness vs conversion).

## Pitfalls

- **Aggregating across advertisers.** A single agency profile can hold dozens of `dsp_advertisers`. Always scope queries to one advertiser unless the user explicitly wants cross-brand totals.
- **Mixing attribution windows.** DSP defaults to 14-day total attribution. If the user has been quoting 7-day click-only numbers from another tool, the comparison is apples-to-oranges — call this out explicitly.
- **Asking the geography report for ROAS.** It doesn't carry it. Compute from cost and sales client-side and say so.
- **Treating the audience report as time-series.** `dsp_audience` is a SUMMARY snapshot. Don't try to chart it day-over-day; pair it with `dsp_campaign_performance` for purchase metrics.
- **Forgetting that DSP has its own creative pipeline.** Pausing a Sponsored Ads campaign doesn't pause a DSP line item. Be precise about which platform the user is asking about, especially when they say "campaign".

## Tips

- The MCP exposes `dsp_creatives` at the advertiser level (not the campaign level). To answer "what creatives does this campaign use", drill from creatives to ad groups.
- DSP performance numbers lag 1-3 days behind real time, similar to Sponsored Ads.
- "Order" in DSP terminology is roughly equivalent to "campaign" elsewhere — note `orderName` in report fields.
- For experiment-style questions ("did this line item lift sales?"), pair `dsp_campaign_performance` with the `dsp_conversion_source` report to see whether lift came from on-Amazon or off-Amazon conversions.
