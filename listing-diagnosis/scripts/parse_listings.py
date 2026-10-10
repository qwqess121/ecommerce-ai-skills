import json

INPUT = r'C:\Users\Administrator\.claude\projects\C--Users-Administrator-Desktop-2\8a15d32d-5211-4d90-979d-4c343baa6946\tool-results\mcp-LingXing-MCP-action-1790212252230.txt'

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['data']['data']['list']
total = data['data']['data']['total']

parents = {}
stores = set()
for item in items:
    st = item.get('status_text', '')
    if st != '在售':
        continue
    pa = item.get('parent_asin', '')
    mid = item.get('marketplace', '')
    shop = item.get('shop', '')
    stores.add(shop)
    key = pa + '|' + mid
    if key not in parents:
        parents[key] = {
            'parent_asin': pa,
            'child_asin': item.get('amz_product_id', ''),
            'marketplace': mid,
            'shop': shop,
            'brand': item.get('product_brand_text', '') or item.get('seller_brand', ''),
            'title': (item.get('item_name', '') or '')[:90],
            'price': item.get('price', ''),
            'rank': item.get('seller_rank', 0) or 999999,
            'reviews': item.get('reviews_num', 0),
            'principal': item.get('principal_realname', ''),
            'category': item.get('seller_category', []),
            'fulfillment': item.get('fulfillment_channel_type', ''),
            'children': 1
        }
    else:
        parents[key]['children'] += 1

print(f'Total listings in DB: {total} (this page: {len(items)})')
active = [it for it in items if it.get('status_text') == '在售']
print(f'Active in this page: {len(active)}')
print(f'Unique parent ASINs (active): {len(parents)}')
print(f'Stores: {sorted(stores)}')
print()

for i, (k, p) in enumerate(sorted(parents.items(), key=lambda x: x[1].get('rank', 999999))):
    cats = ', '.join(p['category']) if isinstance(p['category'], list) else str(p['category'])
    print(f"{i+1}. Parent={p['parent_asin']}  Mkt={p['marketplace']}  Shop={p['shop']}")
    print(f"   Brand={p['brand']}  BSR={p['rank']}  Reviews={p['reviews']}  Price=${p['price']}  Children={p['children']}  {p['fulfillment']}  Owner={p['principal']}")
    print(f"   Title: {p['title']}")
    print(f"   Cat: {cats}")
    print()
