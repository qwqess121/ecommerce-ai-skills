---
name: sys-search-term-harvest-dashboard
description: "Live Amazon Ads search-term harvest analysis as an interactive dashboard: find winning terms to promote to exact. Use when asking what keywords to add or target."
---

# Search Term Harvest Dashboard

This skill takes the user from "what should I target?" to a live, interactive dashboard showing every high-CTR customer search term currently triggered by their broad and phrase keywords — the strongest candidates to promote to new exact-match targeting.

This is the positive-signal sibling to the wasted-ad-spend dashboard. Same design language, opposite valence: forest green for the headline accent, harvest-priority tiers, NEW/SAME reach badges.

## Workflow

Follow these steps in order. Don't skip the discovery steps — the analyst tool errors when scoping is wrong, and the "% of total" stat is meaningless without a context number.

### 1. Identify the account and marketplace

Call `list_brands` to get the user's brands and the advertising profiles under them.

If multiple brands exist, ask the user which brand to analyze. Use a tappable-options prompt with one option per brand (filter to brands that actually have an `accounts` entry where `platform == "amazon"`).

**Then resolve a single Amazon Ads profile/marketplace before running any query.** Inspect the chosen brand's `accounts` (where `platform == "amazon"`). If the brand has more than one Amazon Ads profile (e.g., separate US and CA accounts under one brand), **ask the user which marketplace** with a tappable-options prompt — one option per profile, labeled with country code. Don't default silently; harvest signal is per-marketplace because shopper behavior, competitor density, and language differ. Default suggestion when multiple exist: US (typically the largest).

Save the chosen `account_id` (the UUID for the specific ads profile, NOT the brand UUID) and pass it to the analyst tool via `account_ids`. Do NOT use `brand_ids` scoping for this skill — `brand_ids` would merge marketplaces, which corrupts the revenue share, reach labels, and exact-match promotion candidates that the rest of the workflow depends on being single-locale.

### 2. Pull total ad sales (context for the revenue %)

Before running the harvest query, get the total ad sales over the same window so the dashboard's "% of total" stat is real. **Two short calls beat one fat call** — the analyst has been observed to drop row-level data when asked for both rows AND aggregates in one call.

> What was total Sponsored Products sales14d across all campaigns for the last 30 days ([YYYY-MM-DD] to [YYYY-MM-DD])? Single-row summary only.

Save `total_ad_sales` from the response. Compute the date window from "today minus 2 days" backward 30 days — Amazon Ads report data has a 1–3 day lag, so the user's "today" isn't yet complete.

### 3. Run the harvest query

Call `ask_report_analyst` with the chosen scope and this exact framing:

> From the sponsored_products_search_terms report for [YYYY-MM-DD] through [YYYY-MM-DD], return the top 50 customer search terms by CTR where the matched keyword's matchType is BROAD or PHRASE only (exclude EXACT). Filter to rows with at least 100 impressions and at least 3 clicks so CTR is meaningful (no 1/2 = 50% noise).
>
> Aggregate at (customer search term, matched keyword text, matchType, campaign name) level. For each row return: searchTerm, keywordText, matchType, campaignName, impressions, clicks, ctr, cost, sales14d, purchases14d, acos (null where sales14d = 0), conversion_rate (purchases14d / clicks), and a flag searchTerm_equals_keyword that is "YES" if searchTerm exactly equals keywordText, otherwise "NO".
>
> Sort by CTR descending. Top 50 rows. Return as structured table data (not just prose summary).

**Why this framing matters:**

- "BROAD or PHRASE only (exclude EXACT)" is the harvest definition — exact-match search terms are already targeted, so there's nothing to promote.
- The 100-impression / 3-click floor prevents the top of the list being dominated by 1-click / 2-impression flukes.
- The `searchTerm_equals_keyword` flag is the key harvest decision signal: NO rows expand reach when harvested to exact; YES rows just tighten control. The dashboard surfaces this prominently.
- "Return as structured table data" guards against the analyst returning only a prose summary.

**If the analyst returns only the aggregate without the 50 detail rows** — this happens roughly 1 in 3 times — follow up immediately:

> Return just the 50 row-level results from the previous harvest query as structured table data, no totals or summaries.

### 4. Triage and headline finding

Before rendering the artifact, scan the data and prepare a brief headline. Look for:

