#!/usr/bin/env python3
"""
选类目 Top15（报告 2 档：类目 Top15，强制基准，不做形态与价格筛选）
====================================================================
从 node_top15 取回的本品精确节点销量前列中，去掉本品，按品牌去重（每个品牌保留销量最高的 ASIN），
取前 15 个品牌的代表。同一品牌的多个变体会占满名额，所以必须去重。
本品品牌与 gate.exclude_brands 中的公司品牌不计入（与竞品门槛一致，列为内部关联）。
与真竞品无关：真竞品由 竞品门槛.py 按形态与价格带筛；Top15 只看节点内的销量位次。

用法：
  python -X utf8 选类目Top15.py <数据目录>

读取：
  <数据目录>/取数配置.json           own（本品 ASIN）
  <数据目录>/candidates/node_top15.json   product_research 原文（data.items）

写出：
  <数据目录>/candidates/top15.json   {"asins":[...], "rows":[...], "shortfall":n, "basis":"..."}

退出码：0 = 已写出；1 = 缺输入文件或数据格式不对。
不足 15 个时写入 shortfall，报告中如实写明，不得用其他节点的商品凑数。
"""

import json
import re
import sys
from pathlib import Path

TOP_N = 15


def unwrap_detail(d):
    """listing/asin_detail.json 可能是工具返回原文（外层 code/message/data），也可能已展开；统一返回展开后的对象。"""
    return d.get("data", d) if isinstance(d, dict) and isinstance(d.get("data"), dict) else d


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    d = Path(sys.argv[1])
    cfg_p = d / "取数配置.json"
    pages = sorted(d.glob("candidates/node_top15_p*.json"), key=lambda f: int(re.search(r"_p(\d+)", f.stem).group(1)))
    if not cfg_p.exists():
        sys.exit("缺少 取数配置.json。")
    if not pages:
        sys.exit("缺少 candidates/node_top15_p*.json，先按取数流程调用 node_top15（逐页）。")
    cfg = load(cfg_p)
    own = cfg["own"]
    own_brand = (unwrap_detail(load(d / "listing" / "asin_detail.json")).get("brand") or "").strip().lower() if (d / "listing" / "asin_detail.json").exists() else ""
    excl_brands = {b.strip().lower() for b in cfg.get("gate", {}).get("exclude_brands", []) if b.strip()}
    if own_brand:
        excl_brands.add(own_brand)
    items = []
    for f in pages:
        items += load(f).get("data", {}).get("items", [])
    if not items:
        sys.exit("node_top15 分页中没有 data.items，请重新调用并保存原文。")
    data = {"total": load(pages[0]).get("data", {}).get("total")}

    rows, seen_brand = [], set()
    for it in items:
        asin = it.get("asin")
        brand = (it.get("brand") or "").strip().lower()
        if not asin or asin == own or not brand or brand in seen_brand or brand in excl_brands:
            continue
        seen_brand.add(brand)
        rows.append({k: it.get(k) for k in ("asin", "brand", "title", "price", "units", "ratings", "rating", "nodeLabelPath")})
        if len(rows) == TOP_N:
            break

    out = {
        "asins": [r["asin"] for r in rows],
        "rows": rows,
        "shortfall": max(0, TOP_N - len(rows)),
        "basis": f"本品精确节点按月销量降序，去掉本品 {own}，排除品牌 {sorted(excl_brands)}，按品牌去重（每品牌取销量最高的 ASIN），取前 {TOP_N} 个品牌，不做形态与价格筛选",
        "source_total": data.get("total"),
    }
    dst = d / "candidates" / "top15.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Top15：{len(rows)} 个（目标 {TOP_N}），缺额 {out['shortfall']}，已写入 {dst}")
    if out["shortfall"]:
        print("注意：去重后节点内不足 15 个品牌，报告中必须如实写明缺额。")


if __name__ == "__main__":
    main()
