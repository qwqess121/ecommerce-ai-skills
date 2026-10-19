#!/usr/bin/env python3
"""
推荐头号词（取数清单中的 pick_head_keyword 任务）
=================================================
规则（固定，不人工挑选）：
  在本品流量词（keywords/<OWN>.json，traffic_keyword 原文）中，
  1. 本品有自然排名（rankPosition 存在）；
  2. 关键词不含本品品牌名（避免品牌词当头号词）；
  3. 取 trafficPercentage（本品流量占比）最高的一个；流量占比并列（如全为 0）时取月搜索量 searches 最高的一个。
结果写入 取数配置.json 的 head_keyword，依据写入 head_keyword_basis；
前五名候选写入 candidates/head_keyword.json，供报告核对。

用法：
  python -X utf8 推荐头号词.py <数据目录>
退出码：0 = 已写入；1 = 输入缺失或没有符合规则的关键词。
"""

import json
import sys
from pathlib import Path


def unwrap_detail(d):
    """listing/asin_detail.json 可能是工具返回原文（外层 code/message/data），也可能已展开；统一返回展开后的对象。"""
    return d.get("data", d) if isinstance(d, dict) and isinstance(d.get("data"), dict) else d


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def items_of(doc):
    # 取数流程 save 保存的是工具返回原文：{"code":..,"data":{"items":[..]}}，也兼容直接的 items
    if isinstance(doc, dict):
        if "data" in doc and isinstance(doc["data"], dict):
            return doc["data"].get("items", [])
        return doc.get("items", [])
    return doc if isinstance(doc, list) else []


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    d = Path(sys.argv[1])
    cfg_p = d / "取数配置.json"
    kw_p = d / "keywords" / f"{load(cfg_p)['own']}.json"
    detail_p = d / "listing" / "asin_detail.json"
    if not kw_p.exists():
        sys.exit(f"缺少 {kw_p.relative_to(d).as_posix()}，先按清单调用 own_keywords。")
    if not detail_p.exists():
        sys.exit("缺少 listing/asin_detail.json，先取本品详情。")

    cfg = load(cfg_p)
    brand = (unwrap_detail(load(detail_p)).get("brand") or "").strip().lower()
    items = items_of(load(kw_p))

    eligible = []
    for it in items:
        kw = (it.get("keyword") or "").strip()
        share = it.get("trafficPercentage")
        if not kw or share is None or not it.get("rankPosition"):
            continue
        if brand and brand in kw.lower():
            continue
        eligible.append(it)
    eligible.sort(key=lambda x: (x.get("trafficPercentage") or 0, x.get("searches") or 0), reverse=True)

    if not eligible:
        sys.exit("没有符合规则的关键词（需要本品自然排名与非品牌词）。")

    top = eligible[0]
    cfg["head_keyword"] = top["keyword"]
    cfg["head_keyword_basis"] = (
        f"规则：本品有自然排名、不含品牌名（{brand or '未知'}）的流量词中，流量占比最高。"
        f"该词流量占比 {top['trafficPercentage']:.2%}，自然排名 {top['rankPosition'].get('position')}，"
        f"月搜索量 {top.get('searches')}，购买率 {top.get('purchaseRate')}。"
    )
    cfg_p.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    shortlist = [{"keyword": x["keyword"], "trafficPercentage": x["trafficPercentage"],
                  "naturalPosition": x["rankPosition"].get("position"), "searches": x.get("searches")}
                 for x in eligible[:5]]
    out = {"head_keyword": top["keyword"], "basis": cfg["head_keyword_basis"], "top5": shortlist}
    dst = d / "candidates" / "head_keyword.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"头号词：{top['keyword']}（流量占比 {top['trafficPercentage']:.2%}），已写入 取数配置.json")


if __name__ == "__main__":
    main()