- **Total revenue flowing through these 50 terms** — sum `sales14d`. The % of total ad sales tells you whether harvest is high-impact (≥10% of sales) or marginal (<3%).
- **Top revenue term by name** — call out the #1 sales14d row. This is almost always a NEW-reach PRIME-tier term and is the single most valuable thing the user could harvest.
- **Count of NEW + has-buys rows** — the genuine new-reach harvest candidates. Filter to `isNew && buys > 0` for the actionable subset.
- **WATCH rows (zero conversions)** — terms with high CTR but no buys. Could be attribution lag (very recent clicks haven't converted yet), competitor confusion (the search term implies a different product), or listing issues. Mention specifically if there's a cluster around one ASIN.
- **PRIME concentration** — if PRIME tier has fewer than 5 rows, the user has limited high-confidence harvest candidates and should consider running with a looser ACOS threshold (e.g., ≤55% instead of ≤40%).

Lead the response with this triage in 2–3 sentences before the artifact. The dashboard is interactive, but the headline is what the user actually acts on.

### 5. Render the dashboard artifact

Use the template at `assets/dashboard-template.jsx` as the starting point. Save the populated artifact to `/mnt/user-data/outputs/search-term-harvest.jsx` and present it with `present_files`.

To populate:

1. Read `assets/dashboard-template.jsx`.
2. Replace the `RAW` array with the actual data rows from the analyst response. Each row needs: `term`, `keyword`, `match` (string: "EXACT" / "PHRASE" / "BROAD" — though for this skill it'll always be PHRASE or BROAD given the filter), `impressions`, `clicks`, `ctr`, `cost`, `sales`, `buys`, `acos` (number or null), `cvr`, `isNew` (boolean from the YES/NO flag). Use raw numbers from the `data` field — not rounded display values from the answer text.
3. Replace the masthead constants: `BRAND` (from the brand's `name` field), `MARKETPLACE` (use the ads profile's `country` field plus " Ads", e.g., "US Ads"), `SNAPSHOT` (from `report_freshness.sponsored_products_search_terms.data_complete_through`, formatted as "YYYY-MM-DD · HH:MM UTC"), `WINDOW` (the 30-day range as "30D · MM-DD → MM-DD"), `TOTAL_AD_SALES` (the aggregate from step 2).
4. Do not modify the styling, palette, fonts, or layout — those are part of the skill's design language. The aesthetic is editorial-financial: warm cream background, Instrument Serif display, Geist Mono for data. Forest green is the positive-signal accent (the FBA and waste dashboards use oxblood for negative-signal); harvest-priority tiers run forest → olive → amber → oxblood-for-watch. Generic-looking tables defeat the purpose of building this as a skill.

### 6. Offer next steps

After presenting the artifact, offer 1–2 follow-ups based on what the data shows. Don't list every option — pick what's actually useful given the result:

- **If many PRIME + NEW rows:** offer to generate a bulk-upload exact-match keywords file (term + campaign + ad group + recommended bid based on avg_cpc). This is the most actionable next step for active harvest workflows.
- **If WATCH rows cluster around one ASIN:** offer to check that listing (high CTR + zero conversions on multiple search variants usually means PDP, price, or stock — not keyword).
- **If most rows are SAME (not NEW):** offer to re-run with `matchType IN ('BROAD')` only to find higher-divergence harvest candidates. Phrase matches often produce search terms identical to the keyword text; broad matches surface more variation.
- **If the user has multiple brands/profiles:** offer to run the same check on another brand.

Do not offer all of these at once. Pick the most useful one or two.

## Variant queries

**Show only new-reach harvest opportunities:** Add `searchTerm <> keywordText` to the filter (or filter in the artifact via the "New only" pill — both work, but server-side filtering returns more rows since the top-50-by-CTR cap is then applied to NEW rows only).

**Broader CTR floor for sparse accounts:** If the user has under ~$10K/month spend, the 100-impression floor may exclude most terms. Drop to `impressions >= 30 AND clicks >= 2`. Mention the lower confidence in the response.

**Harvest by absolute clicks instead of CTR:** Some users prefer raw volume over rate ("show me the busiest broad/phrase terms"). Change `ORDER BY ctr DESC` to `ORDER BY clicks DESC` and drop the impression floor (clicks already implies volume).

**Different window:** Replace "30 days" with the requested window. The harvest signal needs enough data to trust — under 14 days is risky.

**Different brand or marketplace:** Re-run from step 1.

## Caveats to always surface

The data has known limitations the user should be reminded of:

- Search-term reports lag 1–3 days behind real-time clicks. WATCH rows (zero conversions) may convert later if the click was recent — don't kill them aggressively.
- The PRIME tier threshold (≥30 clicks AND ACOS ≤ 40%) is tuned for mid-size accounts. For very small accounts (<$10K/month) reduce the click floor; for very large accounts, raise the ACOS ceiling.
- Conversion rate is `purchases14d / clicks`. For high-AOV products with long consideration cycles, this understates true intent.
- Harvest assumes you have control of the campaign structure. If campaigns are managed by another tool or rule, coordinate before bulk-uploading new keywords.

The template footer already surfaces methodology, reach explanation, and data source. Mention these in the response narrative when relevant.

## Common pitfalls

**Skipping the total-sales pull.** Without `TOTAL_AD_SALES`, the "% of total" stat in the masthead is meaningless or fabricated. Pull it from the analyst.

**Defaulting sort to CTR.** The user often phrases this as "top by CTR" because that's the filter framing, but the *decision* — which terms to harvest — ranks better by revenue (sales14d). The template defaults to revenue desc. Don't override unless the user explicitly asks for CTR sort.

**Hardcoding `isNew` from prose.** The analyst's answer text might describe top rows by name. Compute `isNew` from the `searchTerm_equals_keyword` field in `data`, row by row.

**Treating WATCH rows as immediate adds.** A high-CTR term with zero conversions over 30 days is *not* a harvest candidate yet. The skill labels these distinctly (oxblood, WATCH) so they're not visually conflated with PRIME/STRONG terms.

**Combining harvest analysis across multiple marketplaces.** Don't. Shopper behavior, competitor density, and language differ per marketplace. Always confirm the chosen profile.

**Skipping the headline.** A 50-row interactive dashboard is great, but if you don't lead with something like "$39K of high-intent revenue flowing through these terms, top candidate is *example product line supplement* at $12K", the user has to do the triage themselves. The skill's value is doing both.
