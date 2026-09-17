#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazon title & image bulk compliance tool.

Subcommands:
  make-rules    : dump default rules.json template for editing
  clean-titles  : read source table, clean titles per rules, write report
  rename-images : copy + rename image files per SKU/ASIN naming convention

Pure standard library. XLSX reading needs `openpyxl` (pip install openpyxl).
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys

DEFAULT_RULES = {
    "title": {
        # 最大长度（含空格，多数类目 200；部分类目更短，附件可改）
        "max_length": 200,
        # 禁用符号（品牌名除外）。默认额外清除 ~ # < > *（可配置）
        "forbidden_symbols": ["!", "$", "?", "_", "{", "}", "^", "\u00ac", "\u00a6",
                               "~", "#", "<", ">", "*"],
        # 豁免小词：不计入重复词限制，且非首词时小写
        "exempt_small_words": ["in", "on", "over", "with", "and", "or", "for",
                                "the", "a", "an", "of", "to", "by", "from"],
        # 促销语库（大小写不敏感，命中即移除）
        "promo_phrases": ["free shipping", "100% quality", "best seller",
                          "top rated", "hot item", "high quality",
                          "free shipping worldwide", "100% quality guaranteed"],
        # 单字促销词（改写模式剔除：super/premium/new/best/top 等无信息量形容词）
        "single_word_promo": ["super", "premium", "new", "best", "top",
                              "hot", "great", "amazing", "perfect", "genuine"],
        # 保留原始大小写的词（缩写/品牌名等）：title_case 时命中即保持规范写法
        "preserve_case_words": ["USB", "LED", "DIY", "IPX", "TWS", "PC", "TSA",
                                "HD", "SD", "TV", "AI", "VR", "AR", "3D", "WiFi",
                                "iPhone", "iPad", "MacBook", "AirPods"],
        # 同一词允许出现次数（> 该值移除多余）
        "max_word_repeat": 2,
        # 单复数是否算同一词（去尾 s 归一）
        "singular_plural_as_duplicate": True,
    },
    "image": {
        # 主键字段：sku 或 asin
        "key_field": "sku",
        "format": "jpg",
        "padding": 2,
    },
}


# ----------------------------------------------------------------------------
# title helpers
# ----------------------------------------------------------------------------
def _norm_word(w, singular_plural):
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    if singular_plural and w.endswith("s") and len(w) > 3:
        w = w[:-1]
    return w


def has_repeat(title, rules):
    sp = rules["singular_plural_as_duplicate"]
    exempt = set(rules["exempt_small_words"])
    counts = {}
    for tok in title.split():
        w = re.sub(r"[^A-Za-z0-9]", "", tok)
        if not w:
            continue
        nw = _norm_word(w, sp)
        if nw in exempt:
            continue
        counts[nw] = counts.get(nw, 0) + 1
        if counts[nw] > rules["max_word_repeat"]:
            return True
    return False


def dedupe_words(title, rules):
    exempt = set(rules["exempt_small_words"])
    sp = rules["singular_plural_as_duplicate"]
    counts = {}
    out = []
    for tok in title.split():
        w = re.sub(r"[^A-Za-z0-9]", "", tok)
        if not w:
            out.append(tok)
            continue
        nw = _norm_word(w, sp)
        if nw in exempt:
            out.append(tok)
            continue
        counts[nw] = counts.get(nw, 0) + 1
        if counts[nw] > rules["max_word_repeat"]:
            continue  # drop extra occurrence
        out.append(tok)
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def title_case(title, exempt, preserve=None):
    """Title Case，专有名词/缩写保护。

    - exempt: 豁免小词（非首词时小写）
    - preserve: 保留原始大小写的词（缩写/品牌名），命中即输出规范写法
    - 斜杠分隔的枚举（如 Black/White）按子词各做 Title Case，保留斜杠
    """
    exempt = set(exempt or [])
    preserve_map = {}
    for p in (preserve or []):
        preserve_map[re.sub(r"[^A-Za-z0-9]", "", p).lower()] = p
    out = []
    for i, tok in enumerate(title.split()):
        core = re.sub(r"[^A-Za-z0-9]", "", tok)
        cl = core.lower()
        if not core:
            out.append(tok)
            continue
        # 0) 保留词（缩写/品牌）：输出规范写法，前后非字母数字字符原样保留
        if cl in preserve_map:
            m = re.match(r"^([^A-Za-z0-9]*)([A-Za-z0-9]+)([^A-Za-z0-9]*)$", tok)
            if m:
                pre, _mid, post = m.group(1), m.group(2), m.group(3)
                out.append(pre + preserve_map[cl] + post)
            else:
                out.append(preserve_map[cl])
            continue
        # 1) 斜杠枚举（Black/White、S/M/L）：每段各自 Title Case
        if "/" in tok:
            segs = tok.split("/")
            parts = []
            for seg in segs:
                if not seg:
                    parts.append("")
                    continue
                m = re.match(r"^([^A-Za-z0-9]*)([A-Za-z0-9]+)([^A-Za-z0-9]*)$", seg)
                if m and m.group(2):
                    parts.append(m.group(1) + m.group(2)[:1].upper() + m.group(2)[1:].lower() + m.group(3))
                else:
                    parts.append(seg)
            out.append("/".join(parts))
            continue
        # 2) 豁免小词：非首词小写
        if i > 0 and cl in exempt:
            out.append(tok.lower())
            continue
        # 3) 标准 Title Case：首字母大写，其余小写（词内含数字/符号不变形）
        out.append(tok[:1].upper() + tok[1:].lower() if tok else tok)
    return " ".join(out)


