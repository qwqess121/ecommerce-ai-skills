#!/usr/bin/env python3
"""
竞品门槛（可配置，按本品数据自动推导）
======================================
输入本品的详情与候选池（product_research 按价格带分页取回的全部页），按门槛选出真竞品。
门槛不写死在品类里，而是从本品数据推导：节点、形态族、价格带、同品牌排除。
形态族与排除词见 ../共享规则/取数/竞品门槛词表.json。

用法：
  python -X utf8 竞品门槛.py <数据目录>

读取：
  <数据目录>/取数配置.json              gate 字段：price_band、max_n、backup_n、search_keyword
  <数据目录>/listing/asin_detail.json   本品详情（price、title、brand、asin、nodeLabelPath）
  <数据目录>/candidates/pool_band_p*.json  product_research 的每一页原文（必须全部页都在）

写出：
  <数据目录>/candidates/gate.json          推导出的门槛参数（可审计）
  <数据目录>/candidates/true_competitors.json  {"true_competitors":[...], "backup":[...], "shortfall":n, ...}

退出码：0 = 已写出；1 = 缺页、缺本品数据或形态族无法识别（需要补取或补词表）。
规则要点：
  1. 价格带 = 本品售价 × price_band（两端倍数）。
  2. 节点：候选的 nodeLabelPath 必须与本品相同。
  3. 形态族：候选标题的形态族必须与本品相同（族由词表推导，先匹配 family_priority）。
   3b. 使用场景族：候选的场景族必须与本品相同（pheromone 吸引型；designer_dupe 名牌平替不计入）。
   3c. 人群：本品与候选都写明了女性或男性时必须一致；同时写男女（unisex）或未写明的不排除。
  4. 排除：标题含排除词（refill 等）、或为本品自身、或与本品同品牌（同家族的其他 ASIN 归为内部关联）。
  5. 同一品牌只保留一个代表（单品销量最高的 ASIN），避免同一卖家的多个变体占满名额。
     gate.exclude_brands 中列出的品牌（如本公司的其他品牌）也不计入竞品，归为内部关联。
  6. 按代表的销量从高到低取前 max_n 个；不足时如实写 shortfall，不得用别的形态凑数。
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def _shared_refs():
    """共享参考目录：工具目录的上一级 共享规则/取数（竞品门槛词表.json 所在处）。"""
    return HERE.parent / "共享规则" / "取数"

LEXICON = _shared_refs() / "竞品门槛词表.json"


PLACEHOLDER_BRANDS = {"generic", "unbranded", "none", "n/a", "unknown"}


def unwrap_detail(d):
    """listing/asin_detail.json 可能是工具返回原文（外层 code/message/data），也可能已展开；统一返回展开后的对象。"""
    return d.get("data", d) if isinstance(d, dict) and isinstance(d.get("data"), dict) else d


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def family_of(title, lex):
    t = (title or "").lower()
    for fam in lex["family_priority"]:
        for tok in lex["form_families"][fam]:
            if tok in t:
                return fam
    return None


def scenario_of(title, lex):
    """使用场景族（如 pheromone 吸引、designer_dupe 名牌平替）。与形态并列判定：形态相同但场景不同不计入真竞品。"""
    t = (title or "").lower()
    for sc in lex.get("scenario_priority", []):
        for tok in lex.get("scenario_families", {}).get(sc, []):
            if tok in t:
                return sc
    return None


def crowd_of(title):
    """目标人群：women / men / unisex（同时写男女）/ None（未写明）。只有 women 与 men 互斥才排除，unisex 与 None 不排除。"""
    t = (title or "").lower()
    women = re.search(r"\b(women|woman|her|ladies)\b", t) is not None
    men = re.search(r"\b(men|man)\b", t) is not None
    if women and men:
        return "unisex"
    if women:
        return "women"
    if men:
        return "men"
    return None


def read_pool(cand_dir):
    """读取全部分页。返回 (items, 缺失页列表, 页数)。页数以第一页 data.pages 为准。"""
    files = sorted(Path(cand_dir).glob("pool_band_p*.json"))
    if not files:
        return None, None, 0
    pages = {}
    total = None
    for f in files:
        d = load(f)
        data = d.get("data", d)
        k = int(f.stem.split("_p")[-1])
        pages[k] = data.get("items", [])
        if total is None:
            total = int(data.get("pages", 1))
    missing = [k for k in range(1, (total or 1) + 1) if k not in pages]
    items = [it for k in sorted(pages) for it in pages[k]]
    return items, missing, total or 1


def brand_reps_for_cutoff(items, own_asin, own_brand, own_node, own_family, own_scenario, own_crowd, own_price, lo_mult, hi_mult, lex, gate_cfg):
    lo, hi = own_price * lo_mult, own_price * hi_mult
    excl = [x.lower() for x in lex["exclude_title_terms"]]
    excl_brands = {b.strip().lower() for b in gate_cfg.get("exclude_brands", []) + gate_cfg.get("internal_brands", []) if b.strip()}
    by_brand = {}
    for it in items:
        price = it.get("price")
        if price is None or not (lo <= float(price) <= hi):
            continue
        if own_node and it.get("nodeLabelPath") and it["nodeLabelPath"] != own_node:
            continue
        if it.get("asin") == own_asin:
            continue
        brand = (it.get("brand") or "").strip().lower()
        if not brand or brand in PLACEHOLDER_BRANDS or brand == own_brand or brand in excl_brands:
            continue
        title = (it.get("title") or "").lower()
        if any(x in title for x in excl) or family_of(title, lex) != own_family:
            continue
        if own_scenario and scenario_of(title, lex) != own_scenario:
            continue
        if own_crowd in ("women", "men") and crowd_of(title) in ("women", "men") and crowd_of(title) != own_crowd:
            continue
        cur = by_brand.get(brand)
        if cur is None or (it.get("units") or 0) > (cur.get("units") or 0):
            by_brand[brand] = it
    return sorted(by_brand.values(), key=lambda x: (x.get("units") or 0), reverse=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    d = Path(sys.argv[1])
    cfg = load(d / "取数配置.json")
    gate_cfg = cfg.get("gate", {})
    lo_mult, hi_mult = gate_cfg.get("price_band", [0.6, 1.4])
    max_n = int(gate_cfg.get("max_n", 5))
    backup_n = int(gate_cfg.get("backup_n", 5))

    detail_p = d / "listing" / "asin_detail.json"
    if not detail_p.exists():
        sys.exit("缺少 listing/asin_detail.json，先完成本品详情取数。")
    own = unwrap_detail(load(detail_p))
    own_asin = own["asin"]
    own_price = float(own["price"])
    own_brand = (own.get("brand") or "").strip().lower()
    own_node = own.get("nodeLabelPath") or ""

    lex = load(LEXICON)
    own_family = family_of(own.get("title"), lex)
    if own_family is None:
        sys.exit("本品标题无法归入任何形态族。请在 竞品门槛词表.json 中补充该形态的词，再重试。")
    own_scenario = scenario_of(own.get("title"), lex)
    if own_scenario is None:
        sys.exit("本品标题无法归入任何使用场景族。请在 竞品门槛词表.json 的 scenario_families 中补充，再重试。")
    own_crowd = crowd_of(own.get("title"))

    items, missing, total_pages = read_pool(d / "candidates")
    if items is None:
        sys.exit("缺少候选池：先按取数流程分页取回 candidates/pool_band_p1.json 起的全部页。")
    fetched_pages = total_pages - len(missing)
    early_stop = None
    if missing:
        # 只允许在“已取页连续且最后一页的最小销量低于截止线”时提前停止（见 竞品门槛.py 文档）
        if missing != list(range(fetched_pages + 1, total_pages + 1)):
            sys.exit(f"候选池不完整，缺第 {missing} 页（共 {total_pages} 页）。补取后再运行。")
    stop_ok = False
    if missing:
        cut_probe = brand_reps_for_cutoff(items, own_asin, own_brand, own_node, own_family, own_scenario, own_crowd, own_price, lo_mult, hi_mult, lex, gate_cfg)
        need = max_n + backup_n
        cutoff = cut_probe[need - 1]["units"] if len(cut_probe) >= need else 0
        last_units = min((it.get("units") or 0) for it in items)
        if cutoff and last_units < cutoff:
            stop_ok = True
            early_stop = {"fetched_pages": list(range(1, fetched_pages + 1)), "total_pages": total_pages,
                          "cutoff_units": cutoff, "last_fetched_units": last_units,
                          "reason": "已取页按销量降序排列，末条销量低于第 %d 个品牌的代表销量，后续页不能改变真竞品与备选"
                          % need}
        else:
            sys.exit(f"候选池不完整，缺第 {missing} 页（共 {total_pages} 页），且未达到提前停止条件。补取后再运行。")

    lo, hi = round(own_price * lo_mult, 2), round(own_price * hi_mult, 2)
    excl = [x.lower() for x in lex["exclude_title_terms"]]
    # 同公司其他品牌（如本公司的另一个品牌）列为内部关联，不计入竞品
    excl_brands = {b.strip().lower() for b in gate_cfg.get("exclude_brands", []) if b.strip()}
    # 内部关联品牌（同一卖家主体的其他品牌）：不进真竞品，但保留在类目排名中作为参照对象
    internal_set = {b.strip().lower() for b in gate_cfg.get("internal_brands", []) if b.strip()}
    internal_items = []
    reasons = {"价格带外": 0, "节点不同": 0, "形态不同": 0, "排除词": 0, "本品": 0, "同品牌": 0, "排除品牌（配置）": 0, "无品牌": 0}
    eligible = []
    for it in items:
        price = it.get("price")
        if price is None or not (lo <= float(price) <= hi):
            reasons["价格带外"] += 1
            continue
        if own_node and it.get("nodeLabelPath") and it["nodeLabelPath"] != own_node:
            reasons["节点不同"] += 1
            continue
        if it.get("asin") == own_asin:
            reasons["本品"] += 1
            continue
        brand = (it.get("brand") or "").strip()
        if not brand or brand.lower() in PLACEHOLDER_BRANDS:
            reasons["无品牌"] += 1
            continue
        if brand.lower() == own_brand:
            reasons["同品牌"] += 1
            continue
        if brand.lower() in excl_brands:
            reasons["排除品牌（配置）"] += 1
            continue
        title = it.get("title") or ""
        if any(x in title.lower() for x in excl):
            reasons["排除词"] += 1
            continue
        if family_of(title, lex) != own_family:
            reasons["形态不同"] += 1
            continue
        if scenario_of(title, lex) != own_scenario:
            reasons["场景不同"] = reasons.get("场景不同", 0) + 1
            continue
        cr = crowd_of(title)
        if own_crowd in ("women", "men") and cr in ("women", "men") and cr != own_crowd:
            reasons["人群不同"] = reasons.get("人群不同", 0) + 1
            continue
        if brand.lower() in internal_set:
            internal_items.append(it)
            reasons["内部关联（配置）"] = reasons.get("内部关联（配置）", 0) + 1
            continue
        eligible.append(it)

    # 同品牌只保留一个代表（单品销量最高；销量相同取评分数更多）
    by_brand = {}
    for it in eligible:
        key = it["brand"].strip().lower()
        cur = by_brand.get(key)
        rank = (it.get("units") or 0, it.get("ratings") or 0)
        if cur is None or rank > ((cur.get("units") or 0), (cur.get("ratings") or 0)):
            by_brand[key] = it
    reps = sorted(by_brand.values(), key=lambda x: ((x.get("units") or 0), (x.get("ratings") or 0)), reverse=True)

    true_list = reps[:max_n]
    backup_list = reps[max_n:max_n + backup_n]
    shortfall = max(0, max_n - len(true_list))

    def row(it):
        return {"asin": it["asin"], "brand": it["brand"], "title": it.get("title"), "price": it.get("price"),
                "units": it.get("units"), "ratings": it.get("ratings"), "rating": it.get("rating")}

    gate = {
        "own_asin": own_asin, "own_brand": own.get("brand"), "own_price": own_price,
        "own_family": own_family, "own_scenario": own_scenario, "own_crowd": own_crowd, "own_node": own_node,
        "price_band_multiplier": [lo_mult, hi_mult], "price_band_abs": [lo, hi],
        "exclude_title_terms": lex["exclude_title_terms"],
        "brand_dedupe": "同品牌保留单品销量最高的 ASIN",
        "exclude_brands": gate_cfg.get("exclude_brands", []),
        "internal_brands": gate_cfg.get("internal_brands", []),
        "max_n": max_n, "backup_n": backup_n,
        "pool_items": len(items), "pool_pages": total_pages,
        "excluded_counts": reasons, "eligible_asins": len(eligible), "eligible_brands": len(reps),
        "search_keyword": gate_cfg.get("search_keyword", ""),
        "early_stop": early_stop,
    }
    save(d / "candidates" / "gate.json", gate)
    if early_stop:
        save(d / "candidates" / "pool_stop.json", early_stop)
    internal_best = {}
    for it in internal_items:
        key = it["brand"].strip().lower()
        cur = internal_best.get(key)
        if cur is None or (it.get("units") or 0) > (cur.get("units") or 0):
            internal_best[key] = it
    internal_rows = sorted(internal_best.values(), key=lambda x: (x.get("units") or 0), reverse=True)
    save(d / "candidates" / "internal_related.json", {
        "asins": [x["asin"] for x in internal_rows],
        "rows": [row(x) for x in internal_rows],
        "basis": f"内部关联品牌 {sorted(internal_set)}：同一卖家主体，不计入真竞品；仍作为类目排名中的参照对象列出",
    })
    save(d / "candidates" / "true_competitors.json", {
        "true_competitors": [x["asin"] for x in true_list],
        "backup": [x["asin"] for x in backup_list],
        "true_detail": [row(x) for x in true_list],
        "backup_detail": [row(x) for x in backup_list],
        "shortfall": shortfall,
        "basis": f"门槛：节点 {own_node}；形态族 {own_family}；价格带 ${lo}–${hi}；同品牌只保留一个代表；排除词 {lex['exclude_title_terms']}",
        "brands_considered": len(reps),
    })
    print(f"候选池 {len(items)} 条（{total_pages} 页）→ 价格带与形态通过 {len(eligible)} 条 → {len(reps)} 个品牌")
    print(f"真竞品 {len(true_list)} 个（目标 {max_n}），备选 {len(backup_list)} 个，缺额 {shortfall}")
    if shortfall:
        print(f"注意：真竞品不足 {max_n} 个，报告中必须如实写明缺额，不得用其他形态凑数。")


if __name__ == "__main__":
    main()
