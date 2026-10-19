"""
Phase 5: Excel Report v3.1 — 8 Sheets with full data
Integrates: phase3_diagnosis_v3, ads_analysis, competitor_products, tk_product_details
"""
import json, os, sys
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("ERROR: pip install openpyxl")
    sys.exit(1)

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

def load_json(name):
    path = os.path.join(BASE, name)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

diag = load_json('phase3_diagnosis_v3.json')
ads_data = load_json('ads_analysis.json')
comp_products = load_json('competitor_products.json')
tk_details = load_json('tk_product_details.json')
tk_data = load_json('tiktok_data.json')
phase2_tk = load_json('phase2_tiktok_scores.json')
amz_scrape = load_json('amz_scrape_images.json')
tk_scrape = load_json('tk_scrape_details.json')
phase0 = load_json('phase0_data.json')

# Load asin_detail for badge info (auto-discover all asin_detail_*.json)
amz_details = {}
import glob
for fpath in sorted(glob.glob(os.path.join(BASE, 'asin_detail_*.json'))):
    data = load_json(os.path.basename(fpath))
    if data:
        items = data if isinstance(data, list) else data.get('results', [])
        for item in items:
            if 'error' not in item and item.get('asin'):
                amz_details[item['asin']] = item

if not diag:
    print("ERROR: phase3_diagnosis_v3.json not found")
    sys.exit(1)

# Build lookup maps
ads_map = {}
if ads_data:
    for r in ads_data.get('results', []):
        ads_map[r['asin']] = r

tk_detail_map = {}
if tk_details:
    for r in tk_details.get('results', []):
        tk_detail_map[str(r['product_id'])] = r

# Scraped image/A+ data
scrape_map = {}
if amz_scrape:
    for r in amz_scrape.get('results', []):
        if not r.get('error'):
            scrape_map[r['asin']] = r

tk_scrape_map = {}
if tk_scrape:
    for r in tk_scrape.get('results', []):
        if not r.get('error') and r.get('image_count', 0) > 0:
            tk_scrape_map[r['product_id']] = r