def truncate_at_boundary(t, max_len):
    if len(t) <= max_len:
        return t
    cut = t[:max_len].rfind(" ")
    if cut > 0:
        return t[:cut].rstrip()
    return t[:max_len].rstrip()


def analyze_original(title, rules):
    """Check the ORIGINAL title against rules; return list of issue codes."""
    flags = []
    if len(title) > rules["max_length"]:
        flags.append("over_length")
    if any(ch in title for ch in rules["forbidden_symbols"]):
        flags.append("forbidden_symbol")
    low = title.lower()
    if any(re.search(re.escape(p), low) for p in rules["promo_phrases"]):
        flags.append("promo_phrase")
    if has_repeat(title, rules):
        flags.append("repeat_word")
    if title.isupper() and any(c.isalpha() for c in title):
        flags.append("all_caps")
    return flags


def clean_title(title, rules):
    """Return (new_title, changed_bool). Cleaning is deterministic & non-destructive."""
    t = title
    # 1) remove promo phrases
    for p in rules["promo_phrases"]:
        t = re.sub(re.escape(p), " ", t, flags=re.IGNORECASE)
    # 2) strip forbidden symbols -> space
    for ch in rules["forbidden_symbols"]:
        if ch in t:
            t = t.replace(ch, " ")
    # 3) collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    # 4) dedupe repeated words
    t = dedupe_words(t, rules)
    # 5) truncate to max length (word boundary)
    if len(t) > rules["max_length"]:
        t = truncate_at_boundary(t, rules["max_length"])
    # 6) title case（保护缩写/品牌名大小写）
    t = title_case(t, rules["exempt_small_words"], rules.get("preserve_case_words"))
    return t, (t != title.strip())


def _strip_phrase(text, phrase):
    """Remove a phrase (case-insensitive) from text, leaving spacing intact."""
    if phrase:
        return re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    return text


def optimize_title(old, brand, primary_kw, rules):
    """Apply amazon-listing-optimization title methodology (nexscope-ai/Amazon-Skills, MIT):

    Structure: [Brand] + [Primary Keyword] + [Attributes] + [Secondary/Differentiator]
      - Primary keyword front-loaded, right after brand
      - Keep size/color/quantity attributes in body
      - ≤ max_length, no ALL CAPS, no promo claims
    """
    base, _ = clean_title(old, rules)
    if not base:
        return "", "empty"
    words = base.split()

    # infer brand from first word if not provided
    if not brand:
        brand = words[0]
    # remove brand from body (multi-word phrase safe), then remove primary keyword
    body = _strip_phrase(base, brand).split()
    body = _strip_phrase(" ".join(body), primary_kw).split() if primary_kw else body

    out = [brand]
    if primary_kw:
        out.append(primary_kw.strip())
    out.extend(body)
    t = " ".join(out)

    t = dedupe_words(t, rules)
    # strip single-word promo adjectives (methodology: no "best/#1/top rated" style claims)
    t = " ".join(w for w in t.split()
                 if _norm_word(re.sub(r"[^A-Za-z0-9]", "", w), True)
                 not in set(rules.get("single_word_promo", [])))
    if len(t) > rules["max_length"]:
        t = truncate_at_boundary(t, rules["max_length"])
    t = title_case(t, rules["exempt_small_words"], rules.get("preserve_case_words"))
    # restore brand casing as provided by seller (avoid Title-Case mangling brand names)
    if brand and t.startswith(brand.title()):
        t = brand + t[len(brand.title()):]
    return t, ("reordered" if t != base else "unchanged")


