---
name: sys-amazon-ads-optimization
description: "Amazon Ads optimization playbook: bids, budgets, negative keywords, seasonal events (Prime Day, Black Friday), performance diagnosis. Use when optimizing campaigns."
---

# Amazon Ads Optimization Guide

Use this guide when optimizing Amazon Advertising campaigns. It covers the five-pillar campaign framework, bid strategy, negative keyword management, seasonal prep, and tactical fixes for common problems.

## Evergreen Operations

Things every Amazon brand should schedule or keep running.

### Run the Five-Pillar Campaign Framework

* **Protect** — exact brand terms + product page ads to defend your turf
* **Conquer** — target competitor ASINs to steal share
* **Strengthen** — ranking campaigns with down-only bids to climb search results
* **Dominate** — single-keyword exact campaigns with fixed bids for your heroes
* **Discover** — auto, broad, and phrase to keep finding new terms

**Cadence:** keep every pillar live and review performance once a month.

### Bid-to-Value with Guardrails

* Formula: `Bid = Revenue-per-click x target ACoS`
* Add a *minimum* bid so ranking terms never fall off the page
* Add a *maximum* bid so mature terms don't overspend

**Cadence:** continuous; raise floor bids ~25% before high seasons.

### Aggressive Negative-Keyword Program

* Rule of thumb: accounts with healthy ACoS have 3-5x more negatives than positives
* Upper-limit rule: any term with >= 20 clicks and 0 orders becomes a negative exact
* Each month run an N-gram sheet to strip low-quality themes (e.g. "ceramic")

**Cadence:** block fresh waste weekly, full audit monthly.

### Wasted-Spend Weekly

* Pull SP/SB/SD search-term & matched-target reports (Sun-Sat)
* Log spend with no orders and cut or cap truly wasted terms

**Cadence:** every week.

### Remote Health-Check Dashboard

* One sheet shows weekly spend, sales, ACoS, % non-converting spend, budget caps
* Lets leadership spot problems without opening the ad console

**Cadence:** review once a week; escalate any yellow/red cells.

### Daily Budget Hygiene

* Use Amazon's *Out-of-Budget* filter every day
* Top 20% of campaigns should never cap out; re-allocate from the bottom 80% monthly

### Seasonal Playbook for Prime Events & Holidays

* Identify keywords with >= 2 orders in the last 30 days
* "Best" set: 3x budget, up to 2x bid. "Good" set: 2x budget. Rest stay normal.
* Choose a mode: **All-Gas**, **Profit-Only**, or **Hybrid**

**Timing:** start 2 weeks before, lock budgets day-of, revert when CVR normalizes.

## Problem to Strategic Move

Higher-level pivots you pull when the business situation changes.

### Need explosive top-line growth for a surge?

Go **"All Gas, No Brakes"** — triple budgets, double bids, accept higher ACoS to grab share.

### Profit is squeezed by higher fees?

Switch to **"Profit Focus"** — leave bids steady but raise budgets only on already-efficient campaigns so the CVR lift drops straight to the bottom line.

### Sales dip and you're not sure why?

Run a **market-vs-you pulse check** in Category Insights, Opportunity Explorer & Brand Metrics *before* touching campaigns.

### Keep chopping bids on high-ACoS ranking terms?

Create a **minimum-bid ranking campaign** so visibility never falls below a set threshold while you optimize the listing.

### Lose visibility on peak-CPC days?

Use the **hedgehog focus**: isolate hero keywords in their own portfolio, raise only those bids, and let budgets (not bids) absorb extra volume elsewhere.

### Campaigns run out of budget by midday?

Apply an **80/20 budget pyramid** — unlimited budgets for the top 20% of campaigns, capped or trimmed budgets for the bottom 80%.

### Afraid to test new keywords during Q4?

Keep **max-bid guardrails** in place and funnel exploration spend into separate Discover campaigns so proven queries get the lion's share of peak-season dollars.

## Problem to Tactical Fix

Hands-on moves inside individual campaigns.

### Keyword reaches 20 clicks with 0 orders

Add it as a *negative exact* immediately.

