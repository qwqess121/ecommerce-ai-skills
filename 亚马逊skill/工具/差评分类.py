#!/usr/bin/env python3
"""
差评分类（统一口径的唯一来源）
==============================
对每个对象的差评（reviews/<ASIN>_neg.json，data.items 第 1 页）做分类，结果写入
reviews/classification_<ASIN>.json；计数只从这里算出，报告里的差评数字必须与之一致。

分类规则见 ../共享规则/取数/差评分类规则.md（四类：留香不足、渗漏、QC、其他）。

用法：
  python -X utf8 差评分类.py template <数据目录> <ASIN>
      生成 reviews/classification_<ASIN>.json 的骨架（每条含星级、日期、摘录、categories 空列表）。
      分类由人工或代理阅读 excerpt（或 content）后填写 categories。
  python -X utf8 差评分类.py import <数据目录> <分类结果.json>
      导入 {ASIN: {"1": [类别...], "2": [...], ...}} 形式的分类结果，生成分类文件。
  python -X utf8 差评分类.py stat <数据目录> [ASIN ...]
      校验并统计：每条至少一类；“其他”不得与其他类同时出现；条数与原始差评一致。
      统计结果写入分类文件的 summary 字段，并打印表格。
退出码：0 = 全部通过；1 = 校验失败（逐条列出）；2 = 用法错误。
"""

import json
import sys
from pathlib import Path

CATEGORIES = ["留香不足", "渗漏", "QC", "其他"]


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def save(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def neg_items(data_dir, asin):
    f = Path(data_dir) / "reviews" / f"{asin}_neg.json"
    if not f.exists():
        sys.exit(f"缺少 reviews/{asin}_neg.json，先按清单取差评。")
    d = load(f)
    return d.get("data", d).get("items", []), d.get("data", d).get("total")


def cls_path(data_dir, asin):
    return Path(data_dir) / "reviews" / f"classification_{asin}.json"


def template(data_dir, asin):
    items, total = neg_items(data_dir, asin)
    out = {"asin": asin, "source": f"reviews/{asin}_neg.json", "page_items": len(items), "total": total,
           "rules": "见 ../共享规则/取数/差评分类规则.md",
           "items": []}
    for i, it in enumerate(items, 1):
        content = (it.get("content") or "").replace("<br>", " ").strip()
        out["items"].append({"idx": i, "star": it.get("star"), "date": it.get("date"),
                             "excerpt": content[:160], "categories": [], "note": ""})
    save(cls_path(data_dir, asin), out)
    print(f"已生成骨架：{cls_path(data_dir, asin)}（{len(items)} 条，全量 total {total}）")


def do_import(data_dir, src):
    mapping = load(src)
    for asin, cats in mapping.items():
        p = cls_path(data_dir, asin)
        if not p.exists():
            template(data_dir, asin)
        d = load(p)
        for it in d["items"]:
            key = str(it["idx"])
            if key in cats:
                it["categories"] = cats[key]
        save(p, d)
        print(f"已导入 {asin}：{sum(1 for it in d['items'] if it['categories'])}/{len(d['items'])} 条有分类")


def check_and_stat(data_dir, asin):
    p = cls_path(data_dir, asin)
    if not p.exists():
        return [f"缺少 {p.name}，先运行 template 并完成分类"], None
    d = load(p)
    items = d["items"]
    errors = []
    _, total = neg_items(data_dir, asin)
    if len(items) != d.get("page_items"):
        errors.append(f"条数 {len(items)} 与原始第 1 页条数 {d.get('page_items')} 不一致")
    counts = {c: 0 for c in CATEGORIES}
    overlap = 0
    union = 0
    for it in items:
        cats = it.get("categories") or []
        if not cats:
            errors.append(f"第 {it['idx']} 条没有分类")
            continue
        bad = [c for c in cats if c not in CATEGORIES]
        if bad:
            errors.append(f"第 {it['idx']} 条类别不合法：{bad}")
            continue
        if "其他" in cats and len(cats) > 1:
            errors.append(f"第 {it['idx']} 条同时含“其他”与其他类，应去掉“其他”")
        for c in cats:
            counts[c] += 1
        if len([c for c in cats if c != "其他"]) > 1:
            overlap += 1
        if any(c in ("渗漏", "QC") for c in cats):
            union += 1
    summary = {"reviews_in_page": len(items), "total_negative": total, "counts": counts,
               "overlap_reviews": overlap, "leak_or_qc_union": union}
    if not errors:
        d["summary"] = summary
        save(p, d)
    return errors, summary


def stat(data_dir, asins):
    if not asins:
        asins = sorted({f.stem.replace("classification_", "") for f in (Path(data_dir) / "reviews").glob("classification_*.json")})
    failed = False
    print(f"{'ASIN':<12}{'样本':>5}{'全量':>7}{'留香不足':>9}{'渗漏':>6}{'QC':>5}{'其他':>5}{'重叠':>5}{'渗漏或QC':>9}")
    for a in asins:
        errors, s = check_and_stat(data_dir, a)
        if errors:
            failed = True
            print(f"{a}：校验失败")
            for e in errors[:20]:
                print(f"   - {e}")
            continue
        c = s["counts"]
        print(f"{a:<12}{s['reviews_in_page']:>5}{s['total_negative']:>7}{c['留香不足']:>9}{c['渗漏']:>6}{c['QC']:>5}{c['其他']:>5}{s['overlap_reviews']:>5}{s['leak_or_qc_union']:>9}")
    sys.exit(1 if failed else 0)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    cmd, data_dir = sys.argv[1], sys.argv[2]
    if cmd == "template":
        template(data_dir, sys.argv[3])
    elif cmd == "import":
        do_import(data_dir, sys.argv[3])
    elif cmd == "stat":
        stat(data_dir, sys.argv[3:])
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
