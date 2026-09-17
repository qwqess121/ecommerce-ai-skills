// Search Term Harvest Dashboard — Template
//
// To populate: replace BRAND, MARKETPLACE, SNAPSHOT, WINDOW, TOTAL_AD_SALES
// constants and the RAW array with values from the analyst response.
//
// RAW row schema: {
//   term: string,         // customer search term
//   keyword: string,      // matched keyword text
//   match: string,        // "PHRASE" | "BROAD" (EXACT is excluded by the query)
//   impressions: number,
//   clicks: number,       // ≥3 by filter
//   ctr: number,          // clicks / impressions, as a decimal
//   cost: number,         // total ad cost in account currency
//   sales: number,        // sales14d
//   buys: number,         // purchases14d (0 = WATCH tier)
//   acos: number | null,  // null when sales = 0
//   cvr: number,          // purchases14d / clicks
//   isNew: boolean,       // true when searchTerm ≠ keywordText (NEW reach)
// }
//
// Do not modify the styling — the editorial-financial aesthetic is part of
// the skill and must stay in sync with fba-inventory-risk-dashboard and
// wasted-ad-spend-dashboard.

import { useState, useMemo, useEffect } from "react";
import { ArrowUp, ArrowDown, ChevronsUpDown, Search } from "lucide-react";

// ── REPLACE THESE ─────────────────────────────────────────────────────────────
const BRAND = "{{ BRAND_NAME }}";              // e.g., "Example Brand Name"
const MARKETPLACE = "{{ MARKETPLACE }}";        // e.g., "US Ads"
const SNAPSHOT = "{{ SNAPSHOT_UTC }}";          // e.g., "2026-05-11 · 15:35 UTC"
const WINDOW = "{{ DATE_WINDOW }}";             // e.g., "30D · 04-11 → 05-10"
const TOTAL_AD_SALES = 0;                       // e.g., 411965.76

const RAW = [
  // { term: "example product line supplement", keyword: "example product line", match: "PHRASE",
  //   impressions: 4988, clicks: 764, ctr: 0.1532, cost: 3232.65,
  //   sales: 12043.05, buys: 149, acos: 0.2684, cvr: 0.1950, isNew: true },
  // ... populate from analyst data field
];
// ──────────────────────────────────────────────────────────────────────────────

const palette = {
  bg: "#f4eee0",
  paper: "#fbf7ec",
  ink: "#1a1612",
  mute: "#7a6f5e",
  rule: "#d4cab3",
  oxblood: "#8a1c1c",
  amber: "#a86a16",
  olive: "#7a7320",
  forest: "#2c3a2c",
};

function tier(r) {
  if (r.buys === 0) return { label: "WATCH", color: palette.oxblood };
  const acos = r.acos ?? 999;
  if (r.clicks >= 30 && acos <= 0.40) return { label: "PRIME", color: palette.forest };
  if (r.clicks >= 10 && acos <= 0.55) return { label: "STRONG", color: palette.olive };
  return { label: "EMERGING", color: palette.amber };
}

