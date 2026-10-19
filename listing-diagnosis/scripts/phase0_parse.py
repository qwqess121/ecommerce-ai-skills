import json, glob, os, sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_SKILL_ROOT, 'templates', 'report-config.json')
BASE = os.path.join(_SKILL_ROOT, 'tool-results')  # 领星MCP原始数据目录，需手动指定
OUT_PATH = os.path.join(_SKILL_ROOT, 'output', 'phase0_data.json')

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

auto_rules = {r['small_rank_category']: r['amazon_l3'] for r in config['product_category_auto_mapping']['rules']}
l3_map = config['category_l3_mapping']['amazon']
own_brands = set(b.lower() for b in config['all_own_brands'])

files = sorted(glob.glob(os.path.join(BASE, 'mcp-LingXing-MCP-action-*.txt')))
print(f'Found {len(files)} LingXing result files', file=sys.stderr)

all_items = []
for f_path in files:
    try:
        with open(f_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        items = data.get('data', {}).get('data', {}).get('list', [])
        all_items.extend(items)
    except:
        pass

active = [it for it in all_items if it.get('status_text') == '\u5728\u552e']
print(f'Total active items: {len(active)}', file=sys.stderr)

parents = {}
children_data = []

for item in active:
    pa = item.get('parent_asin', '') or item.get('amz_product_id', '')
    child_asin = item.get('amz_product_id', '')
    mid = item.get('marketplace', '')
    shop_raw = item.get('shop', '') or ''
    brand = item.get('product_brand_text', '') or item.get('seller_brand', '') or ''
    owner = item.get('principal_realname', '') or ''
    price = item.get('price', 0) or 0
    rank = item.get('seller_rank', 0) or 0
    reviews = item.get('reviews_num', 0) or 0
    rating = item.get('seller_rating', 0) or 0
    title = (item.get('item_name', '') or '')[:200]
    sku = item.get('seller_sku', '') or ''
    fba_qty = item.get('afn_fulfillable_quantity', 0) or 0
    fulfillment = item.get('fulfillment_channel_type', '') or ''
    sr_raw = item.get('small_rank', '')

    country = 'US' if ('\u7f8e\u56fd' in mid or 'US' in mid) else 'CA' if ('\u52a0\u62ff\u5927' in mid or 'CA' in mid) else mid
    marketplace_id = 'ATVPDKIKX0DER' if country == 'US' else 'A2EUQ1WTGCTBG2'

    sr_cats = []
    if sr_raw and isinstance(sr_raw, str) and sr_raw.startswith('['):
        try:
            for s in json.loads(sr_raw):
                sr_cats.append(s.get('category', ''))
        except:
            pass
    elif sr_raw and isinstance(sr_raw, str):
        sr_cats.append(sr_raw)

    matched_l3 = None
    for sc in sr_cats:
        if sc in auto_rules:
            matched_l3 = auto_rules[sc]
            break
    if not matched_l3 and sr_cats:
        for sc in sr_cats:
            for rule_key in auto_rules:
                if rule_key.lower() in sc.lower() or sc.lower() in rule_key.lower():
                    matched_l3 = auto_rules[rule_key]
                    break
            if matched_l3:
                break

    child_rec = {
        'child_asin': child_asin,
        'parent_asin': pa,
        'country': country,
        'marketplace_id': marketplace_id,
        'shop': shop_raw,
        'brand': brand,
        'owner': owner,
        'title': title[:80],
        'sku': sku,
        'price': price,
        'fba_qty': fba_qty,
        'fulfillment': fulfillment,
        'rank': rank,
        'reviews': reviews,
    }
    children_data.append(child_rec)

    key = pa + '|' + country
    if key not in parents:
        node_paths = None
        if matched_l3 and matched_l3 in l3_map:
            node_paths = l3_map[matched_l3].get('nodeIdPaths', [None])[0]

        parents[key] = {
            'parent_asin': pa,
            'country': country,
            'marketplace_id': marketplace_id,
            'shop': shop_raw,
            'brand': brand,
            'owner': owner,
            'title': title,
            'price': price,
            'rank': rank,
            'reviews': reviews,
            'rating': rating,
            'matched_l3': matched_l3,
            'node_id_path': node_paths,
            'small_rank_cats': sr_cats,
            'child_count': 1,
            'total_fba_qty': fba_qty,
        }
    else:
        parents[key]['child_count'] += 1
        parents[key]['total_fba_qty'] += fba_qty

parent_list = sorted(parents.values(), key=lambda x: (x['country'], int(str(x.get('rank') or 999999).replace(',', ''))))

l3_groups = {}
for p in parent_list:
    l3 = p.get('matched_l3') or 'UNKNOWN'
    k = l3 + '|' + p['country']
    if k not in l3_groups:
        l3_groups[k] = {'l3': l3, 'country': p['country'], 'node_id_path': p.get('node_id_path'), 'asins': []}
    l3_groups[k]['asins'].append(p['parent_asin'])

us_count = sum(1 for p in parent_list if p['country'] == 'US')
ca_count = sum(1 for p in parent_list if p['country'] == 'CA')
matched = sum(1 for p in parent_list if p.get('matched_l3'))
unmatched = [p for p in parent_list if not p.get('matched_l3')]

print(f'Parent ASINs: {len(parent_list)} (US={us_count}, CA={ca_count})', file=sys.stderr)
print(f'L3 matched: {matched}, unmatched: {len(unmatched)}', file=sys.stderr)
print(f'L3 category+country groups: {len(l3_groups)}', file=sys.stderr)
print(f'Children records: {len(children_data)}', file=sys.stderr)

if unmatched:
    print(f'\nUnmatched ASINs:', file=sys.stderr)
    for p in unmatched:
        print(f"  {p['parent_asin']} {p['country']} [{p['brand']}] sr={p['small_rank_cats']}", file=sys.stderr)

output = {
    'summary': {
        'total_parents': len(parent_list),
        'us': us_count, 'ca': ca_count,
        'total_children': len(children_data),
        'l3_groups': len(l3_groups),
        'matched': matched, 'unmatched': len(unmatched),
    },
    'parents': parent_list,
    'children': children_data,
    'l3_groups': l3_groups,
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)
print(f'Saved to {OUT_PATH}', file=sys.stderr)
print(json.dumps(output['summary'], indent=2))
