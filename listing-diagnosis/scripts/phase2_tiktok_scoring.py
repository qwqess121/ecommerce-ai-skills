import json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK_DATA = os.path.join(BASE, 'output', 'tiktok_data.json')
REFS = os.path.join(BASE, 'references')
OUTPUT = os.path.join(BASE, 'output', 'phase2_tiktok_scores.json')

if not os.path.exists(TK_DATA):
    print(f'ERROR: {TK_DATA} not found', file=sys.stderr)
    sys.exit(1)

with open(TK_DATA, 'r', encoding='utf-8') as f:
    tk_data = json.load(f)

with open(os.path.join(REFS, 'tiktok-prohibited-words.json'), 'r', encoding='utf-8') as f:
    tk_prohibited_data = json.load(f)

with open(os.path.join(REFS, 'common-typos.json'), 'r', encoding='utf-8') as f:
    typos_data = json.load(f)

# Build prohibited words
prohibited_flat = {}
replacement_map = {}
for key, cat_data in tk_prohibited_data.items():
    if key.startswith('_') or not isinstance(cat_data, dict):
        continue
    severity = cat_data.get('severity', 'medium')
    cat_name = cat_data.get('description', key)
    replacements = cat_data.get('replacement_suggestions', {})
    for word in cat_data.get('words', []):
        wl = word.lower()
        prohibited_flat[wl] = {'category': cat_name, 'severity': severity, 'original': word}
        if wl in replacements or word in replacements:
            replacement_map[wl] = replacements.get(wl, replacements.get(word, ''))

typo_map = {}
for section in ['common_typos', 'ecommerce_typos', 'unit_errors']:
    for entry in typos_data.get(section, []):
        typo_map[entry['wrong'].lower()] = entry['correct']


def check_prohibited(text):
    found = []
    text_lower = text.lower()
    for word, info in prohibited_flat.items():
        if word in text_lower:
            idx = text_lower.index(word)
            context = text[max(0, idx - 20):min(len(text), idx + len(word) + 20)]
            replacement = replacement_map.get(word, '')
            found.append({
                'word': info['original'], 'category': info['category'],
                'severity': info['severity'], 'context': f'...{context}...',
                'replacement': replacement,
            })
    return found


def check_typos(text):
    found = []
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    for w in words:
        if w in typo_map:
            idx = text.lower().index(w)
            context = text[max(0, idx - 15):min(len(text), idx + len(w) + 15)]
            found.append({'wrong': w, 'correct': typo_map[w], 'context': f'...{context}...'})
    return found


def score_tk_title(title):
    score = 25
    issues = []
    suggestions = []
    severity_items = []

    if not title:
        return 0, ['[Critical] 标题缺失'], ['添加完整标题'], [('critical', '标题缺失')]

    length = len(title)
    if length > 200:
        score -= 3
        issues.append(f'标题过长({length}字符>200)')
    elif length < 50:
        score -= 5
        issues.append(f'标题过短({length}字符<50)，TikTok建议80-128字符')
        suggestions.append('补充关键词和卖点，目标80-128字符')
        severity_items.append(('warning', f'标题仅{length}字符'))

    first_3_words = ' '.join(title.split()[:3]).lower()
    core_patterns = ['perfume', 'fragrance', 'pheromone', 'air freshener', 'pest', 'repell', 'cologne']
    has_core_in_front = any(kw in first_3_words for kw in core_patterns)
    if not has_core_in_front and length > 30:
        score -= 5
        issues.append('核心关键词未在前3个词位置(TikTok搜索权重衰减)')
        suggestions.append('将核心品类词放在标题最前面，品牌名后置')

    prohibited = check_prohibited(title)
    high = [p for p in prohibited if p['severity'] == 'high']
    if high:
        score -= min(8, len(high) * 4)
        issues.append(f'[Critical] 高危违规词: {", ".join(p["word"] for p in high[:3])}')
        severity_items.extend([('critical', f'标题含"{p["word"]}"') for p in high[:2]])
    medium = [p for p in prohibited if p['severity'] == 'medium']
    if medium:
        score -= min(3, len(medium))
        issues.append(f'中等风险词: {", ".join(p["word"] for p in medium[:3])}')

    typos = check_typos(title)
    if typos:
        score -= 2
        issues.append(f'拼写: {"; ".join(f"{t["wrong"]}→{t["correct"]}" for t in typos[:3])}')

    return max(0, score), issues, suggestions, severity_items


