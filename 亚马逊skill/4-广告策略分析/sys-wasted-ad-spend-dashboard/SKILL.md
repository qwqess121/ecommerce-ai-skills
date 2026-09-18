---
description: Run a live wasted-ad-spend analysis for an Amazon Ads account and render the results as an interactive dashboard artifact. Trigger this skill whenever the user asks about wasted ad spend, search term inefficiency, "where am I bleeding money", "what's costing me clicks without sales", money leaks in sponsored ads, high-cost search terms with no conversions, or anything related to ad budget waste — even if they don't explicitly say "dashboard". Also trigger when the user wants candidates for negative keywords based on poor search-term performance, wants to refresh a previously-built waste view, or asks Claude to "run the waste check again". Uses the Marketplace Ad Pros MCP tools (Amazon Ads brands/profiles + ask_report_analyst on sponsored_products_search_terms) to query live data and produces a sortable, filterable React artifact in the same editorial-financial design language as the FBA inventory risk dashboard.
---

# Wasted Ad Spend Dashboard

This skill takes the user from "where am I wasting money?" to a live, interactive dashboard showing every search term burning budget without producing sales, with sortable columns, magnitude bars, and cost tiers.

## Workflow

Follow these steps in order. Don't skip the discovery steps — the analyst tool errors when scoping is wrong, and waste analysis is meaningless without knowing what total spend the leak represents.

### 1. Identify the account and marketplace

Call `list_brands` to get the user's brands and the advertising profiles under them.

If multiple brands exist, ask the user which brand to analyze. Use a tappable-options prompt with one option per brand (filter to brands that actually have an `accounts` entry where `platform == "amazon"`).

**Then resolve a single Amazon Ads profile/marketplace before running any query.** Inspect the chosen brand's `accounts` (where `platform == "amazon"`). If the brand has more than one Amazon Ads profile (e.g., separate US and CA accounts under one brand), **ask the user which marketplace** with a tappable-options prompt — one option per profile, labeled with country code. Don't default silently; waste analysis is per-marketplace because consumer search behavior, competition, and pricing differ. Default suggestion when multiple exist: US (typically the largest).

Save the chosen `account_id` (the UUID for the specific ads profile, NOT the brand UUID) and pass it to the analyst tool via `account_ids`. Do NOT use `brand_ids` scoping for this skill — `brand_ids` would merge marketplaces and produce a mixed-locale dashboard that the rest of the workflow (single `MARKETPLACE` masthead, per-marketplace negative-keyword recommendations) assumes you don't have.

### 2. Pull total spend (context for the waste %)

Before running the waste query, get the total spend across the same window so the dashboard's "% of total" stat is meaningful. Don't make the user wait through two analyst calls when you can combine — but **the analyst has been observed to drop row-level data when asked for both rows AND aggregates in one call**. Two short calls beat one fat call. Order:

> What was total Sponsored Products spend, sales14d, impressions, clicks, and purchases14d across all campaigns for the last 30 days (YYYY-MM-DD to YYYY-MM-DD)? Single-row summary only.

Save `total_spend` from the response. Compute the date window from "today minus 2 days" backward 30 days — Amazon Ads report data has a 1–3 day lag, so the user's "today" isn't yet complete.

### 3. Run the waste query

Call `ask_report_analyst` with the chosen scope and this exact framing:

> From the sponsored_products_search_terms report for [YYYY-MM-DD] through [YYYY-MM-DD], find the search terms with the most wasted ad spend. Definition: zero conversions (purchases14d = 0) AND at least 5 clicks (so we have real engagement, not 1-click flukes).
>
> Aggregate at customer searchTerm level only (sum cost, clicks, impressions across all campaigns/keywords/match types that matched it). For each row return: searchTerm, total impressions, total clicks, total cost, CTR, avg_cpc, sales14d, campaign_count, top_campaign (single campaign that spent the most on this term), match_types (comma-separated distinct match types that matched it).
>
> Sort by total cost descending. Top 30 rows. Also return a single total: total wasted spend across ALL searchTerms meeting the filter (not just top 30).

**Why this framing matters:** the analyst routes by phrase. Lead with "wasted ad spend" and explicit `purchases14d = 0 AND clicks >= 5`. The aggregation-level instruction ("at customer searchTerm level only") prevents the analyst from defaulting to per-campaign or per-keyword granularity, which produces a noisier dashboard. Include both the row request AND the total-waste aggregate explicitly — the analyst sometimes returns only one or the other.

**If the analyst returns only the aggregate (totals row) without the 30 detail rows** — this happens roughly 1 in 3 times — follow up immediately with a row-only call:
> Return just the 30 row-level results from the previous wasted-ad-spend query, no totals or summaries. I want only the detail rows as structured table data.

Don't argue with the analyst about why — just re-ask for the rows.

### 4. Triage and headline finding

Before rendering the artifact, scan the data and prepare a brief headline. Look for:

