// FBA Inventory Risk Dashboard — Template
//
// To populate: replace the RAW array, BRAND, MARKETPLACE, SNAPSHOT, and WINDOW
// values with the actual data from the analyst responses.
//
// RAW row schema: {
//   sku: string,            // seller SKU
//   asin: string,           // ASIN
//   name: string,           // short product name (see SKILL.md step 4)
//   pack: string,           // pack indicator e.g. "2 Pack", "60 Capsules"
//   fulfillable: number,    // afn-fulfillable-quantity
//   reserved: number,       // afn-reserved-quantity
//   inbound: number,        // sum of working + shipped + receiving
//   daily: number,          // avg daily units sold over trailing 30d
//   dos: number,            // fulfillable / daily (fulfillable-only DOS)
//   fullTitle: string,      // full Amazon listing title (used as hover tooltip)
// }
//
// Effective DOS, tiering, and DOS-shift captions are computed by the template.
// Do not modify the styling — the editorial-financial aesthetic is part of the skill.

import { useState, useMemo, useEffect } from "react";
import { ArrowUp, ArrowDown, ChevronsUpDown, Search } from "lucide-react";

// ── REPLACE THESE ─────────────────────────────────────────────────────────────
const BRAND = "{{ BRAND_NAME }}";              // e.g., "Example Brand Name"
const MARKETPLACE = "{{ MARKETPLACE }}";        // e.g., "US Marketplace"
const SNAPSHOT = "{{ SNAPSHOT_UTC }}";          // e.g., "2026-05-07 · 14:48 UTC"
const WINDOW = "{{ DATE_WINDOW }}";             // e.g., "30D · 04-07 → 05-07"