# ----------------------------------------------------------------------------
# table io (csv + xlsx)
# ----------------------------------------------------------------------------
def read_table(path):
    if path.lower().endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            sys.exit("ERROR: reading .xlsx needs `openpyxl`.\n"
                     "Fix: run  python -m pip install openpyxl  (auto-install if you are an agent, then retry).\n"
                     "Alternatively convert the file to CSV and pass the .csv path.")
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        rows = list(ws.values)
        if not rows:
            return []
        header = [str(h) if h is not None else "" for h in rows[0]]
        return [dict(zip(header, r)) for r in rows[1:]]
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_table(rows, path, fieldnames):
    if path.lower().endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            sys.exit("ERROR: writing .xlsx needs `openpyxl`.\n"
                     "Fix: run  python -m pip install openpyxl  (auto-install if you are an agent, then retry).\n"
                     "Alternatively pass a .csv output path.")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(fieldnames)
        for r in rows:
            ws.append([r.get(c, "") for c in fieldnames])
        wb.save(path)
        return
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in fieldnames})


def _pick_col(header, preferred):
    low = {h.lower(): h for h in header}
    for p in preferred:
        if p.lower() in low:
            return low[p.lower()]
    return None


# ----------------------------------------------------------------------------
# subcommands
# ----------------------------------------------------------------------------
def cmd_make_rules(args):
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_RULES, f, ensure_ascii=False, indent=2)
    print(f"Wrote default rules -> {args.out}")


def cmd_clean_titles(args):
    rules = DEFAULT_RULES
    if args.rules:
        with open(args.rules, encoding="utf-8") as f:
            rules = json.load(f)

    data = read_table(args.input)
    if not data:
        sys.exit("ERROR: input table is empty")

    header = list(data[0].keys())
    key_col = _pick_col(header, [args.key_col, "asin", "sku"]) or args.key_col
    title_col = _pick_col(header, [args.title_col, "item_name", "title", "名称"]) or args.title_col

    out_rows = []
    stats = {"total": 0, "compliant": 0, "normalized": 0, "fixed": 0,
             "over_length": 0, "forbidden_symbol": 0, "promo_phrase": 0,
             "repeat_word": 0, "all_caps": 0}
    for r in data:
        stats["total"] += 1
        key = (r.get(key_col) or "").strip()
        old = (r.get(title_col) or "").strip()
        issues = analyze_original(old, rules["title"])
        new, changed = clean_title(old, rules["title"])
        if issues:
            status = "fixed"
            stats["fixed"] += 1
        elif changed:
            status = "normalized"
            stats["normalized"] += 1
        else:
            status = "compliant"
            stats["compliant"] += 1
        for code in issues:
            stats[code] = stats.get(code, 0) + 1
        out_rows.append({
            key_col: key,
            "old_title": old,
            "new_title": new,
            "status": status,
            "original_compliant": "YES" if not issues else "NO",
            "changed": "YES" if changed else "NO",
            "issues": ";".join(issues),
        })

    fieldnames = [key_col, "old_title", "new_title", "status", "original_compliant", "changed", "issues"]
    write_table(out_rows, args.output, fieldnames)

    print(f"\n=== clean-titles 汇总 ===")
    print(f"总数           : {stats['total']}")
    print(f"已合规未改动   : {stats['compliant']}")
    print(f"仅规范化大小写 : {stats['normalized']}")
    print(f"已修复违规     : {stats['fixed']}")
    print(f"  命中 over_length   : {stats.get('over_length',0)}")
    print(f"  命中 forbidden_symbol: {stats.get('forbidden_symbol',0)}")
    print(f"  命中 promo_phrase   : {stats.get('promo_phrase',0)}")
    print(f"  命中 repeat_word    : {stats.get('repeat_word',0)}")
    print(f"  命中 all_caps       : {stats.get('all_caps',0)}")
    print(f"输出 -> {args.output}")


