---
name: sys-amazon-listing-audit
description: Guide for auditing Amazon Seller Central and Vendor Central listings for quality, compliance, and security issues through the Marketplace Ad Pros MCP server. Use whenever the user mentions listing audits, RUFUS scoring, hijacking, suppressed listings, banned claims, listing quality, missing variations, search term safety, listing health, or anything related to whether their Amazon product pages are healthy, optimized, or at risk. Also use when the user wants to find out why a listing might be losing the buy box, getting suppressed, or under-converting despite ad spend.
---

# Amazon Listing Audit Skill

This skill teaches Claude how to use our MCP listing tools to audit Amazon catalog health — RUFUS scoring, hijacking detection, banned claims, suppression risk, structural problems, and the cross-cutting "ads + listing" workflows that catch wasted ad spend on broken pages.

## Tools

| Tool | Use for |
|---|---|
| `audit_listings` | The workhorse. Runs configurable checks against ASINs and returns severity-tagged issues. **Always supports `include_listing_data=true`** — when audit results need actionable rewrites, include it. |
| `check_review_eligibility` | Determine whether you can request a review for a specific order |
| `request_review` | Send Amazon a request-a-review for a specific order (write op — confirm with user first) |
| `get_listing_change_history` | Show what's changed on a listing over time. Critical for hijacking forensics. |
| `get_selling_partner_catalog_item` | Pull a single ASIN's catalog data (titles, bullets, attributes, dimensions) |
| `search_selling_partner_catalog` | Find ASINs by keyword across the catalog |
| `update_listing` | Apply changes to a listing (write op — confirm with user before any change) |
| `get_selling_partner_listings` | List the user's own SKUs in an account |

## Severity tiers — triage in this order

`audit_listings` tags issues by severity. Use this hierarchy when the user asks "what should I fix first?":

1. **Critical** — risks suppression. The listing could be taken offline by Amazon. Banned claims, missing required attributes, product-type mismatches, certain hijacking patterns.
2. **Warning** — affects discoverability or conversion but won't suppress. Long titles, weak bullets, low RUFUS scores, formatting issues.
3. **Info** — minor / stylistic. Useful for polish but not urgent.

Always lead the response with the critical count and which ASINs are at suppression risk. Don't bury the urgent findings inside a long flat list.

## The check categories

`audit_listings` exposes named checks. Group them by what they're really protecting:

### RUFUS / conversion quality

Amazon's RUFUS is the AI shopping assistant that recommends products from listing content. Bullets that don't answer RUFUS's three core questions don't get recommended:

1. *"Is this right for me?"* — fit, sizing, compatibility, audience signals
2. *"What's different?"* — differentiation, unique features
3. *"How do I use it?"* — use cases, instructions, occasions

Relevant checks: `rufus-bullets`, `bullet-formatting`, `bullet-prohibited-content`, `long-titles`.

When the user asks for RUFUS scoring, use `include_listing_data=true` so you can show the actual bullet text alongside each score and propose a rewrite. A score without the source text is useless to the user.

### Hijacking & content security

Listings can be modified by hijackers (rogue sellers attached to your ASIN, abusive content injection, sabotage phrasing). These are time-sensitive — every hour an injected bullet stays live is reputation damage.

Relevant checks: `hijacking-detection`, `prohibited-chars`, `title-prohibited-chars`. Pair with `get_listing_change_history` to find *when* something changed.

If the user reports a sudden conversion drop on a previously healthy ASIN, run hijacking-detection *before* exploring any other hypothesis. Sudden CVR drops without a price change or stockout are the canonical hijacking signal.

### Banned claims & compliance

Claims like "FDA approved", "clinically proven", "eco-friendly", "antibacterial", "miracle cure" trigger Amazon enforcement and can suppress listings without warning.