const RAW = [
  // {
  //   sku: "EX-SKU-001",
  //   asin: "B0EXAMPLE1",
  //   name: "Example Product Name",
  //   pack: "2 Pack",
  //   fulfillable: 3,
  //   reserved: 4,
  //   inbound: 0,
  //   daily: 5.4333,
  //   dos: 0.55,
  //   fullTitle: "Example Product Name, Official Example Brand Premium Example Product Line...",
  // },
  // ... populate from enriched analyst data
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

// Effective DOS factors in inbound stock arriving from suppliers.
const eff = (r) => (r.fulfillable + r.inbound) / r.daily;

function tier(effDos) {
  if (effDos < 2) return { label: "CRITICAL", color: palette.oxblood };
  if (effDos < 7) return { label: "HIGH", color: palette.amber };
  if (effDos < 14) return { label: "ELEVATED", color: palette.olive };
  return { label: "SECURED", color: palette.forest };
}

function Stat({ label, value, sub }) {
  return (
    <div className="flex flex-col gap-1 px-6 py-5" style={{ borderRight: `1px solid ${palette.rule}` }}>
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

export default function InventoryRiskDashboard() {
  const [sort, setSort] = useState({ key: "effectiveDos", dir: "asc" });
  const [query, setQuery] = useState("");

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

  const criticalCount = useMemo(() => RAW.filter((r) => eff(r) < 2).length, []);
  const highCount = useMemo(() => RAW.filter((r) => eff(r) >= 2 && eff(r) < 7).length, []);
  const securedCount = useMemo(() => RAW.filter((r) => eff(r) >= 14).length, []);
  const totalInbound = useMemo(() => RAW.reduce((s, r) => s + r.inbound, 0), []);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? RAW.filter((r) => r.sku.toLowerCase().includes(q) || r.asin.toLowerCase().includes(q) || r.name.toLowerCase().includes(q))
      : RAW;
    const sorted = [...filtered].sort((a, b) => {
      const av = sort.key === "effectiveDos" ? eff(a) : a[sort.key];
      const bv = sort.key === "effectiveDos" ? eff(b) : b[sort.key];
      if (typeof av === "string") {
        return sort.dir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sort.dir === "asc" ? av - bv : bv - av;
    });
    return sorted;
  }, [sort, query]);

  const setSortKey = (key) => {
    setSort((cur) =>
      cur.key === key
        ? { key, dir: cur.dir === "asc" ? "desc" : "asc" }
        : { key, dir: (key === "sku" || key === "asin" || key === "name" || key === "dos" || key === "effectiveDos") ? "asc" : "desc" }
    );
  };

  const maxDaily = RAW.length ? Math.max(...RAW.map((r) => r.daily)) : 1;

  return (
    <div className="min-h-screen w-full" style={{ background: palette.bg, fontFamily: "'Geist', sans-serif", color: palette.ink }}>
      <div className="max-w-6xl mx-auto px-6 py-10 md:px-12 md:py-14">
        <header
          className="pb-8 mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4"
          style={{ borderBottom: `2px solid ${palette.ink}` }}
        >
          <div>
            <div
              className="text-xs uppercase mb-3"
              style={{ fontFamily: "'Geist Mono', monospace", letterSpacing: "0.24em", color: palette.oxblood }}
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
              FBA Inventory <em style={{ color: palette.oxblood }}>at risk</em>
            </h1>
            <p className="mt-3 max-w-xl" style={{ color: palette.mute, fontSize: "14px", lineHeight: 1.55 }}>
              SKUs with stock on hand but fewer than 14 days of supply at trailing 30-day run rate.
              Tiered by effective DOS — inbound replenishment factored in.
            </p>
          </div>
          <div
            className="text-xs"
            style={{ fontFamily: "'Geist Mono', monospace", color: palette.mute, letterSpacing: "0.08em", textAlign: "right" }}
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
          <Stat label="At-risk SKUs" value={RAW.length} sub="Stock > 0 · DOS < 14d" />
          <Stat label="Critical · <2 days" value={criticalCount} sub="Effective DOS, post-inbound" />
          <Stat label="High · 2–7 days" value={highCount} sub="Effective DOS, post-inbound" />
          <Stat label="Secured by inbound" value={securedCount} sub={`${totalInbound.toLocaleString()} units en route`} />
        </section>

        <div className="flex items-center gap-3 mb-4">
          <div
            className="flex items-center gap-2 px-3 py-2 flex-1 max-w-md"
            style={{ background: palette.paper, border: `1px solid ${palette.rule}` }}
          >
            <Search size={14} style={{ color: palette.mute }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by SKU, ASIN, or product…"
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
          <div className="text-xs" style={{ color: palette.mute, fontFamily: "'Geist Mono', monospace" }}>
            {rows.length} of {RAW.length}
          </div>
        </div>

        <div className="overflow-x-auto" style={{ background: palette.paper, border: `1px solid ${palette.rule}` }}>
          <table className="w-full" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1.5px solid ${palette.ink}` }}>
                <th className="px-4 py-3 text-left" style={{ width: "60px" }}>
                  <span style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10.5px", letterSpacing: "0.16em", color: palette.mute }}>
                    TIER
                  </span>
                </th>
                <th className="px-4 py-3 text-left">
                  <SortHeader label="Seller SKU" active={sort.key === "sku"} dir={sort.dir} onClick={() => setSortKey("sku")} />
                </th>
                <th className="px-4 py-3 text-left">
                  <SortHeader label="Product · ASIN" active={sort.key === "name"} dir={sort.dir} onClick={() => setSortKey("name")} />
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader label="Fulfillable" active={sort.key === "fulfillable"} dir={sort.dir} onClick={() => setSortKey("fulfillable")} align="right" />
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader label="Inbound" active={sort.key === "inbound"} dir={sort.dir} onClick={() => setSortKey("inbound")} align="right" />
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader label="Avg/day · 30d" active={sort.key === "daily"} dir={sort.dir} onClick={() => setSortKey("daily")} align="right" />
                </th>
                <th className="px-4 py-3 text-right">
                  <SortHeader label="DOS · effective" active={sort.key === "effectiveDos"} dir={sort.dir} onClick={() => setSortKey("effectiveDos")} align="right" />
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const effDos = eff(r);
                const t = tier(effDos);
                const intensity = r.daily / maxDaily;
                const dosShifted = Math.abs(effDos - r.dos) > 0.5;
                return (
                  <tr
                    key={r.sku}
                    style={{
                      borderBottom: i === rows.length - 1 ? "none" : `1px dashed ${palette.rule}`,
                      background: effDos < 2 ? "rgba(138, 28, 28, 0.04)" : "transparent",
                      opacity: effDos >= 14 ? 0.72 : 1,
                    }}
                  >
                    <td className="px-4 py-3" style={{ verticalAlign: "middle" }}>
                      <div className="flex items-center gap-2">
                        <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: 999, background: t.color }} />
                        <span style={{ fontFamily: "'Geist Mono', monospace", fontSize: "9.5px", letterSpacing: "0.12em", color: t.color, fontWeight: 500 }}>
                          {t.label}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3" style={{ fontFamily: "'Geist Mono', monospace", fontSize: "13px", color: palette.ink, fontWeight: 500 }}>
                      {r.sku}
                    </td>
                    <td className="px-4 py-3" title={r.fullTitle}>
                      <div style={{ fontFamily: "'Instrument Serif', serif", fontSize: "17px", color: palette.ink, lineHeight: 1.15 }}>
                        {r.name}
                        {r.pack && (
                          <span style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", color: palette.mute, marginLeft: 6, letterSpacing: "0.08em" }}>
                            · {r.pack}
                          </span>
                        )}
                      </div>
                      <div style={{ fontFamily: "'Geist Mono', monospace", fontSize: "11px", color: palette.mute, marginTop: 2, letterSpacing: "0.04em" }}>
                        {r.asin}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right" style={{ fontFamily: "'Geist Mono', monospace", fontSize: "13px", color: palette.ink }}>
                      {r.fulfillable}
                      {r.reserved > 0 && (
                        <div style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", color: r.reserved > r.fulfillable * 3 ? palette.amber : palette.mute, marginTop: 2, letterSpacing: "0.04em" }}>
                          +{r.reserved} reserved
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right" style={{ fontFamily: "'Geist Mono', monospace", fontSize: "13px", color: r.inbound > 0 ? palette.forest : palette.rule, fontWeight: r.inbound > 0 ? 500 : 400 }}>
                      {r.inbound > 0 ? `+${r.inbound.toLocaleString()}` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right" style={{ verticalAlign: "middle" }}>
                      <div className="flex items-center justify-end gap-2.5">
                        <div style={{ width: 60, height: 4, background: palette.rule, position: "relative" }}>
                          <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${intensity * 100}%`, background: palette.forest }} />
                        </div>
                        <span style={{ fontFamily: "'Geist Mono', monospace", fontSize: "13px", color: palette.ink, minWidth: 48, textAlign: "right" }}>
                          {r.daily.toFixed(2)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right" style={{ verticalAlign: "middle" }}>
                      <div style={{ fontFamily: "'Instrument Serif', serif", fontSize: "20px", color: t.color, fontWeight: 400, lineHeight: 1 }}>
                        {effDos.toFixed(2)}
                        <span style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", color: palette.mute, marginLeft: 4, letterSpacing: "0.08em" }}>
                          d
                        </span>
                      </div>
                      {dosShifted && (
                        <div style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", color: palette.mute, marginTop: 3, letterSpacing: "0.04em" }}>
                          <span style={{ textDecoration: "line-through" }}>{r.dos.toFixed(2)}d</span> w/o inbound
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <footer
          className="mt-8 pt-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-xs"
          style={{ borderTop: `1px solid ${palette.rule}`, color: palette.mute, fontFamily: "'Geist', sans-serif", lineHeight: 1.6 }}
        >
          <div>
            <div className="uppercase mb-1.5" style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", letterSpacing: "0.16em", color: palette.ink }}>
              Methodology
            </div>
            Effective DOS = (fulfillable + inbound) ÷ avg daily units (30d). Inbound = working + shipped + receiving. Tiering uses effective DOS. Sales window:&nbsp;
            <span style={{ color: palette.ink, fontFamily: "'Geist Mono', monospace" }}>{WINDOW}</span>.
          </div>
          <div>
            <div className="uppercase mb-1.5" style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", letterSpacing: "0.16em", color: palette.ink }}>
              Caveats
            </div>
            Reserved units are shown but not subtracted from fulfillable. Inbound assumes on-time arrival — receiving delays at FCs will erode coverage. MFN inventory is not included.
          </div>
          <div>
            <div className="uppercase mb-1.5" style={{ fontFamily: "'Geist Mono', monospace", fontSize: "10px", letterSpacing: "0.16em", color: palette.ink }}>
              Source
            </div>
            sp_fba_inventory · sp_listings · sp_orders · 30-day trailing window. Snapshot from {SNAPSHOT}.
          </div>
        </footer>
      </div>
    </div>
  );
}