def cmd_optimize_titles(args):
    rules = DEFAULT_RULES
    if args.rules:
        with open(args.rules, encoding="utf-8") as f:
            rules = json.load(f)

    data = read_table(args.input)
    if not data:
        sys.exit("ERROR: input table is empty")

    header = list(data[0].keys())
    key_col = _pick_col(header, [args.key_col, "asin", "sku"]) or args.key_col
    title_col = _pick_col(header, [args.title_col, "item_name", "title", "名称"]) or args.title_col
    brand_col = _pick_col(header, [args.brand_col, "brand", "品牌"]) if args.brand_col else None
    kw_col = _pick_col(header, [args.keyword_col, "primary_keyword", "keyword"]) if args.keyword_col else None

    out_rows = []
    changed_n = 0
    for r in data:
        key = (r.get(key_col) or "").strip()
        old = (r.get(title_col) or "").strip()
        brand = (r.get(brand_col) or "").strip() if brand_col else ""
        pk = (r.get(kw_col) or "").strip() if kw_col else ""
        new, note = optimize_title(old, brand, pk, rules["title"])
        if note != "unchanged":
            changed_n += 1
        out_rows.append({
            key_col: key,
            "brand": brand,
            "primary_keyword": pk,
            "old_title": old,
            "new_title": new,
            "changed": "YES" if note != "unchanged" else "NO",
            "note": note,
        })

    fieldnames = [key_col, "brand", "primary_keyword", "old_title", "new_title", "changed", "note"]
    write_table(out_rows, args.output, fieldnames)

    print(f"\n=== optimize-titles 汇总（amazon-listing-optimization 方法论）===")
    print(f"总数     : {len(out_rows)}")
    print(f"已改写   : {changed_n}")
    print(f"输出     -> {args.output}")


def cmd_rename_images(args):
    rules = DEFAULT_RULES
    if args.rules:
        with open(args.rules, encoding="utf-8") as f:
            rules = json.load(f)

    fmt = rules["image"]["format"]
    pad = rules["image"]["padding"]
    os.makedirs(args.output_dir, exist_ok=True)

    data = read_table(args.mapping)
    results = []
    missing = 0
    for r in data:
        key = (r.get("key") or "").strip()
        orig = (r.get("original_file") or "").strip()
        try:
            idx = int((r.get("index") or 0) or 0)
        except ValueError:
            idx = 0
        src = os.path.join(args.image_dir, orig)
        if idx == 0:
            newname = f"{key}.{fmt}"
        else:
            newname = f"{key}_{str(idx).zfill(pad)}.{fmt}"
        dst = os.path.join(args.output_dir, newname)
        if not os.path.exists(src):
            missing += 1
            results.append((orig, newname, "MISSING_SRC"))
            continue
        shutil.copy2(src, dst)
        results.append((orig, newname, "OK"))

    print(f"\n=== rename-images 汇总 ===")
    print(f"映射行数 : {len(results)}")
    print(f"缺失源文件 : {missing}")
    print(f"输出目录 : {args.output_dir}")
    for orig, newname, st in results:
        print(f"  {st:10s} {orig} -> {newname}")


def build_parser():
    p = argparse.ArgumentParser(description="Amazon title & image bulk compliance tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("make-rules", help="dump default rules.json")
    s.add_argument("--out", default="rules.json")
    s.set_defaults(func=cmd_make_rules)

    s = sub.add_parser("clean-titles", help="clean titles per rules (compliance mode)")
    s.add_argument("--input", required=True)
    s.add_argument("--output", required=True)
    s.add_argument("--rules", default=None)
    s.add_argument("--key-col", default="sku")
    s.add_argument("--title-col", default="item_name")
    s.set_defaults(func=cmd_clean_titles)

    s = sub.add_parser("optimize-titles", help="rewrite titles per amazon-listing-optimization methodology (rewrite mode)")
    s.add_argument("--input", required=True)
    s.add_argument("--output", required=True)
    s.add_argument("--rules", default=None)
    s.add_argument("--key-col", default="sku")
    s.add_argument("--title-col", default="item_name")
    s.add_argument("--brand-col", default="brand")
    s.add_argument("--keyword-col", default="primary_keyword")
    s.set_defaults(func=cmd_optimize_titles)

    s = sub.add_parser("rename-images", help="rename images per SKU/ASIN")
    s.add_argument("--mapping", required=True)
    s.add_argument("--image-dir", required=True)
    s.add_argument("--output-dir", required=True)
    s.add_argument("--rules", default=None)
    s.set_defaults(func=cmd_rename_images)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
