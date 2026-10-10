import json

files = [
    r'C:\Users\Administrator\.claude\projects\C--Users-Administrator-Desktop-2\8a15d32d-5211-4d90-979d-4c343baa6946\tool-results\mcp-LingXing-MCP-action-1790212252230.txt',
    r'C:\Users\Administrator\.claude\projects\C--Users-Administrator-Desktop-2\8a15d32d-5211-4d90-979d-4c343baa6946\tool-results\mcp-LingXing-MCP-action-1790212955615.txt',
]

all_items = []
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        items = data.get('data', {}).get('data', {}).get('list', [])
        total = data.get('data', {}).get('data', {}).get('total', 0)
        all_items.extend(items)
        print(f'File: ...{f[-30:]}: {len(items)} items (total={total})')
    except Exception as e:
        print(f'Error: {e}')

print(f'\nTotal items loaded: {len(all_items)}')

parents = {}
cats_by_shop = {}
all_cats = set()
for item in all_items:
    if item.get('status_text') != '\u5728\u552e':
        continue
    pa = item.get('parent_asin', '')
    mid = item.get('marketplace', '')
    shop = item.get('shop', '')
    cat = item.get('seller_category', [])
    small_rank_cat = item.get('small_rank', '')
    if isinstance(cat, list):
        for c in cat:
            all_cats.add(c)
    if shop not in cats_by_shop:
        cats_by_shop[shop] = set()
    if isinstance(cat, list):
        for c in cat:
            cats_by_shop[shop].add(c)

    key = pa + '|' + mid
    if key not in parents:
        parents[key] = {
            'pa': pa,
            'mid': mid,
            'shop': shop,
            'brand': item.get('product_brand_text', '') or '',
            'title': (item.get('item_name', '') or '')[:80],
            'rank': item.get('seller_rank', 0) or 999999,
            'cat': cat,
            'small_rank': small_rank_cat,
            'owner': item.get('principal_realname', ''),
            'children': 1
        }
    else:
        parents[key]['children'] += 1

print(f'Active unique parent ASINs: {len(parents)}')
print(f'\nAll categories: {sorted(all_cats)}')

print('\n=== Categories by store ===')
for shop in sorted(cats_by_shop):
    print(f'  {shop}: {sorted(cats_by_shop[shop])}')

print(f'\n=== All {len(parents)} parent ASINs (by BSR) ===')
for i, (k, p) in enumerate(sorted(parents.items(), key=lambda x: x[1]['rank'])):
    c = ', '.join(p['cat']) if isinstance(p['cat'], list) else str(p['cat'])
    print(f"{i+1}. {p['pa']}  {p['mid']}  BSR={p['rank']}  {p['brand']}  [{p['shop']}]  ({p['children']}var)")
    print(f"   {p['title']}")
    print(f"   Cat: {c}  SmallRank: {p['small_rank']}  Owner: {p['owner']}")