### Many 1-click search terms bleed slowly

Run an *N-gram analysis* and negate shared tokens (e.g. "ceramic").

### Negatives are fewer than positives

Schedule a *monthly "negative sprint"* until you hit a 3-5x negative-to-positive ratio.

### Priority keyword loses rank after bid cuts

Set a *hard minimum bid* (e.g. never below $1) in that ad group.

### Black Friday morning and nothing's prepped

30-minute triage:
* Ignore console sales lag — use Business Reports for real-time data
* Top performers? Raise budgets first
* Check the *Out-of-Budget* filter
* Only lift bids on ranking keywords

### Campaign is constantly budget-capped

Estimate clicks x 2 (holiday uplift) and set daily budget at least that high; review midday.

### Launching new keyword set but want cost control

Place fresh terms in a test ad group with a *max-bid ceiling* (e.g. 0.8 x category CPC).

### Weekly ad spend keeps climbing with no revenue lift

Run the *weekly wasted-spend sweep*; trim irrelevant terms and shorten lifespans on unproven ones.

Use the Evergreen list as your permanent operating system, pull a Strategic Move when business conditions demand it, and deploy Tactical Fixes for day-to-day optimization.

## Amazon Native Optimization Rules

Amazon's built-in automation rules, managed through MCP resource types.

### SP Optimization Rules — Dayparting & Performance Bids (`sp_optimization_rules`)

* **SCHEDULE**: Increase bids by X% during specific hours/days (e.g., +50% on weekend evenings 21:00-24:00).
* **PERFORMANCE**: Increase bids when metric conditions are met (e.g., +25% when ACOS < 20%).
* **Limitation**: Only INCREMENT — bids can go up, not down. Use `update_resources` with bid changes for decreases.
* **Lifecycle**: No DELETE. Pause a rule by updating its `status` to `PAUSED` or `ENDED`.
* **Association**: Include `campaignIds` in the create payload to auto-associate on successful creation.

### Budget Rules — SP/SB/SD (`sp_budget_rules`, `sb_budget_rules`, `sd_budget_rules`)

* **SCHEDULE**: Increase budget during a date range with optional intra-day time windows (e.g., +50% between 08:00-18:00). Times use the **profile's timezone**.
* **PERFORMANCE**: Increase budget when a metric condition is met.
  * SP / SD metrics: `ACOS`, `CTR`, `CVR`, `ROAS`
  * SB metrics: `IS`, `NTB`, `ROAS`
* **Limitation**: Only increases budget, never decreases.
* **Association**: Include `campaignIds` in the create payload to auto-associate on creation.

### SB Optimization Rules — CPC Cap (beta) (`sb_optimization_rules`)

* Set a `COST_PER_CLICK` threshold (`LESS_THAN_OR_EQUAL_TO`). Amazon maximizes page visits while holding CPC <= your threshold.
* Each rule is scoped to a single campaign via `entityType=CAMPAIGN` + `entityId` on create.

### When to Use Native Rules vs Manual Updates

* **Native rules**: set-and-forget automation, event-based budget boosts, hour-of-day dayparting, ROAS-gated bid lifts.
* **Manual updates** via `update_resources`: precise per-keyword bid control, bid decreases, cross-campaign coordination, one-off surgical changes.

### Example Workflows

* **Prime Day prep (2 weeks out)**: Create `sp_budget_rules` with `dateRangeTypeRuleDuration` for the event window + `campaignIds` for top performers. Pair with `sp_optimization_rules` (PERFORMANCE, ACOS < target) to push bids on winners automatically.
* **Weekend night dayparting**: Create `sp_optimization_rules` (SCHEDULE, WEEKLY, SATURDAY+SUNDAY, 21:00-24:00, +50%) on campaigns with stronger late-evening CVR.
* **Out-of-budget auto-boost**: Create `sp_budget_rules` (PERFORMANCE, ROAS > threshold, +25%) on campaigns that consistently cap out mid-day.
* **SB CPC ceiling during a launch**: Create `sb_optimization_rules` with `COST_PER_CLICK` <= your ceiling so Amazon optimizes page visits without runaway CPCs.