def score_tk_compliance(title):
    score = 15
    issues = []
    suggestions = []
    severity_items = []

    prohibited = check_prohibited(title)
    high = [p for p in prohibited if p['severity'] == 'high']
    medium = [p for p in prohibited if p['severity'] == 'medium']

    if high:
        score -= min(10, len(high) * 5)
        for p in high[:5]:
            issues.append(f'[Critical] "{p["word"]}" ({p["category"][:30]})')
            if p.get('replacement'):
                suggestions.append(f'"{p["word"]}" → {p["replacement"]}')
        severity_items.extend([('critical', f'TK违规词"{p["word"]}"') for p in high[:2]])
    if medium:
        score -= min(5, len(medium) * 2)
        for p in medium[:3]:
            issues.append(f'[Warning] "{p["word"]}"')

    return max(0, score), issues, suggestions, severity_items


def score_tk_competitor(product, category_top):
    score = 15
    issues = []
    suggestions = []
    severity_items = []

    gmv_28 = product.get('day28_gmv', 0) or 0
    units_28 = product.get('day28_units_sold', 0) or 0

    if category_top:
        top_gmvs = [p.get('period_gmv', 0) or 0 for p in category_top[:10]]
        if top_gmvs:
            median_gmv = sorted(top_gmvs)[len(top_gmvs) // 2]
            if median_gmv > 0 and gmv_28 < median_gmv * 0.1:
                score -= 5
                issues.append(f'28天GMV ${gmv_28:.0f} 远低于品类Top10中位数 ${median_gmv:.0f}')
                severity_items.append(('warning', 'GMV远低于品类'))
            elif median_gmv > 0 and gmv_28 < median_gmv * 0.3:
                score -= 3
                issues.append(f'28天GMV偏低(品类Top10中位${median_gmv:.0f})')

    price = product.get('price', 0) or product.get('floor_price', 0) or 0
    if category_top and price > 0:
        top_prices = [p.get('floor_price', 0) or 0 for p in category_top[:10] if p.get('floor_price', 0)]
        if top_prices:
            avg_price = sum(top_prices) / len(top_prices)
            if price > avg_price * 1.3:
                score -= 3
                issues.append(f'价格${price:.2f}高于品类Top10均价${avg_price:.2f} (+{(price/avg_price-1)*100:.0f}%)')

    creators = product.get('creator_count', 0) or 0
    if creators == 0:
        score -= 3
        issues.append('无达人推广(达人数=0)')
        suggestions.append('开通联盟佣金，招募达人带货')
        severity_items.append(('warning', '无达人推广'))

    return max(0, score), issues, suggestions, severity_items


# Build category top selling lookup
category_top = {}
for cat_key, products in tk_data.get('category_top_selling', {}).items():
    if isinstance(products, list):
        category_top[cat_key] = products

# Score all TikTok products
results = []
all_violations = []
all_typos_found = []
severity_counts = {'critical': 0, 'warning': 0, 'info': 0}

for shop_key, shop_data in tk_data.get('shops', {}).items():
    for prod in shop_data.get('products', []):
        title = prod.get('title', '')
        product_id = prod.get('product_id', '')
        l3_name = ''
        l3_key = ''
        cat = prod.get('category', {})
        if cat:
            l3_info = cat.get('l3', {})
            l3_name = l3_info.get('name', '')
            l3_key = l3_name.lower().replace("'", '').replace(' ', '_') if l3_name else ''

        cat_top = category_top.get(l3_key, []) if l3_key else []

        t_score, t_issues, t_sugg, t_sev = score_tk_title(title)

        # Description scoring (we don't have desc text from shop_product_analysis)
        desc_score = 12  # default - need product_detail_info for full scoring
        desc_issues = ['需调用product_detail_info获取描述文本进行详细评分']

        # Image scoring (we don't have image count from shop_product_analysis)
        img_score = 12
        img_issues = ['需调用product_detail_info获取图片数进行详细评分']

        comp_score, comp_issues, comp_sugg, comp_sev = score_tk_compliance(title)
        spell_score, spell_issues, spell_sugg = 5, [], []
        typos = check_typos(title)
        if typos:
            spell_score -= min(5, len(typos) * 2)
            for t in typos[:3]:
                spell_issues.append(f'{t["wrong"]} → {t["correct"]}')

        bench_score, bench_issues, bench_sugg, bench_sev = score_tk_competitor(prod, cat_top)

        total = t_score + desc_score + img_score + comp_score + spell_score + bench_score

        if total >= 85:
            grade = 'A'
        elif total >= 70:
            grade = 'B'
        elif total >= 55:
            grade = 'C'
        else:
            grade = 'D'

        all_sev = t_sev + comp_sev + bench_sev
        for sev_type, _ in all_sev:
            severity_counts[sev_type] = severity_counts.get(sev_type, 0) + 1

        # Collect violations
        violations = check_prohibited(title)
        for v in violations:
            all_violations.append({
                'product_id': product_id, 'shop': shop_key, 'platform': 'TikTok',
                'word': v['word'], 'category': v['category'], 'severity': v['severity'],
                'location': '标题', 'context': v['context'],
                'replacement': v.get('replacement', ''),
            })

        for t in typos:
            all_typos_found.append({
                'product_id': product_id, 'shop': shop_key, 'platform': 'TikTok',
                'wrong': t['wrong'], 'correct': t['correct'],
                'location': '标题', 'context': t['context'],
            })

        # Build diagnosis
        diag_parts = []
        if t_issues:
            diag_parts.append('[标题] ' + '; '.join(t_issues))
        if desc_issues:
            diag_parts.append('[描述] ' + '; '.join(desc_issues))
        if comp_issues:
            diag_parts.append('[合规] ' + '; '.join(comp_issues))
        if spell_issues:
            diag_parts.append('[拼写] ' + '; '.join(spell_issues))
        if bench_issues:
            diag_parts.append('[竞品] ' + '; '.join(bench_issues))

        priority_fixes = []
        if comp_score < 10:
            priority_fixes.append('🔴违规词清理')
        if t_score < 18:
            priority_fixes.append('🟡标题优化')
        if bench_score < 10:
            priority_fixes.append('🟡提升达人/视频覆盖')

        growth_rate = prod.get('units_sold_growth_rate_percent', None)

        results.append({
            'product_id': product_id,
            'shop': shop_key,
            'title': (title or '')[:200],
            'l3_category': l3_name,
            'price': prod.get('price', 0),
            'price_display': prod.get('price_display', ''),
            'sku_count': prod.get('sku_count', 0),
            'day28_units_sold': prod.get('day28_units_sold', 0),
            'day28_gmv': prod.get('day28_gmv', 0),
            'day90_gmv': prod.get('day90_gmv', 0),
            'day90_units_sold': prod.get('day90_units_sold', 0),
            'total_gmv': prod.get('total_gmv', 0),
            'total_units_sold': prod.get('total_units_sold', 0),
            'product_rating': prod.get('product_rating', 0),
            'growth_rate': growth_rate,
            'commission_rate': prod.get('commission_rate', None),
            'launch_time': prod.get('launch_time', None),
            'creator_count': prod.get('creator_count', 0),
            'video_count': prod.get('video_count', 0),
            'total_score': total,
            'grade': grade,
            'dimensions': {
                'title': {'score': t_score, 'max': 25, 'issues': t_issues},
                'description': {'score': desc_score, 'max': 20, 'issues': desc_issues},
                'images': {'score': img_score, 'max': 20, 'issues': img_issues},
                'compliance': {'score': comp_score, 'max': 15, 'issues': comp_issues},
                'spelling': {'score': spell_score, 'max': 5, 'issues': spell_issues},
                'competitor': {'score': bench_score, 'max': 15, 'issues': bench_issues},
            },
            'priority_fixes': priority_fixes,
            'detailed_diagnosis': ' | '.join(diag_parts),
        })

results.sort(key=lambda x: -(x.get('day28_gmv') or 0))

grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
for r in results:
    grade_counts[r['grade']] += 1

summary = {
    'total_products': len(results),
    'shops': list(set(r['shop'] for r in results)),
    'grade_distribution': grade_counts,
    'avg_score': round(sum(r['total_score'] for r in results) / len(results), 1) if results else 0,
    'total_28d_gmv': sum(r.get('day28_gmv', 0) or 0 for r in results),
    'total_28d_units': sum(r.get('day28_units_sold', 0) or 0 for r in results),
    'total_gmv': sum(r.get('total_gmv', 0) or 0 for r in results),
    'severity_counts': severity_counts,
    'total_violations': len(all_violations),
    'total_typos': len(all_typos_found),
}

output = {
    'summary': summary,
    'scores': results,
    'violations': all_violations,
    'typos': all_typos_found,
    'category_top_selling': {k: v[:10] for k, v in category_top.items()},
}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(json.dumps(summary, indent=2, ensure_ascii=False))
print(f'\nTikTok violations: {len(all_violations)}, typos: {len(all_typos_found)}')
print(f'Saved to {OUTPUT}')