function Stat({ label, value, sub, last }) {
  return (
    <div
      className="flex flex-col gap-1 px-6 py-5"
      style={{ borderRight: last ? "none" : `1px solid ${palette.rule}` }}
    >
      <div
        className="text-xs uppercase tracking-widest"
        style={{ color: palette.mute, fontFamily: "'Geist Mono', monospace", letterSpacing: "0.18em" }}
      >
        {label}
      </div>
      <div
        className="text-4xl"
        style={{ fontFamily: "'Instrument Serif', serif", color: palette.ink, lineHeight: 1 }}
      >
        {value}
      </div>
      {sub && (
        <div className="text-xs" style={{ color: palette.mute, fontFamily: "'Geist', sans-serif" }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function SortHeader({ label, active, dir, onClick, align = "left" }) {
  const Icon = !active ? ChevronsUpDown : dir === "asc" ? ArrowUp : ArrowDown;
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 select-none"
      style={{
        color: active ? palette.ink : palette.mute,
        fontFamily: "'Geist Mono', monospace",
        fontSize: "10.5px",
        letterSpacing: "0.16em",
        textTransform: "uppercase",
        marginLeft: align === "right" ? "auto" : 0,
      }}
    >
      <span>{label}</span>
      <Icon size={12} strokeWidth={2} />
    </button>
  );
}

function ReachBadge({ isNew }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 7px",
        fontFamily: "'Geist Mono', monospace",
        fontSize: "9.5px",
        letterSpacing: "0.12em",
        color: isNew ? palette.forest : palette.mute,
        border: `1px solid ${isNew ? palette.forest : palette.rule}`,
        background: isNew ? "rgba(44, 58, 44, 0.06)" : "transparent",
        fontWeight: 500,
      }}
    >
      {isNew ? "NEW" : "SAME"}
    </span>
  );
}

export default function SearchTermHarvestDashboard() {
  const [sort, setSort] = useState({ key: "sales", dir: "desc" });
  const [query, setQuery] = useState("");
  const [reachFilter, setReachFilter] = useState("all"); // "all" | "new" | "same"

  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap";
    document.head.appendChild(link);
    return () => {
      try { document.head.removeChild(link); } catch (e) {}
    };
  }, []);

  const totalSales = useMemo(() => RAW.reduce((s, r) => s + r.sales, 0), []);
  const newReachCount = useMemo(() => RAW.filter((r) => r.isNew && r.buys > 0).length, []);
  const primeCount = useMemo(() => RAW.filter((r) => tier(r).label === "PRIME").length, []);
  const watchCount = useMemo(() => RAW.filter((r) => r.buys === 0).length, []);
  const pctOfTotal = TOTAL_AD_SALES > 0 ? (totalSales / TOTAL_AD_SALES) * 100 : 0;

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    let filtered = q
      ? RAW.filter(
          (r) =>
            r.term.toLowerCase().includes(q) ||
            r.keyword.toLowerCase().includes(q)
        )
      : RAW;
    if (reachFilter === "new") filtered = filtered.filter((r) => r.isNew);
    if (reachFilter === "same") filtered = filtered.filter((r) => !r.isNew);
    const sorted = [...filtered].sort((a, b) => {
      const av = a[sort.key] ?? -Infinity;
      const bv = b[sort.key] ?? -Infinity;
      if (typeof av === "string") {
        return sort.dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sort.dir === "asc" ? av - bv : bv - av;
    });
    return sorted;
  }, [sort, query, reachFilter]);

  const setSortKey = (key) => {
    setSort((cur) =>
      cur.key === key
        ? { key, dir: cur.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "term" || key === "keyword" ? "asc" : "desc" }
    );
  };

  const maxCtr = RAW.length ? Math.max(...RAW.map((r) => r.ctr)) : 1;
  const maxSales = RAW.length ? Math.max(...RAW.map((r) => r.sales)) : 1;

  const fmtUSD = (n) =>
    "$" + n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  const fmtUSDcents = (n) =>
    "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div
      className="min-h-screen w-full"
      style={{ background: palette.bg, fontFamily: "'Geist', sans-serif", color: palette.ink }}
    >
      <div className="max-w-6xl mx-auto px-6 py-10 md:px-12 md:py-14">
        <header
          className="pb-8 mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4"
          style={{ borderBottom: `2px solid ${palette.ink}` }}
        >
          <div>
            <div
              className="text-xs uppercase mb-3"
              style={{
                fontFamily: "'Geist Mono', monospace",
                letterSpacing: "0.24em",
                color: palette.oxblood,
              }}
            >
              ⏱ Live · {BRAND} · {MARKETPLACE}
            </div>
            <h1
              style={{
                fontFamily: "'Instrument Serif', serif",
                fontSize: "clamp(2.5rem, 5vw, 3.75rem)",
                lineHeight: 0.95,
                color: palette.ink,
                fontWeight: 400,
              }}
            >
              Search Term <em style={{ color: palette.forest }}>Harvest</em>
            </h1>
            <p
              className="mt-3 max-w-xl"
              style={{ color: palette.mute, fontSize: "14px", lineHeight: 1.55 }}
            >
              High-CTR customer search terms triggered by your broad and phrase keywords —
              the most likely candidates to target as new exact-match keywords. Sorted by
              revenue, best opportunities first.
            </p>
          </div>
          <div
            className="text-xs"
            style={{
              fontFamily: "'Geist Mono', monospace",
              color: palette.mute,
              letterSpacing: "0.08em",
              textAlign: "right",
            }}
          >
            <div>SNAPSHOT</div>
            <div style={{ color: palette.ink }}>{SNAPSHOT}</div>
            <div className="mt-2">WINDOW</div>
            <div style={{ color: palette.ink }}>{WINDOW}</div>
          </div>
        </header>

        <section
          className="grid grid-cols-2 md:grid-cols-4 mb-10"
          style={{ background: palette.paper, border: `1px solid ${palette.rule}` }}
        >
          <Stat
            label="High-intent revenue"
            value={fmtUSD(totalSales)}
            sub={`${pctOfTotal.toFixed(1)}% of $${(TOTAL_AD_SALES / 1000).toFixed(0)}K ad sales`}
          />
          <Stat
            label="New harvest opportunities"
            value={newReachCount}
            sub="Term ≠ matched keyword · has buys"
          />
          <Stat
            label="Prime tier"
            value={primeCount}
            sub="≥30 clicks · ACOS ≤ 40%"
          />
          <Stat
            label="Watch · zero buys"
            value={watchCount}
            sub="High CTR · no conversions yet"
            last
          />
        </section>

        <div className="flex items-center gap-3 mb-4 flex-wrap">
          <div
            className="flex items-center gap-2 px-3 py-2"
            style={{ background: palette.paper, border: `1px solid ${palette.rule}`, flex: "1 1 280px", maxWidth: "400px" }}
          >
            <Search size={14} style={{ color: palette.mute }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by search term or matched keyword…"
              className="flex-1 bg-transparent outline-none text-sm"
              style={{ color: palette.ink, fontFamily: "'Geist Mono', monospace" }}
            />
            {query && (
              <button
                onClick={() => setQuery("")}
                className="text-xs"
                style={{ color: palette.mute, fontFamily: "'Geist Mono', monospace" }}
              >
                clear
              </button>
            )}
          </div>
          <div className="flex" style={{ border: `1px solid ${palette.rule}` }}>
            {[
              { key: "all", label: "All reach" },
              { key: "new", label: "New only" },
              { key: "same", label: "Same only" },
            ].map((opt, idx) => (
              <button
                key={opt.key}
                onClick={() => setReachFilter(opt.key)}
                style={{
                  padding: "8px 12px",
                  background: reachFilter === opt.key ? palette.ink : palette.paper,
                  color: reachFilter === opt.key ? palette.bg : palette.mute,
                  fontFamily: "'Geist Mono', monospace",
                  fontSize: "10.5px",
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  borderRight: idx < 2 ? `1px solid ${palette.rule}` : "none",
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div
            className="text-xs ml-auto"
            style={{ color: palette.mute, fontFamily: "'Geist Mono', monospace" }}
          >
            {rows.length} of {RAW.length}
          </div>
        </div>

        <div
          className="overflow-x-auto"
          style={{ background: palette.paper, border: `1px solid ${palette.rule}` }}
        >
          <table className="w-full" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1.5px solid ${palette.ink}` }}>
                <th className="px-4 py-3 text-left" style={{ width: "100px" }}>
                  <span
                    style={{
                      fontFamily: "'Geist Mono', monospace",
                      fontSize: "10.5px",
                      letterSpacing: "0.16em",
                      color: palette.mute,
                    }}
                  >
                    TIER
                  </span>
                </th>
                <th className="px-4 py-3 text-left">
                  <SortHeader
                    label="Search term"
                    active={sort.key === "term"}
                    dir={sort.dir}
                    onClick={() => setSortKey("term")}
                  />
                </th>
                <th className="px-4 py-3 text-left">
                  <SortHeader
                    label="Matched keyword"
                    active={sort.key === "keyword"}
                    dir={sort.dir}
                    onClick={() => setSortKey("keyword")}
                  />
                </th>
                <th className="px-4 py-3 text-left" style={{ width: "85px" }}>
                  <span
                    style={{
                      fontFamily: "'Geist Mono', monospace",
                      fontSize: "10.5px",
                      letterSpacing: "0.16em",
                      color: palette.mute,
                    }}
                  >
                    REACH
                  </span>
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader
                    label="Clicks · CTR"
                    active={sort.key === "clicks"}
                    dir={sort.dir}
                    onClick={() => setSortKey("clicks")}
                    align="right"
                  />
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader
                    label="ACOS"
                    active={sort.key === "acos"}
                    dir={sort.dir}
                    onClick={() => setSortKey("acos")}
                    align="right"
                  />
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader
                    label="Revenue"
                    active={sort.key === "sales"}
                    dir={sort.dir}
                    onClick={() => setSortKey("sales")}
                    align="right"
                  />
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const t = tier(r);
                const ctrIntensity = r.ctr / maxCtr;
                const salesIntensity = r.sales / maxSales;
                return (
                  <tr
                    key={r.term + r.keyword}
                    style={{
                      borderBottom:
                        i === rows.length - 1 ? "none" : `1px dashed ${palette.rule}`,
                      background:
                        t.label === "PRIME"
                          ? "rgba(44, 58, 44, 0.035)"
                          : t.label === "WATCH"
                          ? "rgba(138, 28, 28, 0.035)"
                          : "transparent",
                    }}
                  >
                    <td className="px-4 py-3" style={{ verticalAlign: "middle" }}>
                      <div className="flex items-center gap-2">
                        <span
                          style={{
                            display: "inline-block",
                            width: 8,
                            height: 8,
                            borderRadius: 999,
                            background: t.color,
                          }}
                        />
                        <span
                          style={{
                            fontFamily: "'Geist Mono', monospace",
                            fontSize: "9.5px",
                            letterSpacing: "0.12em",
                            color: t.color,
                            fontWeight: 500,
                          }}
                        >
                          {t.label}
                        </span>
                      </div>
                    </td>
                    <td
                      className="px-4 py-3"
                      style={{
                        fontFamily: "'Geist Mono', monospace",
                        fontSize: "13px",
                        color: palette.ink,
                        fontWeight: 500,
                        maxWidth: "240px",
                      }}
                    >
                      {r.term}
                    </td>
                    <td
                      className="px-4 py-3"
                      style={{
                        fontFamily: "'Geist Mono', monospace",
                        fontSize: "11px",
                        color: palette.mute,
                        maxWidth: "180px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                      title={r.keyword}
                    >
                      {r.keyword}
                    </td>
                    <td className="px-4 py-3" style={{ verticalAlign: "middle" }}>
                      <ReachBadge isNew={r.isNew} />
                    </td>
                    <td className="px-4 py-3 text-right" style={{ verticalAlign: "middle" }}>
                      <div className="flex items-center justify-end gap-2.5">
                        <div
                          style={{
                            width: 50,
                            height: 4,
                            background: palette.rule,
                            position: "relative",
                          }}
                          title={`CTR ${(r.ctr * 100).toFixed(2)}%`}
                        >
                          <div
                            style={{
                              position: "absolute",
                              left: 0,
                              top: 0,
                              bottom: 0,
                              width: `${ctrIntensity * 100}%`,
                              background: palette.forest,
                            }}
                          />
                        </div>
                        <span
                          style={{
                            fontFamily: "'Geist Mono', monospace",
                            fontSize: "13px",
                            color: palette.ink,
                            minWidth: 44,
                            textAlign: "right",
                          }}
                        >
                          {r.clicks}
                        </span>
                        <span
                          style={{
                            fontFamily: "'Geist Mono', monospace",
                            fontSize: "10px",
                            color: palette.mute,
                            minWidth: 44,
                            textAlign: "right",
                          }}
                        >
                          {(r.ctr * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td
                      className="px-4 py-3 text-right"
                      style={{
                        fontFamily: "'Geist Mono', monospace",
                        fontSize: "13px",
                        color: r.acos === null ? palette.mute : palette.ink,
                      }}
                    >
                      {r.acos === null ? "—" : `${(r.acos * 100).toFixed(1)}%`}
                    </td>
                    <td className="px-4 py-3 text-right" style={{ verticalAlign: "middle" }}>
                      <div className="flex items-center justify-end gap-3">
                        <div
                          style={{
                            width: 60,
                            height: 6,
                            background: palette.rule,
                            position: "relative",
                          }}
                          title={`${fmtUSDcents(r.sales)} of ${fmtUSDcents(maxSales)} max`}
                        >
                          <div
                            style={{
                              position: "absolute",
                              left: 0,
                              top: 0,
                              bottom: 0,
                              width: `${salesIntensity * 100}%`,
                              background: t.color,
                            }}
                          />
                        </div>
                        <span
                          style={{
                            fontFamily: "'Instrument Serif', serif",
                            fontSize: "22px",
                            color: t.color,
                            fontWeight: 400,
                            minWidth: 92,
                            textAlign: "right",
                          }}
                        >
                          {r.sales === 0 ? "—" : fmtUSDcents(r.sales)}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <footer
          className="mt-8 pt-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-xs"
          style={{
            borderTop: `1px solid ${palette.rule}`,
            color: palette.mute,
            fontFamily: "'Geist', sans-serif",
            lineHeight: 1.6,
          }}
        >
          <div>
            <div
              className="uppercase mb-1.5"
              style={{
                fontFamily: "'Geist Mono', monospace",
                fontSize: "10px",
                letterSpacing: "0.16em",
                color: palette.ink,
              }}
            >
              Methodology
            </div>
            Top 50 search terms by CTR matched by BROAD or PHRASE keywords. Floor: 100
            impressions and 3 clicks. Tier reflects harvest priority — PRIME needs ≥30 clicks
            and ACOS ≤ 40%.
          </div>
          <div>
            <div
              className="uppercase mb-1.5"
              style={{
                fontFamily: "'Geist Mono', monospace",
                fontSize: "10px",
                letterSpacing: "0.16em",
                color: palette.ink,
              }}
            >
              Reach
            </div>
            NEW = customer search term differs from the matched keyword text (harvesting as
            exact = new reach). SAME = identical to keyword (harvesting tightens bid control
            but doesn't expand reach).
          </div>
          <div>
            <div
              className="uppercase mb-1.5"
              style={{
                fontFamily: "'Geist Mono', monospace",
                fontSize: "10px",
                letterSpacing: "0.16em",
                color: palette.ink,
              }}
            >
              Source
            </div>
            sponsored_products_search_terms · 14-day attribution. Snapshot from{" "}
            <span style={{ color: palette.ink, fontFamily: "'Geist Mono', monospace" }}>
              {SNAPSHOT}
            </span>
            .
          </div>
        </footer>
      </div>
    </div>
  );
}