- **Total waste as % of total spend** — under 2% means the user has a healthy account and the dashboard is mostly informational. Over 5% means there's real money on the table; lead with this number. Around 3–4% is typical for an active Amazon Ads account.
- **Own-brand search terms with zero conversions** — this is the diagnostic gold. If a search like "example product name capsules" gets 38 clicks at 0 conversions, that's not a keyword problem — it's a listing/PDP/price/stock problem on that ASIN. Call these out by name. Look for terms that match (or closely match) a campaign's product name.
- **Long-tail share** — if top 30 represents less than 50% of total waste, the bleed is diffuse and individual negatives won't move the needle much. Mention this so the user knows what they're getting from negative-keyword work.
- **Suspected competitor / cross-product confusion** — terms that obviously refer to a different brand or product family (e.g., "competitor brand product line" appearing on a campaign that doesn't sell that). These are easy negative-keyword wins.

Lead the response with this triage in 2–3 sentences before the artifact. The dashboard is interactive, but the headline is what the user actually needs to act on.

### 5. Render the dashboard artifact

Use the template at `assets/dashboard-template.jsx` as the starting point. Save the populated artifact to `/mnt/user-data/outputs/wasted-ad-spend.jsx` and present it with `present_files`.

To populate:

1. Read `assets/dashboard-template.jsx`.
2. Replace the `RAW` array with the actual data rows from the analyst response. Each row needs: `term`, `campaign`, `impressions`, `clicks`, `cost`, `ctr`, `cpc`, `matches` (array of strings like `["EXACT", "PHRASE"]`). Use raw numbers from the `data` field — not rounded display values from the answer text.
3. Replace the masthead constants: `BRAND` (from the brand `name` field), `MARKETPLACE` (use the ads profile's `country` field plus " Ads", e.g., "US Ads"), `SNAPSHOT` (from `report_freshness.sponsored_products_search_terms.data_complete_through`, formatted as "YYYY-MM-DD · HH:MM UTC"), `WINDOW` (the 30-day range as "30D · MM-DD → MM-DD"), `TOTAL_WASTED` (the aggregate from step 3), `TOTAL_SPEND` (from step 2), `WORST_TERM` (the term in row 1 of RAW, used in the headline stat).
4. Do not modify the styling, palette, fonts, or layout — those are part of the skill's design language. The aesthetic is editorial-financial: warm cream background, Instrument Serif display, Geist Mono for data, oxblood/amber/olive cost tiers, tier-colored magnitude bars. Generic-looking tables defeat the purpose of building this as a skill.

### 6. Offer next steps

After presenting the artifact, offer 1–2 follow-ups based on what the data shows. Don't list every option — pick what's actually useful given the result:

- **If own-brand terms appear in the waste list:** offer to run the listing audit on those ASINs (this is usually the bigger lever than negative keywords, since the spend implies real shopper intent that's failing to convert at the PDP).
- **If competitor/wrong-product terms dominate:** offer to generate a bulk-upload negative keywords list (term + recommended match type — use the `matches` array to pick negative-exact vs negative-phrase vs negative-broad).
- **If waste is low and diffuse:** offer the inverse view — high-CTR converting terms that aren't yet exact-match targeted (the harvesting query).
- **If the user has multiple brands/profiles:** offer to run the same check on another brand.

Do not offer all of these at once. Pick the most useful one or two.

## Variant queries

If the user asks for a different cut, adapt the question while keeping the structure tight:

**Near-zero (high-ACOS, not strict zero):** Replace the strict filter with `SUM(cost) > 50 AND (SUM(sales14d) = 0 OR SUM(cost) / NULLIF(SUM(sales14d), 0) > 1.0)` — captures both literal zero-conversion terms and terms that convert but at a loss. Useful when the user says "where am I losing money" rather than "where am I wasting clicks". Tier thresholds in the dashboard should be re-anchored if cost ranges shift significantly.

**By campaign:** Group at (searchTerm, campaign) rather than searchTerm alone. Use this when the user wants to know specifically where to add negatives. The dashboard then shows the same term appearing multiple times if it's wasting budget across more than one campaign. Update the `RAW` row schema to keep both fields as keys.

**Longer / shorter window:** Replace "30 days" with the requested window. Re-check the data_complete_through date if the user asks for a window ending today — they may not have full data yet.

**Different brand or marketplace:** Re-run from step 1 with a different `brand_id` and ads profile. The template constants change, but the workflow is identical.

## Caveats to always surface

The data has known limitations the user should be reminded of:

- Search-term reports lag 1–3 days behind real-time spend. The dashboard snapshot reflects this, not "right now".
- Sales attribution is 14-day. A term with zero `purchases14d` today might convert later if the click was recent; consider re-running before adding aggressive negatives on borderline cases.
- The 5-click minimum filter is a noise floor, not a hard rule. Terms with 1–4 clicks and zero conversions are excluded from this view but may still represent waste at scale — mention this if the user asks about the total long-tail.
- "Top campaign" reflects which campaign spent the most on a given search term, not necessarily the only one. The full match_types list shows which match types matched, but not which keyword text — for that, the per-keyword breakdown is a follow-up.

The template footer already surfaces methodology, exclusions, and data source. Mention these in the response narrative when relevant.

## Common pitfalls

**Skipping the total-spend pull.** Without `TOTAL_SPEND`, the "% of total" stat in the masthead is meaningless or wrong. Don't fake it from your own arithmetic — pull it from the analyst, since the report's spend number is the source of truth and accounts for cross-currency, refunds, etc.

**Hardcoding `WORST_TERM` from prose.** The analyst's answer text often summarizes a top-3 list. Pull the worst term from RAW row 1 after you populate, not from the prose.

**Wrong tier thresholds.** The template uses fixed thresholds (≥$100 critical, $60–$100 high, <$60 elevated) chosen for typical mid-six-figure-spend accounts. For very small accounts (<$10K/month) these are too high and everything will land in ELEVATED; for very large accounts (>$1M/month) they're too low and everything will be CRITICAL. Note this if the spread looks degenerate, and offer to re-anchor (e.g., scale thresholds to be 0.1%, 0.05%, and 0.025% of total spend).

**Combining waste analysis across multiple marketplaces.** Don't. Search-term performance is per-marketplace because consumer search behavior, competition, and pricing differ. Ask the user which marketplace if there's more than one — same rule as the FBA dashboard.

**Skipping the headline.** A 30-row interactive dashboard is great, but if you don't lead with something like "$5,787 wasted (3.6% of $161K), driven mostly by listing problems on the top-spend ASINs", the user has to do the triage themselves. The skill's value is doing both.