# Styles
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(name="Microsoft YaHei", size=11, bold=True, color="FFFFFF")
DATA_FONT = Font(name="Microsoft YaHei", size=10)
BOLD_FONT = Font(name="Microsoft YaHei", size=10, bold=True)
RED_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
LIGHT_BLUE = PatternFill(start_color="D6EAF8", end_color="D6EAF8", fill_type="solid")
ORANGE_FILL = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style="thin", color="D9D9D9"), right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"), bottom=Side(style="thin", color="D9D9D9"))
WRAP = Alignment(vertical="top", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center")

def setup_headers(ws, headers):
    for i, (name, width) in enumerate(headers, 1):
        c = ws.cell(row=1, column=i, value=name)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = THIN_BORDER
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[1].height = 28
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"

LINK_FONT = Font(name="Microsoft YaHei", size=10, color="0563C1", underline="single")

def wc(ws, row, col, value, font=DATA_FONT, fill=None, align=None, link=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font
    c.border = THIN_BORDER
    c.alignment = align or WRAP
    if fill:
        c.fill = fill
    if link:
        c.hyperlink = link
        c.font = LINK_FONT
    return c

def grade_fill(g):
    return {'A': GREEN_FILL, 'B': GREEN_FILL, 'C': YELLOW_FILL, 'D': RED_FILL}.get(g)

def score_fill(s):
    if s >= 85: return GREEN_FILL
    if s >= 70: return YELLOW_FILL
    return RED_FILL

wb = Workbook()
wb.remove(wb.active)

# ======================== Sheet 1: 诊断摘要 ========================
ws1 = wb.create_sheet("诊断摘要")
title_font = Font(name="Microsoft YaHei", size=16, bold=True, color="1F4E79")
sub_font = Font(name="Microsoft YaHei", size=12, bold=True)
stat_font = Font(name="Microsoft YaHei", size=11)

ws1.merge_cells("A1:F1")
ws1["A1"].value = f"AB America / HOOGALIFE Listing 诊断报告 v3.1 — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
ws1["A1"].font = title_font
ws1["A1"].alignment = CENTER
ws1.row_dimensions[1].height = 45

row = 3
amz_s = diag['amz_summary']
tk_s = diag['tk_summary']

ws1.cell(row=row, column=1, value="亚马逊诊断概览").font = sub_font
row += 1
for label, val in [
    ("诊断产品数(父ASIN)", amz_s['total']),
    ("有详情数据", amz_s['with_detail']),
    ("平均综合评分", amz_s['avg_score']),
    ("等级分布", f"A:{amz_s['grades']['A']}  B:{amz_s['grades']['B']}  C:{amz_s['grades']['C']}  D:{amz_s['grades']['D']}"),
    ("违规词检出数", amz_s['violations']),
    ("拼写错误检出数", amz_s['typos']),
]:
    ws1.cell(row=row, column=1, value=label).font = stat_font
    ws1.cell(row=row, column=2, value=val).font = stat_font
    row += 1

row += 1
ws1.cell(row=row, column=1, value="TikTok诊断概览").font = sub_font
row += 1
for label, val in [
    ("诊断商品数", tk_s['total']),
    ("平均综合评分", tk_s['avg_score']),
    ("28天总GMV", f"${tk_s.get('total_28d_gmv', 0):,.0f}"),
    ("等级分布", f"A:{tk_s['grades']['A']}  B:{tk_s['grades']['B']}  C:{tk_s['grades']['C']}  D:{tk_s['grades']['D']}"),
    ("违规词检出数", tk_s['violations']),
    ("拼写错误检出数", tk_s['typos']),
]:
    ws1.cell(row=row, column=1, value=label).font = stat_font
    ws1.cell(row=row, column=2, value=val).font = stat_font
    row += 1

row += 1
ws1.cell(row=row, column=1, value="广告分析概览").font = sub_font
row += 1
if ads_data:
    ads_with = ads_data.get('success', 0)
    ads_no = ads_data.get('no_ads', 0)
    over_reliant = sum(1 for r in ads_data.get('results', [])
                       if (r.get('traffic', {}).get('ad_pct') or 0) > 60)
    healthy = sum(1 for r in ads_data.get('results', [])
                  if (r.get('traffic', {}).get('organic_pct') or 0) > 80)
    for label, val in [
        ("分析ASIN数(US)", ads_data.get('total_asins', 0)),
        ("有广告数据", ads_with),
        ("无广告数据", ads_no),
        ("过度依赖广告(>60%)", over_reliant),
        ("自然流量健康(>80%)", healthy),
    ]:
        ws1.cell(row=row, column=1, value=label).font = stat_font
        c = ws1.cell(row=row, column=2, value=val)
        c.font = stat_font
        if label.startswith("过度") and val > 0:
            c.fill = RED_FILL
        row += 1

row += 1
ws1.cell(row=row, column=1, value="竞品分析概览").font = sub_font
row += 1
if comp_products and comp_products.get('categories'):
    _c = comp_products['categories']
    _sc = comp_products.get('success_categories') or sum(1 for v in _c.values() if v.get('products'))
    _tc = comp_products.get('total_categories') or len(_c)
    _tp = comp_products.get('total_products') or sum(len(v.get('products', [])) for v in _c.values())
    for label, val in [
        ("覆盖L3品类", f"{_sc} / {_tc}"),
        ("竞品产品总数", _tp),
    ]:
        ws1.cell(row=row, column=1, value=label).font = stat_font
        ws1.cell(row=row, column=2, value=val).font = stat_font
        row += 1

ws1.column_dimensions["A"].width = 28
ws1.column_dimensions["B"].width = 40

# ======================== Sheet 2: 亚马逊Listing诊断 ========================
AMZ_H = [
    ("国家", 6), ("平台", 8), ("店铺", 18), ("负责人", 12), ("ASIN", 14),
    ("品牌", 12), ("L3品类", 22), ("综合评分", 8), ("等级", 6),
    ("原标题", 55), ("修改标题", 55),
    ("五点描述建议", 60), ("主副图建议", 40), ("A+建议", 40),
    ("违规词", 30), ("错词", 20),
    ("BSR", 10), ("评分", 6), ("评论数", 8), ("LQS", 6),
    ("图片数", 6), ("有A+", 5), ("A+图片数", 7), ("A+模块", 18),
    ("有视频", 5), ("BS", 4), ("AC", 4),
    ("自然流量%", 10), ("广告流量%", 10), ("Campaign数", 10), ("广告策略", 45),
]

ws2 = wb.create_sheet("亚马逊Listing诊断")
setup_headers(ws2, AMZ_H)

for idx, item in enumerate(diag['amz_results'], 2):
    asin = item['asin']
    ad = ads_map.get(asin, {})
    traffic = ad.get('traffic', {})
    ad_struct = ad.get('ad_structure', {})
    organic_pct = traffic.get('organic_pct')
    ad_pct = traffic.get('ad_pct')
    campaigns = ad_struct.get('total_campaigns', 0)
    strategy = ad.get('strategy_detail', '') or ad.get('strategy', '')

    detail = amz_details.get(asin, {})
    badge = detail.get('badge', {}) if isinstance(detail.get('badge'), dict) else {}
    has_ebc = 'Y' if badge.get('ebc', 'N') == 'Y' else 'N'
    has_video = 'Y' if badge.get('video', 'N') == 'Y' else 'N'
    is_bs = 'Y' if badge.get('bestSeller', 'N') == 'Y' else ''
    is_ac = 'Y' if badge.get('amazonChoice', 'N') == 'Y' else ''

    # Scraped image/A+ data
    sc = scrape_map.get(asin, {})
    sc_img_count = sc.get('image_count', '-')
    sc_aplus = sc.get('aplus', {})
    sc_aplus_imgs = sc_aplus.get('image_count', '-') if sc_aplus.get('exists') else '-'
    sc_aplus_modules = ', '.join(sc_aplus.get('modules', [])) if sc_aplus.get('exists') else '-'

    vals = [
        item['country'], item['platform'], item['shop'], item['owner'], asin,
        item['brand'], item['l3_category'],
        item['total_score'], item['grade'],
        item['original_title'], item['optimized_title'],
        item['features_suggestion'], item['image_suggestion'], item['aplus_suggestion'],
        item['violation_words'], item['typo_words'],
        item['bsr'], item['rating'], item['reviews'], item['lqs'],
        sc_img_count, has_ebc, sc_aplus_imgs, sc_aplus_modules,
        has_video, is_bs, is_ac,
        f"{organic_pct:.1f}%" if organic_pct is not None else '-',
        f"{ad_pct:.1f}%" if ad_pct is not None else '-',
        campaigns if campaigns else '-',
        strategy,
    ]
    country_code = item['country']
    domain = 'amazon.com' if country_code == 'US' else 'amazon.ca'
    amz_link = f'https://www.{domain}/dp/{asin}'

    for col, val in enumerate(vals, 1):
        fill = None
        link = None
        if col == 5:
            link = amz_link
        if col == 8 and isinstance(val, (int, float)):
            fill = score_fill(val)
        elif col == 9:
            fill = grade_fill(val)
        elif col == 15 and val:
            fill = RED_FILL
        elif col == 21 and isinstance(val, int) and val < 7:
            fill = PatternFill(start_color="FFF2CC", fill_type="solid")
        elif col == 29 and isinstance(ad_pct, (int, float)) and ad_pct > 60:
            fill = RED_FILL
        elif col == 28 and isinstance(organic_pct, (int, float)) and organic_pct > 80:
            fill = GREEN_FILL
        wc(ws2, idx, col, val, fill=fill, link=link)

# ======================== Sheet 3: TikTok Listing诊断 ========================
TK_H = [
    ("国家", 6), ("平台", 8), ("店铺", 12), ("负责人", 12), ("产品ID", 20),
    ("综合评分", 8), ("等级", 6),
    ("原标题", 45), ("修改标题", 45),
    ("详情描述建议", 55), ("主副图建议", 40),
    ("图片数", 6), ("描述长度", 8),
    ("违规词", 30), ("错词", 20),
    ("28天销量", 10), ("28天GMV", 12), ("累计GMV", 12),
    ("达人数", 8), ("视频数", 8), ("评论数", 8), ("库存", 8),
    ("爆火指数", 8), ("评分", 6), ("佣金率", 8), ("付费推广", 6),
]

ws3 = wb.create_sheet("TikTok Listing诊断")
setup_headers(ws3, TK_H)

for idx, item in enumerate(diag['tk_results'], 2):
    pid = str(item['product_id'])
    tk_d = tk_detail_map.get(pid, {})
    raw = tk_d.get('raw_detail', {})
    product_raw = raw.get('product', {}) if isinstance(raw, dict) else {}

    gmv28 = item.get('day28_gmv', 0) or 0
    gmv_total = item.get('total_gmv', 0) or 0
    creator = item.get('creator_count', 0) or product_raw.get('linked_creator_count', 0) or 0
    video_count = tk_d.get('video_count', 0) or product_raw.get('linked_video_count', 0) or 0
    comm = item.get('commission_rate', None) or product_raw.get('commission_rate', None)

    review_count = item.get('review_count', 0) or 0
    stock_count = item.get('stock_count', 0) or 0
    viral_index = item.get('viral_index', 0) or 0
    has_paid = item.get('has_paid_promotion', False)
    prod_rating = item.get('product_rating', 0) or 0

    tk_sc = tk_scrape_map.get(pid, {})
    tk_img_count = tk_sc.get('image_count', '-')
    tk_desc_len = tk_sc.get('description_length', '-')

    vals = [
        item['country'], item['platform'], item['shop'], item['owner'], pid,
        item['total_score'], item['grade'],
        item['original_title'], item['optimized_title'],
        item['description_suggestion'], item['image_suggestion'],
        tk_img_count, tk_desc_len,
        item['violation_words'], item['typo_words'],
        item.get('day28_units_sold', 0),
        f"${gmv28:,.0f}" if gmv28 else '$0',
        f"${gmv_total:,.0f}" if gmv_total else '$0',
        creator if creator else 0,
        video_count if video_count else 0,
        review_count,
        stock_count,
        viral_index,
        prod_rating,
        f"{comm}%" if comm else '-',
        'Y' if has_paid else '',
    ]
    tk_link = f'https://www.tiktok.com/shop/pdp/{pid}'
    for col, val in enumerate(vals, 1):
        fill = None
        link = None
        if col == 5:
            link = tk_link
        if col == 6 and isinstance(val, (int, float)):
            fill = score_fill(val)
        elif col == 7:
            fill = grade_fill(val)
        elif col == 12 and isinstance(val, (int, float)) and val < 5:
            fill = YELLOW_FILL
        elif col == 14 and val:
            fill = RED_FILL
        wc(ws3, idx, col, val, fill=fill, link=link)

# ======================== Sheet 4 & 5: 亚马逊竞品（拆分为两个Sheet） ========================
COMP_H_BASE = [
    ("L3品类", 22), ("排名", 6), ("ASIN", 14), ("标题", 50),
    ("品牌", 14), ("价格", 8), ("月销量", 10), ("月销售额", 12),
    ("BSR", 10), ("评分", 6), ("评论数", 10),
    ("LQS", 6), ("卖家类型", 10),
]

def write_comp_sheet(ws, max_per_cat, exclude_own):
    """Write competitor products to sheet. exclude_own=True for Top5, False for Top20."""
    row_idx = 2
    if not comp_products or not comp_products.get('categories'):
        wc(ws, 2, 1, '竞品数据未采集')
        return
    for cat_name, cat_data in comp_products['categories'].items():
        products = cat_data.get('products', [])
        if cat_data.get('error') or not products:
            continue
        if exclude_own:
            filtered = [p for p in products if not p.get('is_own_brand', False)]
        else:
            filtered = list(products)
        show = filtered[:max_per_cat]
        if not show:
            continue
        ncols = ws.max_column or 13
        wc(ws, row_idx, 1, f"{cat_name} (Top{len(show)})", font=BOLD_FONT, fill=LIGHT_BLUE)
        for c in range(2, ncols + 1):
            wc(ws, row_idx, c, '', fill=LIGHT_BLUE)
        row_idx += 1
        for rank, prod in enumerate(show, 1):
            is_own = prod.get('is_own_brand', False)
            comp_asin = prod.get('asin', '')
            m_units = prod.get('units') or prod.get('monthly_units') or prod.get('totalUnits') or ''
            m_rev = prod.get('revenue') or prod.get('monthly_revenue') or prod.get('totalAmount') or ''
            vals = [
                '', rank, comp_asin,
                (prod.get('title', '') or '')[:60],
                prod.get('brand', ''), prod.get('price', ''),
                f"{m_units:,}" if isinstance(m_units, (int, float)) and m_units else ('-' if not m_units else m_units),
                f"${m_rev:,.0f}" if isinstance(m_rev, (int, float)) and m_rev else ('-' if not m_rev else m_rev),
                prod.get('bsr', prod.get('bsrRank', '')), prod.get('rating', ''),
                prod.get('ratings', ''), prod.get('lqs', ''),
                prod.get('sellerType', prod.get('fulfillment', '')),
            ]
            if not exclude_own:
                vals.append('Y' if is_own else '')
            comp_link = f'https://www.amazon.com/dp/{comp_asin}' if comp_asin else None
            for col, val in enumerate(vals, 1):
                fill = GREEN_FILL if is_own else None
                link = comp_link if col == 3 else None
                wc(ws, row_idx, col, val, fill=fill, link=link)
            row_idx += 1
        row_idx += 1

ws4 = wb.create_sheet("竞品-同外观Top5")
setup_headers(ws4, COMP_H_BASE)
write_comp_sheet(ws4, 5, exclude_own=True)

ws4b = wb.create_sheet("竞品-同场景品类前20")
setup_headers(ws4b, COMP_H_BASE + [("自有品牌", 8)])
write_comp_sheet(ws4b, 20, exclude_own=False)

# ======================== Sheet 5: TikTok竞品分析 ========================
TK_COMP_H = [
    ("L3品类", 18), ("排名", 6), ("商品ID", 20), ("标题", 45),
    ("店铺", 18), ("价格区间", 14),
    ("周GMV", 12), ("累计GMV", 12), ("达人数", 8), ("增长率%", 8), ("自有商品", 8),
]

ws5 = wb.create_sheet("TikTok竞品分析")
setup_headers(ws5, TK_COMP_H)

row_idx = 2
if phase2_tk and phase2_tk.get('category_top_selling'):
    own_shops = set()
    if tk_data:
        for sk in tk_data.get('shops', {}):
            shop_info = tk_data['shops'][sk]
            own_shops.add(shop_info.get('seller_id', ''))
            own_shops.add(sk.lower())

    for cat_key, products in phase2_tk['category_top_selling'].items():
        cat_display = cat_key.replace('_', ' ').title()
        wc(ws5, row_idx, 1, cat_display, font=BOLD_FONT, fill=LIGHT_BLUE)
        for c in range(2, 12):
            wc(ws5, row_idx, c, '', fill=LIGHT_BLUE)
        row_idx += 1

        for rank, prod in enumerate(products[:10], 1):
            shop_info = prod.get('shop', {})
            shop_name = shop_info.get('shop_name', '') if isinstance(shop_info, dict) else str(shop_info)
            shop_id = shop_info.get('shop_id', '') if isinstance(shop_info, dict) else ''
            is_own = 'Y' if shop_id in own_shops or shop_name.lower() in own_shops else ''
            growth = prod.get('units_sold_growth_rate_percent', None)

            tk_comp_pid = str(prod.get('product_id', ''))
            tk_comp_link = f'https://www.tiktok.com/shop/pdp/{tk_comp_pid}' if tk_comp_pid else None
            vals = [
                '', rank, tk_comp_pid, (prod.get('title', '') or '')[:50],
                shop_name, prod.get('price_display', ''),
                f"${prod.get('period_gmv', 0):,.0f}",
                f"${prod.get('total_gmv', 0):,.0f}",
                '', f"{growth:.1f}%" if growth is not None else '-', is_own,
            ]
            for col, val in enumerate(vals, 1):
                fill = GREEN_FILL if is_own == 'Y' else None
                link = tk_comp_link if col == 3 else None
                wc(ws5, row_idx, col, val, fill=fill, link=link)
            row_idx += 1
        row_idx += 1

# ======================== Sheet 7: 子ASIN运营附表 ========================
CHILD_H = [
    ("父ASIN", 14), ("子ASIN", 14), ("国家", 4), ("店铺", 18), ("品牌", 12),
    ("负责人", 14), ("SKU", 16), ("标题", 40), ("价格", 8),
    ("FBA库存", 10), ("配送方式", 8), ("BSR排名", 8), ("评论数", 8),
    ("价格异常", 10), ("库存预警", 10),
]

ws_child = wb.create_sheet("子ASIN运营附表")
setup_headers(ws_child, CHILD_H)

row_idx = 2
if phase0 and phase0.get('children'):
    children_list = phase0['children']
    from collections import defaultdict
    parent_prices = defaultdict(list)
    for ch in children_list:
        p = ch.get('price')
        if isinstance(p, (int, float)) and p > 0:
            parent_prices[ch.get('parent_asin', '')].append(p)
    parent_avg = {k: sum(v)/len(v) for k, v in parent_prices.items() if v}

    for ch in sorted(children_list, key=lambda x: (x.get('parent_asin',''), x.get('child_asin',''))):
        child_asin = ch.get('child_asin', '')
        parent_asin = ch.get('parent_asin', '')
        price = ch.get('price', '')
        fba_qty = ch.get('fba_qty', 0) or 0

        price_flag = ''
        price_fill_c = None
        if isinstance(price, (int, float)) and price > 0 and parent_asin in parent_avg:
            avg = parent_avg[parent_asin]
            deviation = abs(price - avg) / avg if avg > 0 else 0
            if deviation > 0.5:
                price_flag = f'偏差{deviation*100:.0f}%'
                price_fill_c = RED_FILL
            elif deviation > 0.3:
                price_flag = f'偏差{deviation*100:.0f}%'
                price_fill_c = YELLOW_FILL

        inv_flag = ''
        inv_fill_c = None
        fulfillment = ch.get('fulfillment', '')
        if fulfillment == 'FBA':
            if fba_qty == 0:
                inv_flag = '断货'
                inv_fill_c = RED_FILL
            elif fba_qty < 10:
                inv_flag = '低库存'
                inv_fill_c = YELLOW_FILL

        country = ch.get('country', '')
        domain = 'amazon.com' if country == 'US' else 'amazon.ca'
        child_link = f'https://www.{domain}/dp/{child_asin}' if child_asin else None

        vals = [
            parent_asin, child_asin, country,
            ch.get('shop', ''), ch.get('brand', ''), ch.get('owner', ''),
            ch.get('sku', ''), (ch.get('title', '') or '')[:50],
            f"${price:.2f}" if isinstance(price, (int, float)) else price,
            f"{fba_qty:,}" if isinstance(fba_qty, (int, float)) else fba_qty,
            fulfillment, ch.get('rank', ''), ch.get('reviews', ''),
            price_flag, inv_flag,
        ]
        for col, val in enumerate(vals, 1):
            fill = None
            link = child_link if col == 2 else None
            if col == 14:
                fill = price_fill_c
            elif col == 15:
                fill = inv_fill_c
            elif col == 10 and inv_fill_c:
                fill = inv_fill_c
            wc(ws_child, row_idx, col, val, fill=fill, link=link)
        row_idx += 1

if row_idx == 2:
    wc(ws_child, 2, 1, '(无子ASIN数据)')

# ======================== Sheet 8: 违规词&错词汇总 ========================
VIOL_H = [
    ("ASIN/商品ID", 18), ("平台", 8), ("国家/店铺", 14),
    ("类型", 8), ("违规词/错词", 18), ("类别/正确词", 25),
    ("严重程度", 8), ("出现位置", 8), ("原文上下文", 40), ("建议替换", 20),
]

ws6 = wb.create_sheet("违规词&错词汇总")
setup_headers(ws6, VIOL_H)

row_idx = 2
for v in diag.get('amz_violations', []):
    sev_fill = RED_FILL if v['severity'] == 'high' else YELLOW_FILL
    vals = [v['asin'], v['platform'], v['country'],
            '违规词', v['word'], v['category'][:30],
            v['severity'], v['location'], v['context'], v['replacement']]
    for col, val in enumerate(vals, 1):
        wc(ws6, row_idx, col, val, fill=sev_fill if col in (5, 7) else None)
    row_idx += 1

for v in diag.get('tk_violations', []):
    sev_fill = RED_FILL if v['severity'] == 'high' else YELLOW_FILL
    vals = [v['product_id'], v['platform'], v['shop'],
            '违规词', v['word'], v['category'][:30],
            v['severity'], v['location'], v['context'], v['replacement']]
    for col, val in enumerate(vals, 1):
        wc(ws6, row_idx, col, val, fill=sev_fill if col in (5, 7) else None)
    row_idx += 1

for t in diag.get('amz_typos', []):
    vals = [t['asin'], t['platform'], t['country'],
            '错词', t['wrong'], t['correct'],
            '-', t['location'], t['context'], t['correct']]
    for col, val in enumerate(vals, 1):
        wc(ws6, row_idx, col, val)
    row_idx += 1

for t in diag.get('tk_typos', []):
    vals = [t['product_id'], t['platform'], t['shop'],
            '错词', t['wrong'], t['correct'],
            '-', t['location'], t['context'], t['correct']]
    for col, val in enumerate(vals, 1):
        wc(ws6, row_idx, col, val)
    row_idx += 1

if row_idx == 2:
    wc(ws6, 2, 1, '(未检测到违规词或拼写错误)')

# ======================== Sheet 7: 广告分析&策略建议 ========================
ADS_H = [
    ("国家", 6), ("店铺", 18), ("ASIN", 14), ("品牌", 12), ("L3品类", 20),
    ("Campaign数", 10), ("SP", 5), ("SB", 5), ("SBV", 5),
    ("自然流量%", 10), ("广告流量%", 10), ("流量评分", 10),
    ("详细策略建议", 80),
]

ws7 = wb.create_sheet("广告分析&策略建议")
setup_headers(ws7, ADS_H)

row_idx = 2
if ads_data:
    amz_lookup = {}
    for item in diag['amz_results']:
        amz_lookup[item['asin']] = item

    for r in sorted(ads_data.get('results', []),
                    key=lambda x: -(x.get('traffic', {}).get('ad_pct') or 0)):
        asin = r['asin']
        amz_item = amz_lookup.get(asin, {})
        ad_struct = r.get('ad_structure', {})
        traffic = r.get('traffic', {})
        camp_types = ad_struct.get('campaign_types', {})

        organic = traffic.get('organic_pct')
        ad_pct = traffic.get('ad_pct')
        total_score = traffic.get('total_score')

        country = amz_item.get('country', 'US')
        domain = 'amazon.com' if country == 'US' else 'amazon.ca'
        ads_link = f'https://www.{domain}/dp/{asin}'

        vals = [
            country, amz_item.get('shop', r.get('shop', '')),
            asin, amz_item.get('brand', ''), amz_item.get('l3_category', ''),
            ad_struct.get('total_campaigns', 0),
            camp_types.get('SP', 0), camp_types.get('SB', 0), camp_types.get('SBV', 0),
            f"{organic:.1f}%" if organic is not None else '-',
            f"{ad_pct:.1f}%" if ad_pct is not None else '-',
            total_score if total_score is not None else '-',
            r.get('strategy_detail', '') or r.get('strategy', ''),
        ]
        for col, val in enumerate(vals, 1):
            fill = None
            link = ads_link if col == 3 else None
            if col == 11 and isinstance(ad_pct, (int, float)) and ad_pct > 60:
                fill = RED_FILL
            elif col == 10 and isinstance(organic, (int, float)) and organic > 80:
                fill = GREEN_FILL
            elif col == 6 and val == 0:
                fill = ORANGE_FILL
            wc(ws7, row_idx, col, val, fill=fill, link=link)
        row_idx += 1

# ======================== Sheet 8: 数据覆盖率 ========================
COV_H = [
    ("数据项", 30), ("覆盖数量", 10), ("总数", 10), ("覆盖率", 10), ("状态", 8), ("备注", 40),
]

ws8 = wb.create_sheet("数据覆盖率")
setup_headers(ws8, COV_H)

amz_total = amz_s['total']
amz_detail = amz_s['with_detail']
tk_total = tk_s['total']
tk_with_detail = len(tk_detail_map) if tk_details else 0
tk_with_creator = sum(1 for r in diag['tk_results'] if r.get('creator_count', 0))
if comp_products and comp_products.get('categories'):
    _cats = comp_products['categories']
    comp_success = comp_products.get('success_categories') or sum(1 for v in _cats.values() if v.get('products'))
    comp_total_cats = comp_products.get('total_categories') or len(_cats)
    comp_total_prods = comp_products.get('total_products') or sum(len(v.get('products', [])) for v in _cats.values())
else:
    comp_success = 0
    comp_total_cats = 24
    comp_total_prods = 0
ads_success = ads_data.get('success', 0) if ads_data else 0
ads_total = ads_data.get('total_asins', 92) if ads_data else 92

coverage = [
    ("亚马逊ASIN详情(标题+五点)", amz_detail, amz_total,
     f"{amz_detail/amz_total*100:.0f}%",
     "OK" if amz_detail/amz_total > 0.8 else "!",
     "卖酷asin_detail, 含features五点原文"),
    ("亚马逊图片(主图URL)", amz_detail, amz_total,
     f"{amz_detail/amz_total*100:.0f}%",
     "OK" if amz_detail/amz_total > 0.8 else "!",
     "卖酷asin_detail返回imageUrl"),
    ("亚马逊副图(采集)", len(scrape_map), amz_total,
     f"{len(scrape_map)/amz_total*100:.0f}%",
     "OK" if len(scrape_map)/amz_total > 0.8 else "P",
     f"Playwright采集, 平均{amz_scrape.get('avg_images',0) if amz_scrape else 0}张"),
    ("亚马逊A+(有无标记)", amz_detail, amz_total,
     f"{amz_detail/amz_total*100:.0f}%",
     "OK" if amz_detail/amz_total > 0.8 else "!",
     "卖酷asin_detail返回badge.ebc"),
    ("亚马逊A+模块(采集)", sum(1 for v in scrape_map.values() if v.get('aplus',{}).get('exists')), amz_total,
     f"{sum(1 for v in scrape_map.values() if v.get('aplus',{}).get('exists'))/amz_total*100:.0f}%",
     "OK" if sum(1 for v in scrape_map.values() if v.get('aplus',{}).get('exists')) > amz_total * 0.5 else "P",
     "Playwright采集A+图片数/文本量/模块类型"),
    ("亚马逊竞品明细", comp_success, comp_total_cats,
     f"{comp_success/comp_total_cats*100:.0f}%",
     "OK" if comp_success > 15 else "P",
     f"卖酷product_research, {comp_total_prods}个竞品产品"),
    ("TikTok商品基础数据(标题+GMV)", tk_total, tk_total,
     "100%", "OK", "FastMoss shop_product_analysis"),
    ("TikTok商品详情(描述+图片)", tk_with_detail, tk_total,
     f"{tk_with_detail/tk_total*100:.0f}%" if tk_total else "0%",
     "OK" if tk_with_detail == tk_total else "P",
     "FastMoss product_detail_info"),
    ("TikTok图片+描述(采集)", len(tk_scrape_map), tk_total,
     f"{len(tk_scrape_map)/tk_total*100:.0f}%" if tk_total else "0%",
     "OK" if len(tk_scrape_map)/tk_total > 0.8 else "P",
     f"HTTP采集, 平均{tk_scrape.get('avg_images',0) if tk_scrape else 0}张, 平均{tk_scrape.get('avg_desc_length',0) if tk_scrape else 0}字符描述"),
    ("TikTok达人数据", tk_with_creator, tk_total,
     f"{tk_with_creator/tk_total*100:.0f}%",
     "P" if tk_with_creator < tk_total else "OK",
     "FastMoss product_creator_analysis"),
    ("TikTok竞品(品类Top10)", 7, 7,
     "100%", "OK", "FastMoss product_rank_top_selling"),
    ("广告分析(Sif)", ads_success, ads_total,
     f"{ads_success/ads_total*100:.0f}%" if ads_total else "0%",
     "OK", f"Sif MCP, {ads_success}有广告 / {ads_data.get('no_ads',0) if ads_data else 0}无广告"),
    ("违规词检测", amz_total + tk_total, amz_total + tk_total,
     "100%", "OK", f"AMZ:{amz_s['violations']}条 + TK:{tk_s['violations']}条"),
    ("子ASIN运营数据", len(phase0.get('children', [])) if phase0 else 0,
     phase0.get('summary', {}).get('total_children', 0) if phase0 else 0,
     f"{len(phase0.get('children', []))/phase0.get('summary',{}).get('total_children',1)*100:.0f}%" if phase0 and phase0.get('summary',{}).get('total_children') else "0%",
     "OK" if phase0 and phase0.get('children') else "!",
     "领星ERP数据, 含价格/库存/配送/Buy Box"),
]

status_fill_map = {"OK": GREEN_FILL, "P": YELLOW_FILL, "!": RED_FILL}

for idx, (item, covered, total, rate, status, note) in enumerate(coverage, 2):
    vals = [item, covered, total, rate, status, note]
    for col, val in enumerate(vals, 1):
        c = wc(ws8, idx, col, val)
        if col == 5:
            c.fill = status_fill_map.get(val, GREEN_FILL)

# Save
out_path = os.path.join(BASE, f'Listing诊断报告v3.1_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx')
wb.save(out_path)
print(f'\nReport saved: {out_path}')
print(f'Sheets: {len(wb.sheetnames)}')
for name in wb.sheetnames:
    ws_tmp = wb[name]
    rows = ws_tmp.max_row - 1 if ws_tmp.max_row > 1 else 0
    print(f'  {name}: {rows} rows')
