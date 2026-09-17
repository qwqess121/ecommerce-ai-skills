---
description: Run a live FBA inventory health check that surfaces at-risk SKUs alongside product names, inbound replenishment, reserved stock, and effective days of supply (post-inbound) — rendered as an interactive dashboard artifact. Trigger this whenever the user asks about FBA inventory, stockout risk, days of supply, replenishment, inbound shipments, "what's running low", "what should I reorder", or wants any kind of inventory health view — even if they don't explicitly say "dashboard". Prefer this skill over a basic at-risk view whenever inbound context, product identification, or replenishment timing might matter — which is almost always for an active seller. Also trigger when the user wants to refresh a previously-built inventory pipeline view, or asks to "run the inventory check again". Uses the Marketplace Ad Pros MCP tools (Selling Partner integrations + ask_selling_partner_report_analyst) to query live data.
---

# FBA Inventory Risk Dashboard

This skill takes the user from "how's my inventory?" to a live, interactive dashboard that shows every at-risk SKU with full pipeline context — current stock, reserved units, inbound replenishment, product names, and effective days of supply once inbound is counted.

The key insight this skill encodes: **fulfillable-only DOS dramatically overstates risk**. A SKU with 2 days of fulfillable stock and 900 units inbound is not a fire. A SKU with 5 days of fulfillable stock and zero inbound is. This skill surfaces both numbers so the user can act on the real picture.

## Workflow

Follow these steps in order. Don't skip the discovery steps — the analyst tool errors when account scoping is wrong.

### 1. Identify the account

Call `list_selling_partner_integrations` to get the user's SP integrations.

If exactly one integration is returned, proceed. If multiple, ask the user which one.

Then call `list_selling_partner_accounts` with the integration_id to get marketplace accounts. Each account is one marketplace (US, MX, BR, UK, DE, etc.).

**If multiple marketplaces exist, ask the user which one** — inventory is per-marketplace and you cannot meaningfully combine them. Use a tappable-options prompt with one option per marketplace. Default suggestion: US (typically the largest).

Save the chosen `account_id` (the UUID, NOT the marketplace_id like `ATVPDKIKX0DER`).

### 2. Run the at-risk query

Call `ask_selling_partner_report_analyst` with the account_id and this exact question framing:

> FBA at-risk inventory: top 50 SKUs where current fulfillable quantity is greater than 0 AND days of supply is less than 14. Use trailing 30-day average daily units sold as the run rate. For each SKU return: seller SKU, ASIN, current fulfillable quantity, avg daily units sold (last 30 days), and days of supply (fulfillable / avg daily). Exclude SKUs with zero stock and SKUs with zero sales over the last 30 days. Sort ascending by days of supply (most urgent first).

**Why this exact framing matters:** the analyst has been observed to error on overly long or comma-heavy questions. Keep the structure: filter description → run rate definition → columns → exclusions → sort. The phrase "FBA at-risk inventory" at the start helps it route correctly.

If the call errors, retry once with simpler phrasing:
> Top 50 FBA SKUs at risk of stockout in the next 14 days. For each, show seller SKU, ASIN, current fulfillable quantity, average daily units sold over the last 30 days, and days of supply. Sort by days of supply ascending. Exclude SKUs with zero sales and zero stock.

If it errors a second time, run a sanity-check query first ("How many FBA SKUs do I have with inventory data?") to confirm the analyst is responsive.

### 3. Enrich with titles, inbound, and reserved

Make a single combined enrichment call with the SKU/ASIN list from step 2. Pass both SKUs and ASINs to give the analyst flexibility on the join:

> For these N seller SKUs (list them) / ASINs (list them), return: seller SKU, ASIN, product title, afn-fulfillable-quantity, afn-reserved-quantity, afn-inbound-working-quantity, afn-inbound-shipped-quantity, afn-inbound-receiving-quantity, and total inbound (working + shipped + receiving). One row per SKU.

