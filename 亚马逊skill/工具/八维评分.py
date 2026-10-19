"""八维评分 v2（官方标准，部分给分，不因缺项直接记 0）

用法：python -X utf8 八维评分.py <数据目录>
输入（数据目录内）：
  listing/listing_capture_all.json     amazon_listing_capture.js 输出（标题、五点、A+、图库数、视频占位）
  listing/asin_detail_6.json       卖家精灵 asin_detail（价格、评分、评论数、LQS、BSR、配送）
  images/analysis/main_<ASIN>.json      逐图分类；items[0] 为主图，含 main_class 字段
                                   main_class: pure_white / white_with_props / scene_or_color
输出：listing/score_8dim.json

主图 main_class 判定（《图片标准.md》第一、五节）：
  pure_white        纯白底、无道具                         → 主图 5 分
  white_with_props  白底，道具贴在产品旁（不在背景上）     → 主图 3 分（不合格典型，非红牌）
  scene_or_color    背景为场景、色块、渐变、灰底（红牌）   → 主图 0 分
"""
import json, statistics, sys
from pathlib import Path

BASE = Path(sys.argv[1])
cap = {r["asin"]: r for r in json.load(open(BASE / "listing" / "listing_capture_all.json", encoding="utf-8"))}
def _load_detail():
    """对象详情：优先 listing/asin_detail_6.json；没有时由 listing/detail/<ASIN>.json 与真竞品清单自动组成（本品 + 真竞品）。"""
    f6 = BASE / "listing" / "asin_detail_6.json"
    if f6.exists():
        return json.load(open(f6, encoding="utf-8"))["items"]
    own = json.load(open(BASE / "取数配置.json", encoding="utf-8"))["own"]
    tc = json.load(open(BASE / "candidates" / "true_competitors.json", encoding="utf-8"))["true_competitors"]
    items = {}
    for a in [own] + tc:
        d = json.load(open(BASE / "listing" / "detail" / f"{a}.json", encoding="utf-8"))["data"]
        items[a] = {k: d.get(k) for k in ("asin", "title", "brand", "price", "rating", "ratings", "lqs", "bsrRank", "coupon", "fulfillment", "sellers")}
    return items
DETAIL = _load_detail()
ORDER = list(DETAIL.keys())  # 第一个为本品
MED = statistics.median([DETAIL[a]["price"] for a in ORDER])
FORBIDDEN = set("!$?_{}^¬¦~#<>*")
PROMO = ["free shipping", "100% quality", "best seller", "top rated", "hot item", "high quality"]
# 头号词取自本品数据目录的取数配置（head_keyword），不得写死为其他产品的词
HEAD = (json.load(open(BASE / "取数配置.json", encoding="utf-8")).get("head_keyword") or "").lower()
TYPES = {"卖点": "卖点/信息", "信息": "卖点/信息", "场景": "场景/使用", "使用": "场景/使用", "尺寸": "尺寸参照", "对比": "对比"}
MAIN_PTS = {"pure_white": 5, "white_with_props": 3, "scene_or_color": 0}


def title_score(a):
    t = cap[a]["title"] or ""
    b = DETAIL[a]["brand"].lower()
    f80 = t[:80].lower()
    det = {"长度≤200": 3 if len(t) <= 200 else 0,
           "无禁用符号": 3 if not (set(t) & FORBIDDEN) else 0,
           "无促销语": 3 if not any(p in t.lower() for p in PROMO) else 0,
           "品牌在前80字符": 3 if b in f80 else 0,
           "头号词在前80字符": 3 if HEAD in f80 else 0}
    return sum(det.values()), det


def bullets_score(a):
    bl = cap[a]["bullets"] or []
    n = len(bl)
    lead = sum(1 for x in bl if ":" in x[:80])
    det = {"条数(5=5,4=3,其余1)": 5 if n >= 5 else (3 if n == 4 else 1),
           "每条≤500字符": 3 if bl and all(len(x) <= 500 for x in bl) else 1,
           "收益前置(小标题)": 3 if lead >= 4 else (1.5 if lead >= 2 else 0.5),
           "头号词嵌入": 4 if any(HEAD in x.lower() for x in bl) else 1.5}
    return sum(det.values()), det


def main_score(a):
    items = json.load(open(BASE / "images" / "analysis" / f"main_{a}.json", encoding="utf-8")).get("items", [])
    cls = items[0].get("main_class", "scene_or_color") if items else "scene_or_color"
    return MAIN_PTS[cls], {"主图类别": cls}