Relevant checks: `bullet-prohibited-content`, `amazon-issues` (surfaces what Amazon itself has flagged via the Listings API — issues that often don't appear clearly in the Seller Central UI).

### Catalog structure

Relevant checks: `product-type-mismatch`, `missing-variations`. Wrong product types prevent listing data from saving. Standalone listings that should be variations get less visibility than grouped variation families.

### Search term safety

Search terms (`generic_keyword`) are invisible to shoppers but affect indexing. Hijackers love this field because the seller can't see the damage. Run `audit_listings` with the relevant check periodically and surface anything irrelevant or suspicious.

## Common workflows

### Full catalog health check

> "Audit my full catalog (up to 25 ASINs). Give me a summary — how many critical, warning, and info issues total, and which ASINs are in the worst shape?"

Use this as the first call when the user opens with "are my listings healthy?". Don't request `include_listing_data=true` for the summary pass — only fetch listing data when you're going to act on specific ASINs (it inflates the response).

### Suppression-risk triage

> "Audit my top 15 ASINs and filter to critical-severity issues only. For each, what's the issue and what do I need to do to fix it?"

This is the "what could take my listings offline?" query. Critical-only keeps the noise down.

### RUFUS rewrite pass

> "Audit my 5 best-selling ASINs with the `rufus-bullets` check, `include_listing_data=true`. For any bullet scoring below 3, suggest a rewrite that scores higher while keeping the same message."

The rewrite step is what makes this useful — scores without rewrites just create homework for the user.

### Hijacking sweep (run regularly)

> "Run `hijacking-detection` across all my ASINs with `include_listing_data=true`. Check titles, bullets, descriptions, and search terms for injected adult content, abusive language, or sabotage phrases."

Schedule reminder: hijacking is opportunistic and continuous. Quarterly sweeps miss live attacks.

### Cross-channel: ads + listing audit

These are the highest-ROI workflows because they connect ad spend waste to fixable listing problems:

**High CPC + low conversion:**
> "Find advertised products with the highest CPC and ACOS above 50% in the last 30 days. Run a listing audit on those ASINs with `include_listing_data=true`. Are there bullet or title issues that could explain poor conversion?"

**Top spend + listing health:**
> "Top 10 products by ad spend in the last 30 days. Audit those ASINs for critical issues, weak RUFUS scores, and compliance warnings. I want to make sure my biggest ad investments have healthy listings behind them."

**Sudden CVR drop = potential hijacking:**
> "Which advertised ASINs had the biggest drop in CVR comparing the last 14 days vs the previous 14? For the top 5, run `hijacking-detection` with `include_listing_data=true`."

A previously-healthy ASIN that suddenly stops converting without a price change or stockout is the classic hijacking pattern.

### Forensic: what changed and when

> "Show me the change history for ASIN <X> in the last 30 days. I want to see who changed what and when, especially the bullets and search terms."

Use `get_listing_change_history` for this. Critical when a customer or hijacking event is suspected.

## Output guidance

- Lead with severity counts and at-risk ASINs. Don't bury critical issues in a long table.
- When proposing rewrites, show **before** and **after** for each bullet — diffs are easier to review than full rewrites.
- For compliance/banned-claims findings, name the exact phrase the user needs to remove and suggest the closest compliant alternative (e.g., "FDA approved" → "made in an FDA-registered facility", with a note that the user should confirm the substitute is accurate for their product).
- Don't apply `update_listing` without the user's explicit confirmation per change. Listing updates can take hours to propagate and can fail silently if the data is malformed.

## Pitfalls

- **Auditing without listing data.** The summary view shows "20 issues found" but doesn't show the actual bullet or title text. The user can't act on that. For any audit the user intends to fix from, request `include_listing_data=true`.
- **Conflating severity with urgency.** A `critical` issue on a never-advertised, low-volume ASIN is less urgent than a `warning` on a top-spend ASIN. Cross-reference with sales/spend data when ranking what to fix first.
- **Treating hijacking detection as one-time.** Hijackers re-attack. Build it into a regular cadence, not a one-time audit.
- **Suggesting rewrites without `include_listing_data=true`.** Without the source text, you'll either invent the original or write generic suggestions. Always pull the actual content first.
- **Running write operations (`update_listing`, `request_review`) without explicit user confirmation.** Both touch live customer-facing data.

## Tips

- Catalog audits work best in batches of 15-25 ASINs. Larger batches risk truncated responses and are harder to act on.
- The `amazon-issues` check surfaces Amazon's own flags — things like documentation deadlines and product-type warnings that often don't appear clearly in Seller Central. Run this monthly even if everything looks fine.
- Pair listing audits with the Amazon Ads Optimization skill when investigating conversion problems — bad listings and bad bidding produce the same symptom (high spend, low sales) and you need both lenses to diagnose.
- For brand-protection workflows, combine `audit_listings` (current state) with `get_listing_change_history` (what changed) to build a forensic timeline.