A single combined call is intentional — earlier versions used two separate calls (one for titles, one for inbound) which works but burns extra query budget. If the combined call errors, fall back to two calls: titles first, then inbound. Do NOT try to combine the original at-risk query with this enrichment in a single call — the analyst tends to error on multi-table joins of that complexity.

The titles query often returns multiple rows per ASIN (one per variation SKU). Dedupe by ASIN, taking the first non-null title — Amazon's listing titles for variants of the same ASIN are usually identical.

### 4. Derive short product names

Amazon listing titles are heavily SEO-stuffed (often 200+ characters with brand names repeated 5 times). The dashboard needs a short, human-readable name. Apply this extraction:

1. Take everything before the first comma OR before the first " - " (em-dash, en-dash, and " – " count) — whichever appears first.
2. Strip leading "Official ", "Premium ", or shouting all-caps brand prefixes (e.g., "EXAMPLE BRAND NAME ").
3. Remove leading parenthetical pack indicators (e.g., "(3 Pack) Example Product Name Supplement" → "Example Product Name Supplement").
4. Pull the pack/count info from the trailing parenthetical (e.g., "(2 Pack)", "(60 Capsules)") into a separate `pack` field. If no parenthetical, leave pack empty or use a sensible default like "Pack".
5. Limit the short name to ~35 characters if possible — the dashboard cell will show the pack info separately and the full title is preserved as a hover tooltip.

Keep the full unmodified title in a `fullTitle` field on each row — the template uses it as a hover tooltip so the user can see the original Amazon listing text on demand.

### 5. Triage and headline finding

Before rendering, scan the enriched data and prepare a short headline. The triage must be inbound-aware:

- **Identify the highest-velocity at-risk SKU and check its inbound.** If it has substantial inbound (>14 days at the current run rate), call it out as "looks scary on fulfillable-only DOS, but already covered by inbound" so the user doesn't waste energy on a phantom fire.
- **List the actually-critical SKUs:** effective DOS < 2 AND inbound = 0. These are the genuine emergencies.
- **List the high-risk-no-coverage SKUs:** effective DOS 2–7 AND inbound = 0. Reorder candidates.
- **Flag reserved-quantity anomalies.** If any SKU shows reserved > 3× fulfillable, surface it specifically — this often signals stranded inventory, a stuck bulk order, or a listing-mapping bug. The template highlights this visually in amber but the narrative should name the SKU.
- **Look for same-product / different-pack clusters.** If two or more SKUs in the list share the same base product name (e.g., "Example Product Line 2-pack" + "Example Product Line 3-pack" + "Example Product Line 60-cap"), call out the category. Even if the hero pack has inbound, the variant packs often don't — that's a supplier pack-strategy gap worth surfacing.

Lead the response with this triage in 3–5 sentences before the artifact. The dashboard is interactive, but the headline is what the user actually needs to act on.

### 6. Render the dashboard artifact

Use the template at `assets/dashboard-template.jsx` as the starting point. Save the populated artifact to `/mnt/user-data/outputs/fba-inventory-risk.jsx` and present it with `present_files`.

To populate:

