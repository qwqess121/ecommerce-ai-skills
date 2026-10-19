import json, os, sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(_SKILL_ROOT, 'output', 'phase0_data.json')
OUT_PATH = os.path.join(_SKILL_ROOT, 'output', 'phase3_child_scan.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

children = data['children']
parents = {(p['parent_asin'], p['country']): p for p in data['parents']}

parent_children = {}
for c in children:
    key = (c['parent_asin'], c['country'])
    parent_children.setdefault(key, []).append(c)

alerts = []
stats = {'total_children': 0, 'out_of_stock': 0, 'low_stock': 0, 'price_anomaly': 0, 'fbm_listings': 0}

for key, siblings in parent_children.items():
    prices = [float(s['price']) for s in siblings if s.get('price') and float(s['price']) > 0]
    avg_price = sum(prices) / len(prices) if prices else 0

    for c in siblings:
        stats['total_children'] += 1
        child_alerts = []
        price = float(c.get('price', 0) or 0)
        fba_qty = int(c.get('fba_qty', 0) or 0)
        fulfillment = c.get('fulfillment', '')

        if fba_qty == 0 and 'FBA' in fulfillment.upper():
            child_alerts.append({'type': 'out_of_stock', 'severity': 'red', 'msg': 'FBA库存为0，已断货'})
            stats['out_of_stock'] += 1
        elif 0 < fba_qty < 10 and 'FBA' in fulfillment.upper():
            child_alerts.append({'type': 'low_stock', 'severity': 'yellow', 'msg': f'FBA库存仅{fba_qty}件，即将断货'})
            stats['low_stock'] += 1

        if price > 0 and avg_price > 0 and len(prices) > 1:
            deviation = abs(price - avg_price) / avg_price
            if deviation > 0.3:
                child_alerts.append({
                    'type': 'price_anomaly',
                    'severity': 'red' if deviation > 0.5 else 'yellow',
                    'msg': f'价格${price:.2f}偏离同父均价${avg_price:.2f} ({deviation*100:.0f}%)'
                })
                stats['price_anomaly'] += 1

        if 'MFN' in fulfillment.upper() or 'FBM' in fulfillment.upper():
            child_alerts.append({'type': 'fbm', 'severity': 'info', 'msg': '自发货(FBM)，非FBA配送'})
            stats['fbm_listings'] += 1

        if child_alerts:
            alerts.append({
                'child_asin': c['child_asin'],
                'parent_asin': c['parent_asin'],
                'country': c['country'],
                'shop': c.get('shop', ''),
                'brand': c.get('brand', ''),
                'title': c.get('title', '')[:60],
                'sku': c.get('sku', ''),
                'price': price,
                'fba_qty': fba_qty,
                'fulfillment': fulfillment,
                'alerts': child_alerts
            })

alerts.sort(key=lambda x: (
    -max((1 if a['severity'] == 'red' else 0) for a in x['alerts']),
    -max((1 if a['severity'] == 'yellow' else 0) for a in x['alerts']),
    x['country'], x['parent_asin']
))

output = {
    'stats': stats,
    'alert_count': len(alerts),
    'alerts': alerts
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(json.dumps(stats, indent=2))
print(f'\nTotal alerts: {len(alerts)}')
print(f'Saved to {OUT_PATH}')
