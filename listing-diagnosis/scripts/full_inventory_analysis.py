import json, glob, os, collections

BASE = r'C:\Users\Administrator\.claude\projects\C--Users-Administrator-Desktop-2\8a15d32d-5211-4d90-979d-4c343baa6946\tool-results'
files = sorted(glob.glob(os.path.join(BASE, 'mcp-LingXing-MCP-action-*.txt')))
print(f'Found {len(files)} LingXing result files')

all_items = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            raw = fh.read()
        data = json.loads(raw)
        items = data.get('data', {}).get('data', {}).get('list', [])
        total = data.get('data', {}).get('data', {}).get('total', 0)
        all_items.extend(items)
    except Exception as e:
        print(f'  Skip {os.path.basename(f)}: {e}')

print(f'Total raw items loaded: {len(all_items)}')

active = [it for it in all_items if it.get('status_text') == '在售']
print(f'Active items: {len(active)}')

# Deduplicate by parent_asin + marketplace
parents = {}
stores = {}
owners = {}
brands_all = set()
categories_top = collections.Counter()
small_rank_cats = collections.Counter()
country_count = collections.Counter()

for item in active:
    pa = item.get('parent_asin', '') or item.get('amz_product_id', '')
    mid = item.get('marketplace', '')
    shop_raw = item.get('shop', '')
    shop = shop_raw.split(' ')[0] if shop_raw else ''
    brand = item.get('product_brand_text', '') or item.get('seller_brand', '') or ''
    owner_str = item.get('principal_realname', '') or ''
    cat_list = item.get('seller_category', [])
    sr_raw = item.get('small_rank', '')

    # Parse small_rank JSON
    sr_cats = []
    if sr_raw and isinstance(sr_raw, str) and sr_raw.startswith('['):
        try:
            sr_data = json.loads(sr_raw)
            for s in sr_data:
                sr_cats.append(s.get('category', ''))
                small_rank_cats[s.get('category', '')] += 1
        except:
            pass
    elif sr_raw and isinstance(sr_raw, str):
        small_rank_cats[sr_raw] += 1

    if isinstance(cat_list, list):
        for c in cat_list:
            categories_top[c] += 1

    # Country
    if '美国' in mid or 'US' in mid:
        country_count['US'] += 1
    elif '加拿大' in mid or 'CA' in mid:
        country_count['CA'] += 1
    else:
        country_count[mid] += 1

    # Store
    if shop not in stores:
        stores[shop] = {'brands': set(), 'categories': set(), 'small_rank_cats': set(), 'owners': set(), 'country': mid, 'parent_count': 0, 'child_count': 0}
    stores[shop]['brands'].add(brand)
    if isinstance(cat_list, list):
        for c in cat_list:
            stores[shop]['categories'].add(c)
    for sc in sr_cats:
        stores[shop]['small_rank_cats'].add(sc)
    if owner_str:
        for o in owner_str.split(','):
            stores[shop]['owners'].add(o.strip())
    stores[shop]['child_count'] += 1

    brands_all.add(brand)

    key = pa + '|' + mid
    if key not in parents:
        parents[key] = {
            'parent_asin': pa,
            'child_asin': item.get('amz_product_id', ''),
            'marketplace': mid,
            'shop': shop,
            'brand': brand,
            'title': (item.get('item_name', '') or '')[:120],
            'price': item.get('price', ''),
            'rank': item.get('seller_rank', 0) or 999999,
            'reviews': item.get('reviews_num', 0) or 0,
            'owner': owner_str,
            'category': cat_list,
            'small_rank_cats': sr_cats,
            'fulfillment': item.get('fulfillment_channel_type', ''),
            'children': 1,
            'afn_qty': item.get('afn_fulfillable_quantity', 0) or 0
        }
        stores[shop]['parent_count'] += 1
    else:
        parents[key]['children'] += 1
        parents[key]['afn_qty'] += item.get('afn_fulfillable_quantity', 0) or 0

print(f'\nUnique parent ASINs (active): {len(parents)}')
print(f'Unique stores: {len(stores)}')
print(f'Unique brands: {sorted(b for b in brands_all if b)}')

# Country breakdown
print(f'\n=== COUNTRY BREAKDOWN (child ASINs) ===')
for c, cnt in country_count.most_common():
    print(f'  {c}: {cnt}')

# Store summary
print(f'\n=== STORES ({len(stores)}) ===')
for shop in sorted(stores.keys()):
    info = stores[shop]
    brands = ', '.join(sorted(b for b in info['brands'] if b))
    cats = ', '.join(sorted(info['categories']))
    sr = ', '.join(sorted(info['small_rank_cats']))
    ow = ', '.join(sorted(info['owners'])) or '(无)'
    print(f'  {shop}')
    print(f'    国家: {info["country"]} | Parent ASIN: {info["parent_count"]} | Child ASIN: {info["child_count"]}')
    print(f'    品牌: {brands}')
    print(f'    负责人: {ow}')
    print(f'    顶级品类: {cats}')
    print(f'    子品类(small_rank): {sr}')

# Top-level categories
print(f'\n=== TOP-LEVEL CATEGORIES ===')
for cat, cnt in categories_top.most_common():
    print(f'  {cat}: {cnt} child ASINs')

# Small rank categories (L3/L4)
print(f'\n=== SMALL RANK CATEGORIES (L3/L4 subcategories) ===')
for cat, cnt in small_rank_cats.most_common():
    print(f'  {cat}: {cnt} child ASINs')

# All parent ASINs sorted by BSR (top 50)
print(f'\n=== TOP 50 PARENT ASINs (by BSR) ===')
sorted_parents = sorted(parents.values(), key=lambda x: int(str(x.get('rank', 999999)).replace(',', '') or '999999'))
for i, p in enumerate(sorted_parents[:50]):
    sr = ', '.join(p['small_rank_cats']) if p['small_rank_cats'] else '(无)'
    print(f"{i+1}. {p['parent_asin']}  {p['marketplace']}  BSR={p['rank']}  Rev={p['reviews']}  ${p['price']}  {p['children']}var  {p['brand']}  [{p['shop']}]  Owner={p['owner']}")
    print(f"   SmallRank: {sr}")

# Print all parent ASINs (full list)
print(f'\n=== ALL {len(parents)} PARENT ASINs ===')
for i, p in enumerate(sorted_parents):
    sr = ', '.join(p['small_rank_cats']) if p['small_rank_cats'] else '(无)'
    cats = ', '.join(p['category']) if isinstance(p['category'], list) else str(p['category'])
    print(f"{i+1}. {p['parent_asin']}|{p['marketplace']}|BSR={p['rank']}|Rev={p['reviews']}|${p['price']}|{p['children']}var|{p['brand']}|{p['shop']}|{p['owner']}|Cat:{cats}|SR:{sr}|FBA_qty:{p['afn_qty']}")

# Summary stats
print(f'\n=== SUMMARY ===')
us_parents = [p for p in parents.values() if '美国' in p['marketplace'] or 'US' in p['marketplace']]
ca_parents = [p for p in parents.values() if '加拿大' in p['marketplace'] or 'CA' in p['marketplace']]
print(f'Total parent ASINs: {len(parents)}')
print(f'  US: {len(us_parents)}')
print(f'  CA: {len(ca_parents)}')
print(f'Total child ASINs (active): {len(active)}')
print(f'Total stores: {len(stores)}')
print(f'Total unique brands: {len([b for b in brands_all if b])}')
print(f'Total top-level categories: {len(categories_top)}')
print(f'Total subcategories (small_rank): {len(small_rank_cats)}')