1. Read `assets/dashboard-template.jsx`.
2. Replace the `RAW` array with the enriched data rows. Each row needs: `sku`, `asin`, `name`, `pack`, `fulfillable`, `reserved`, `inbound`, `daily`, `dos`, `fullTitle`. Use raw numbers from the `data` field of the analyst responses, not the rounded display values from the answer text — those are formatted for humans and may have lost precision.
3. Replace the masthead values: `BRAND` (from the account's `brand` or `account_name` field), `MARKETPLACE` (from `country_code` formatted as "US Marketplace" etc.), `SNAPSHOT` (from `report_freshness.sp_fba_inventory.data_complete_through`, formatted as "YYYY-MM-DD · HH:MM UTC"), and `WINDOW` (the trailing-30-day window, e.g., "30D · 04-11 → 05-11").
4. Do not modify the styling, palette, fonts, or layout — those are part of the skill's design language. The aesthetic is editorial-financial: warm cream background, Instrument Serif display, Geist Mono for data, oxblood/amber/olive/forest urgency tiers. Generic-looking tables defeat the purpose of building this as a skill.

The template's effective-DOS computation, tiering (CRITICAL/HIGH/ELEVATED/SECURED), reserved-anomaly highlighting, and DOS-shift caption ("X.Xd w/o inbound" struck-through) are all handled by the template — no extra work needed beyond populating RAW correctly.

### 7. Offer next steps

After presenting the artifact, offer 1–2 follow-ups based on what the data shows. Don't list every option — pick what's actually useful:

- **If there are several genuine criticals with zero inbound:** offer to draft POs or reorder quantities. Note that this needs the user's lead time (PO to FBA check-in, in days) and optionally a service level / safety stock target.
- **If reserved anomalies were flagged:** offer to dig into Seller Central's stranded-inventory or reserved-detail reports for the affected SKU.
- **If same-product / different-pack clusters were found:** offer to pull the cluster's full pack-size lineup (including the non-at-risk packs) to assess whether the entire variation family needs replenishment.
- **If the picture is mostly secured by inbound:** offer to look at inbound-receiving lag (how long shipments are sitting in receiving vs. moving to fulfillable) to validate the assumed coverage isn't theoretical.

Do not offer all of these at once. Pick the most useful one or two.

## Variant queries

If the user asks for a different cut, adapt the at-risk query while keeping the structure tight:

**Already-stocked-out (lost sales right now):** Drop the `fulfillable > 0` filter; sort by `daily` desc instead of `dos` asc since DOS will all be 0. Inbound becomes the key column.

**Different time window (e.g., seasonal):** Replace "trailing 30-day" with "trailing 7-day" for hot-velocity products or "trailing 90-day" for stable lines. Be explicit about the window so the analyst doesn't pick its own. Update the `WINDOW` masthead value accordingly.

**Wider net (DOS < 30 instead of < 14):** Useful for medium-term planning. Update the at-risk query's threshold and update the "Stock > 0 · DOS < 14d" subtitle in the masthead.

## Caveats to always surface

The data has known limitations:

- Snapshot is typically 3–4 hours stale (Amazon SP-API report cadence).
- Fulfillable and inbound quantities are FBA only. MFN inventory is not included — use `get_selling_partner_listings` if the user needs the merchant-fulfilled side.
- Inbound assumes on-time arrival. If shipments sit in receiving at FCs for days, the "effective DOS" overstates real coverage.
- "Average daily units" is the 30-day mean. For SKUs with spiky demand (Prime Day items, gifting categories near holidays) this understates real near-term risk.
- Reserved units are shown but not subtracted from fulfillable in DOS calcs — reserved represents pending customer orders that will be deducted within 1–3 days, so it's a near-term overhang the dashboard surfaces but doesn't double-count.

The template footer already includes these caveats. Mention them in the response narrative when relevant.

## Common pitfalls

**Wrong account_id type.** The analyst expects the UUID from `list_selling_partner_accounts`, not the Amazon `marketplace_id` (like `ATVPDKIKX0DER`). If the analyst returns an empty or scope-mismatched result, double-check this.

**Skipping marketplace selection.** If the user has US + MX + BR and you don't ask, you'll silently run against whichever marketplace happens to be first in the list. Always confirm.

**Combining everything into one analyst call.** The analyst is reliable on the lean at-risk query and reliable on the enrichment query, but unreliable on a single mega-query that does both. Keep them separate.

**Dumping the raw Amazon listing title into the table.** Amazon titles are 200+ characters of SEO. The dashboard cell will look broken. Always extract a short name (see step 4).

**Skipping the headline.** A 25-row interactive dashboard is great, but if you don't lead with "the SKU that looks worst on fulfillable-only DOS is actually fine because of inbound" or "these 8 SKUs have zero inbound and need POs cut this week", the user has to do the triage themselves. The skill's value is doing both.

**Treating fulfillable-only DOS as the action signal.** This is the trap the original at-risk dashboard fell into. Always tier and sort by effective DOS (fulfillable + inbound) / daily. The template defaults to this — don't override it.