def gallery_score(a):
    items = json.load(open(BASE / "images" / "analysis" / f"main_{a}.json", encoding="utf-8")).get("items", [])
    n = cap[a]["imageCount"]
    v = cap[a]["videoCount"]
    kinds = " ".join(i.get("kind", "") for i in items[1:])
    covered = sorted({lab for k, lab in TYPES.items() if k in kinds})
    det = {"图库张数(≥7=4,6=3,其余1.5)": 4 if n >= 7 else (3 if n == 6 else 1.5),
           "视频占位(有=2)": 2 if v >= 1 else 0,
           f"附图类型(覆盖{len(covered)}/4,每类1分)": len(covered),
           "覆盖类型": covered}
    return min(det["图库张数(≥7=4,6=3,其余1.5)"] + det["视频占位(有=2)"] + len(covered), 10), det


def aplus_score(a):
    x = cap[a]["aplus"]
    det = {}
    det["A+存在(4)"] = 4 if x.get("present") else 0
    if x.get("textSource") == "dom_text":
        det["正文≥300字符(3),否则1.5"] = 3 if x["textLen"] >= 300 else 1.5
    else:
        det["图片型alt≥60字符(3),否则1.5"] = 3 if x["textLen"] >= 60 else 1.5
    det["A+图≥5张(3),1-4张(1.5)"] = 3 if x.get("imgCount", 0) >= 5 else (1.5 if x.get("imgCount", 0) >= 1 else 0)
    return min(sum(det.values()), 10), det


def desc_score(a):
    """产品描述模块不存在时，以 A+ 正文为描述的等效内容（描述 = A+ 文案的功能）"""
    x = cap[a]["aplus"]
    det = {"描述来源": "A+正文代替（页面无描述模块）" if x.get("present") else "无"}
    if x.get("textSource") == "dom_text":
        det["文案长度(≥300=6,否则3)"] = 6 if x["textLen"] >= 300 else 3
    else:
        det["图片型alt文案(≥60=4,否则2)"] = 4 if x["textLen"] >= 60 else 2
    det["头号词在文案中(2)"] = 2 if HEAD in (x.get("text") or "").lower() else 0.5
    det["结构(≥5图=2,1-4图=1)"] = 2 if x.get("imgCount", 0) >= 5 else (1 if x.get("imgCount", 0) >= 1 else 0)
    return min(sum(v for k, v in det.items() if isinstance(v, (int, float))), 10), det


def pricing_score(a):
    r = DETAIL[a]["price"] / MED
    pts = 10 if r <= 1.0 else (7 if r <= 1.15 else (4 if r <= 1.30 else 2))
    return pts, {"价格/中位数": round(r, 3), "中位数$": round(MED, 2), "优惠券": DETAIL[a].get("coupon") or "无"}


def reviews_score(a):
    r, c = DETAIL[a]["rating"], DETAIL[a]["ratings"]
    rp = 7 if r >= 4.5 else (6 if r >= 4.0 else (4 if r >= 3.5 else (2 if r >= 3.0 else 1)))
    cp = 8 if c >= 1000 else (6 if c >= 100 else (4 if c >= 50 else (2 if c >= 10 else 1)))
    return rp + cp, {"星级分": rp, "评论数分": cp}


def seo_score(a):
    t = (cap[a]["title"] or "").lower()
    bl = " ".join(cap[a]["bullets"] or []).lower()
    ap = (cap[a]["aplus"]["text"] or "").lower()
    det = {"标题(4)": 4 if HEAD in t else 0, "五点(3)": 3 if HEAD in bl else 0, "A+/描述(3)": 3 if HEAD in ap else 0}
    return sum(det.values()), det


out = {}
for a in ORDER:
    ts, td = title_score(a)
    bs, bd = bullets_score(a)
    ms, md = main_score(a)
    gs, gd = gallery_score(a)
    ps, pd = aplus_score(a)
    ds, dd = desc_score(a)
    prs, prd = pricing_score(a)
    rs, rd = reviews_score(a)
    ss, sd = seo_score(a)
    total = ts + bs + ms + gs + ps + ds + prs + rs + ss
    out[a] = {"brand": DETAIL[a]["brand"], "标题": ts, "五点": bs, "主图": ms, "附图与视频": gs, "A+": ps,
              "描述": ds, "定价": prs, "评论": rs, "SEO": ss, "总分": round(total, 1),
              "detail": {"标题": td, "五点": bd, "主图": md, "附图与视频": gd, "A+": pd, "描述": dd,
                         "定价": prd, "评论": rd, "SEO": sd}}
    print(f"{a} {DETAIL[a]['brand']:<11} 标题{ts:>4}/15 五点{bs:>4}/15 主图{ms}/5 附图视频{gs:>4}/10 "
          f"A+{ps:>4}/10 描述{ds:>4}/10 定价{prs:>2}/10 评论{rs:>2}/15 SEO{ss:>2}/10  总分{round(total,1)}/100")

(BASE / "listing" / "score_8dim.json").write_text(json.dumps({"median_price": MED, "scores": out}, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved listing/score_8dim.json")
