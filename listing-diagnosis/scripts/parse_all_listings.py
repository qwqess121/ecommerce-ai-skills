import json, glob, os

BASE = r'C:\Users\Administrator\.claude\projects\C--Users-Administrator-Desktop-2\8a15d32d-5211-4d90-979d-4c343baa6946\tool-results'

files = sorted(glob.glob(os.path.join(BASE, 'mcp-LingXing-MCP-action-*.txt')))
print(f'Found {len(files)} result files')

all_items = []
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    items = data.get('data', {}).get('data', {}).get('list', [])
    total = data.get('data', {}).get('data', {}).get('total', 0)
    all_items.extend(items)
    print(f'  {os.path.basename(f)}: {len(items)} items (total={total})')

print(f'\nTotal items loaded: {len(all_items)}')

# Group by parent ASIN + marketplace
parents = {}
stores_info = {}
for item in all_items:
    st = item.get('status_text', '')
    if st != '在售':
        continue
    pa = item.get('parent_asin', '')
    mid_name = item.get('marketplace', '')
    shop = item.get('shop', '')
    key = pa + '|' + mid_name

    if shop not in stores_info:
        stores_info[shop] = {'brands': set(), 'categories': set(), 'principal': '', 'mid': mid_name}
    stores_info[shop]['brands'].add(item.get('product_brand_text', '') or '')
    cats = item.get('seller_category', [])
    if isinstance(cats, list):
        for c in cats:
            stores_info[shop]['categories'].add(c)
    stores_info[shop]['principal'] = item.get('principal_realname', '') or stores_info[shop]['principal']

    if key not in parents:
        parents[key] = {
            'parent_asin': pa,
            'child_asin': item.get('amz_product_id', ''),
            'marketplace': mid_name,
            'shop': shop,
            'brand': item.get('product_brand_text', '') or item.get('seller_brand', ''),
            'title': (item.get('item_name', '') or '')[:100],
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

print(f'Active unique parent ASINs: {len(parents)}')
print(f'Stores: {len(stores_info)}')
print()

# Print stores summary
print('=== STORES ===')
for shop, info in sorted(stores_info.items()):
    brands = ', '.join(sorted(b for b in info['brands'] if b))
    cats = ', '.join(sorted(info['categories']))
    print(f'  {shop} | Brands: {brands} | Cats: {cats} | Owner: {info["principal"]}')
print()

# Print all parent ASINs sorted by BSR
print('=== PARENT ASINs (sorted by BSR) ===')
for i, (k, p) in enumerate(sorted(parents.items(), key=lambda x: x[1].get('rank', 999999))):
    cats = ', '.join(p['category']) if isinstance(p['category'], list) else str(p['category'])
    print(f"{i+1}. {p['parent_asin']}  {p['marketplace']}  BSR={p['rank']}  Rev={p['reviews']}  ${p['price']}  {p['children']}var  {p['brand']}  {p['shop']}")
    print(f"   {p['title']}")
    print(f"   Cat: {cats}  Owner: {p['principal']}")
