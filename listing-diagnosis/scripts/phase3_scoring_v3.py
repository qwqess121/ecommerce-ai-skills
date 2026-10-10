"""
Phase 3: 诊断评分 & 建议生成 (v3.0)
基于Phase 1采集的真实内容（标题+五点+图片+A+）生成诊断和修改建议
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(BASE, 'output')
REFS = os.path.join(BASE, 'references')

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load data
phase0 = load_json(os.path.join(OUTPUT, 'phase0_data.json'))
config = load_json(os.path.join(BASE, 'templates', 'report-config.json'))
amz_prohibited = load_json(os.path.join(REFS, 'amazon-prohibited-words.json'))
tk_prohibited = load_json(os.path.join(REFS, 'tiktok-prohibited-words.json'))
typos_data = load_json(os.path.join(REFS, 'common-typos.json'))
tk_data = load_json(os.path.join(OUTPUT, 'tiktok_data.json'))
tk_details_extra = load_json(os.path.join(OUTPUT, 'tk_product_details.json'))
amz_scrape = load_json(os.path.join(OUTPUT, 'amz_scrape_images.json'))
tk_scrape = load_json(os.path.join(OUTPUT, 'tk_scrape_details.json'))

# Build TK detail lookup
tk_detail_map = {}
if tk_details_extra:
    for r in tk_details_extra.get('results', []):
        tk_detail_map[str(r['product_id'])] = r

# Build scrape lookups
amz_scrape_map = {}
if amz_scrape:
    for r in amz_scrape.get('results', []):
        if not r.get('error'):
            amz_scrape_map[r['asin']] = r

tk_scrape_map = {}
if tk_scrape:
    for r in tk_scrape.get('results', []):
        if not r.get('error') and r.get('image_count', 0) > 0:
            tk_scrape_map[str(r['product_id'])] = r

# Load asin_detail files (auto-discover all asin_detail_*.json)
amz_details = {}
import glob
for fpath in sorted(glob.glob(os.path.join(OUTPUT, 'asin_detail_*.json'))):
    data = load_json(fpath)
    if data:
        items = data if isinstance(data, list) else data.get('results', [])
        for item in items:
            if 'error' not in item and item.get('asin'):
                amz_details[item['asin']] = item
print(f'Loaded asin_detail for {len(amz_details)} ASINs')

# Build prohibited word maps
def build_prohibited_map(prohibited_data):
    flat = {}
    replacements = {}
    if not prohibited_data:
        return flat, replacements
    for key, cat_data in prohibited_data.items():
        if key.startswith('_') or not isinstance(cat_data, dict):
            continue
        severity = cat_data.get('severity', 'medium')
        cat_name = cat_data.get('description', key)
        repl = cat_data.get('replacement_suggestions', {})
        for word in cat_data.get('words', []):
            wl = word.lower()
            flat[wl] = {'category': cat_name, 'severity': severity, 'original': word}
            if wl in repl or word in repl:
                replacements[wl] = repl.get(wl, repl.get(word, ''))
    return flat, replacements

amz_words, amz_replacements = build_prohibited_map(amz_prohibited)
tk_words, tk_replacements = build_prohibited_map(tk_prohibited)

# Build typo map
typo_map = {}
if typos_data:
    for section in ['common_typos', 'ecommerce_typos', 'unit_errors']:
        for entry in typos_data.get(section, []):
            typo_map[entry['wrong'].lower()] = entry['correct']

def check_prohibited(text, word_map, repl_map):
    found = []
    text_lower = text.lower()
    for word, info in word_map.items():
        if word in text_lower:
            idx = text_lower.index(word)
            ctx = text[max(0, idx-20):min(len(text), idx+len(word)+20)]
            found.append({
                'word': info['original'],
                'category': info['category'],
                'severity': info['severity'],
                'context': f'...{ctx}...',
                'replacement': repl_map.get(word, ''),
            })
    return found

def check_typos(text):
    found = []
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    for w in words:
        if w in typo_map:
            idx = text.lower().find(w)
            ctx = text[max(0, idx-15):min(len(text), idx+len(w)+15)]
            found.append({'wrong': w, 'correct': typo_map[w], 'context': f'...{ctx}...'})
    return found

def generate_title_suggestion(title, brand, category, features=None):
    """Generate optimized title based on current title + brand + category patterns"""
    if not title:
        return ''

    words = title.split()
    has_brand = brand and brand.lower() in title.lower()

    core_keywords = []
    if category:
        cat_words = category.lower().split()
        for cw in cat_words:
            if cw not in ['&', 'and', 'for', 'of', 'the', "women's", "men's"]:
                core_keywords.append(cw)

    feature_keywords = []
    if features:
        for f in features[:3]:
            first_words = f.split()[:3]
            feature_keywords.extend([w for w in first_words if len(w) > 3 and w.lower() not in ['with', 'this', 'that', 'from']])

    parts = []
    if brand and not has_brand:
        parts.append(brand)
    elif has_brand:
        brand_idx = title.lower().index(brand.lower())
        if brand_idx > 20:
            remaining = title[:brand_idx].strip().rstrip(',').rstrip('-')
            parts.append(brand)
            parts.append(remaining)
        else:
            parts.append(title[:80])
            return ' '.join(parts)

    if not parts:
        parts.append(brand or '')

    cat_part = category or ''
    if cat_part and cat_part.lower() not in title.lower():
        parts.append(cat_part)

    attrs = []
    for w in words:
        wl = w.lower().strip(',').strip('-')
        if wl not in [b.lower() for b in (parts + core_keywords)] and len(wl) > 2:
            if wl not in ['for', 'and', 'the', 'with', 'set', 'pack']:
                attrs.append(w.strip(',').strip('-'))
        if len(attrs) >= 6:
            break

    if attrs:
        parts.extend(attrs[:6])

    suggestion = ' '.join(parts)
    if len(suggestion) > 150:
        suggestion = suggestion[:147] + '...'
    if len(suggestion) < 50 and title:
        suggestion = title[:80]

    return suggestion

def analyze_features(features):
    """Analyze bullet points and generate improvement suggestions"""
    if not features or not isinstance(features, list):
        return '无五点描述数据，建议添加至少5条，每条以利益点开头'

    suggestions = []
    rufus_coverage = {'who': False, 'different': False, 'how': False}

    who_words = ['for', 'ideal for', 'perfect for', 'suitable', 'designed for', 'great for']
    diff_words = ['unique', 'unlike', 'different', 'exclusive', 'special', 'innovative', 'premium', 'upgraded']
    how_words = ['use', 'how to', 'simply', 'easy to', 'step', 'apply', 'install', 'just']

    for i, f in enumerate(features):
        fl = f.lower()
        for w in who_words:
            if w in fl:
                rufus_coverage['who'] = True
        for w in diff_words:
            if w in fl:
                rufus_coverage['different'] = True
        for w in how_words:
            if w in fl:
                rufus_coverage['how'] = True

        if len(f) > 500:
            suggestions.append(f'第{i+1}条过长({len(f)}字符>500)，精简至255字符内')
        elif len(f) < 30:
            suggestions.append(f'第{i+1}条过短({len(f)}字符)，补充具体卖点和细节')

    if len(features) < 5:
        suggestions.insert(0, f'仅{len(features)}条五点(建议5条)，补充缺少的条目')

    missing_rufus = []
    if not rufus_coverage['who']:
        missing_rufus.append('"适合谁"(Is this right for me?)')
    if not rufus_coverage['different']:
        missing_rufus.append('"有何不同"(What makes this different?)')
    if not rufus_coverage['how']:
        missing_rufus.append('"怎么用"(How do I use it?)')
    if missing_rufus:
        suggestions.append(f'缺少RUFUS三问覆盖: {", ".join(missing_rufus)}')

    first_words_ok = 0
    for f in features:
        first_word = f.split()[0].lower() if f.split() else ''
        benefit_starts = ['premium', 'easy', 'high', 'long', 'multi', 'safe', 'natural',
                          'professional', 'comfortable', 'durable', 'lightweight', 'versatile']
        if any(first_word.startswith(b) for b in benefit_starts):
            first_words_ok += 1
    if first_words_ok < len(features) // 2:
        suggestions.append('建议每条以利益点/卖点词开头(如Premium/Easy/Durable)')

    if not suggestions:
        return '五点描述质量良好，无需大改'

    return '; '.join(suggestions)

def analyze_images(detail, scrape_data=None):
    """Generate image improvement suggestions based on available data"""
    image_url = detail.get('imageUrl', '')
    has_video = detail.get('badge', {}).get('video', False) if isinstance(detail.get('badge'), dict) else False

    suggestions = []
    img_count = 0

    if scrape_data:
        img_count = scrape_data.get('image_count', 0)
        is_parent = scrape_data.get('is_parent_page', False)
        if is_parent:
            suggestions.append(f'父ASIN页面(变体选择页)，实际图片需查看子ASIN')
        elif img_count >= 7:
            suggestions.append(f'图片{img_count}张(达标)')
        elif img_count >= 5:
            suggestions.append(f'图片仅{img_count}张，建议补充至7+张')
        elif img_count > 0:
            suggestions.append(f'图片仅{img_count}张，严重不足，需补充至7+张')
        else:
            suggestions.append('无副图数据')

        aplus = scrape_data.get('aplus', {})
        if aplus.get('exists'):
            a_imgs = aplus.get('image_count', 0)
            modules = aplus.get('modules', [])
            mod_str = '+'.join(modules[:4]) if modules else '未知模块'
            suggestions.append(f'A+已有({a_imgs}图, {mod_str})')
            if 'comparison_table' not in modules:
                suggestions.append('建议添加对比表模块')
            if 'brand_story' not in modules:
                suggestions.append('建议添加品牌故事模块')
    else:
        if not image_url:
            suggestions.append('缺少主图，需立即上传白底主图')
        else:
            suggestions.append('有主图')
        suggestions.append('建议确保: 7+张图(主图白底+信息图+场景图+尺寸图+对比图+包装图)')

    if not has_video:
        suggestions.append('无视频，建议添加产品展示视频(提升转化率15-20%)')

    return '; '.join(suggestions), img_count

def analyze_aplus(detail):
    """Generate A+ content suggestions"""
    has_aplus = False
    badge = detail.get('badge', {})
    if isinstance(badge, dict):
        has_aplus = badge.get('ebc', 'N') == 'Y' or badge.get('aPlus', False)

    if not has_aplus:
        return '无A+/EBC内容 → 建议添加: 品牌故事模块+产品对比表+FAQ模块+使用场景图+成分/材质说明。Premium A+可加视频模块'
    else:
        return '已有A+/EBC内容。建议优化: 品牌故事(提升品牌认知) + 对比表(vs竞品) + FAQ(减少退货) + 场景大图 + 成分/工艺说明。争取7+模块'

# ============ Process Amazon ASINs ============
print('Processing Amazon ASINs...')
amz_results = []
amz_violations = []
amz_typos_found = []

if phase0:
    # Build store lookup
    store_lookup = {}
    if config:
        for store in config.get('amazon_stores', []):
            for asin_info in store.get('asin_list', []):
                pass  # We'll match by store differently

    for parent in phase0.get('parents', []):
        asin = parent['parent_asin']
        country = parent['country']
        shop = parent['shop']
        owner = parent.get('owner', '')
        brand = parent.get('brand', '')
        l3_cat = parent.get('l3_category', '')

        detail = amz_details.get(asin, {})
        has_detail = bool(detail)

        title = detail.get('title', parent.get('title', ''))
        features = detail.get('features', [])
        price = detail.get('price', parent.get('price', 0))
        bsr = detail.get('bsr', 0)
        rating = detail.get('rating', 0)
        reviews = detail.get('ratings', 0)
        lqs = detail.get('lqs', 0)
        variations = detail.get('variations', parent.get('variations', 0))
        if isinstance(variations, list):
            variations = len(variations)

        sc = amz_scrape_map.get(asin)

        # Generate suggestions — even without detail, give useful advice
        optimized_title = generate_title_suggestion(title, brand, l3_cat, features)
        if has_detail:
            features_suggestion = analyze_features(features)
            image_suggestion, actual_img_count = analyze_images(detail, scrape_data=sc)
            aplus_suggestion = analyze_aplus(detail)
        else:
            cat_hint = f'"{l3_cat}"品类' if l3_cat else '该品类'
            features_suggestion = (f'建议五点描述覆盖RUFUS三问: '
                                   f'1)"适合谁"({cat_hint}目标人群+使用场景) '
                                   f'2)"有何不同"(核心差异化卖点vs竞品) '
                                   f'3)"怎么用"(使用方法/安装步骤)。'
                                   f'每条以利益点开头，长度150-255字符，嵌入{cat_hint}核心关键词')
            image_suggestion, actual_img_count = analyze_images({}, scrape_data=sc)
            if sc:
                sc_aplus = sc.get('aplus', {})
                if sc_aplus.get('exists'):
                    a_imgs = sc_aplus.get('image_count', 0)
                    modules = sc_aplus.get('modules', [])
                    aplus_suggestion = f'已有A+({a_imgs}图, {"+".join(modules[:3]) if modules else "未知"})'
                    if 'comparison_table' not in modules:
                        aplus_suggestion += '; 建议添加对比表(vs竞品差异化)'
                    if 'brand_story' not in modules:
                        aplus_suggestion += '; 建议添加品牌故事(提升品牌认知)'
                else:
                    aplus_suggestion = f'无A+内容 → 建议为{cat_hint}添加: 品牌故事+对比表+FAQ+场景大图+成分说明'
            else:
                aplus_suggestion = (f'建议添加A+内容: 品牌故事模块 + 产品对比表(vs竞品3-5项) + '
                                    f'FAQ模块(3-5个常见问题) + 使用场景大图 + 成分/材质说明。'
                                'Premium A+可加视频模块和交互式图表')

        # Check violations on all text
        full_text = title
        if features:
            full_text += ' ' + ' '.join(features)
        violations = check_prohibited(full_text, amz_words, amz_replacements)
        violation_words = ', '.join(set(v['word'] for v in violations)) if violations else ''

        # Check typos
        typos = check_typos(full_text)
        typo_words = ', '.join(set(f"{t['wrong']}→{t['correct']}" for t in typos)) if typos else ''

        # Collect for dedicated sheets
        for v in violations:
            loc = '标题' if v['word'].lower() in title.lower() else '五点描述'
            amz_violations.append({
                'asin': asin, 'platform': 'Amazon', 'country': country,
                'word': v['word'], 'category': v['category'], 'severity': v['severity'],
                'location': loc, 'context': v['context'], 'replacement': v['replacement'],
            })
        for t in typos:
            loc = '标题' if t['wrong'].lower() in title.lower() else '五点描述'
            amz_typos_found.append({
                'asin': asin, 'platform': 'Amazon', 'country': country,
                'wrong': t['wrong'], 'correct': t['correct'],
                'location': loc, 'context': t['context'],
            })

        # Simple scoring
        score = 100
        issues = []

        # Title scoring
        if not title:
            score -= 20
            issues.append('标题缺失')
        else:
            if len(title) > 200:
                score -= 5
                issues.append(f'标题过长({len(title)}字符)')
            elif len(title) < 50:
                score -= 3
                issues.append(f'标题过短({len(title)}字符)')
            if brand and brand.lower() not in title.lower()[:30]:
                score -= 2
                issues.append('品牌未在标题前30字符')

        # Features scoring
        if not features:
            score -= 10
            issues.append('无五点描述数据')
        else:
            if len(features) < 5:
                score -= 5
                issues.append(f'仅{len(features)}条五点')
            long_bullets = [f for f in features if len(f) > 500]
            if long_bullets:
                score -= 2
                issues.append(f'{len(long_bullets)}条五点过长')

        # Image scoring (use actual scraped count when available)
        if sc and not sc.get('is_parent_page'):
            if actual_img_count == 0:
                score -= 10
                issues.append('无图片')
            elif actual_img_count < 5:
                score -= 8
                issues.append(f'图片严重不足({actual_img_count}张<5)')
            elif actual_img_count < 7:
                score -= 4
                issues.append(f'图片不足({actual_img_count}张<7)')
        elif not detail.get('imageUrl'):
            score -= 10
            issues.append('无主图')

        badge = detail.get('badge', {})
        if isinstance(badge, dict):
            if badge.get('video', 'N') != 'Y' and not (sc and sc.get('has_video')):
                score -= 3
                issues.append('无视频')
            if badge.get('ebc', 'N') != 'Y':
                sc_aplus = sc.get('aplus', {}) if sc else {}
                if not sc_aplus.get('exists'):
                    score -= 10
                    issues.append('无A+/EBC内容')
            if badge.get('bestSeller', 'N') == 'Y':
                score += 3
            if badge.get('amazonChoice', 'N') == 'Y':
                score += 2

        # Violations
        high_viols = [v for v in violations if v['severity'] == 'high']
        if high_viols:
            score -= min(10, len(high_viols) * 5)
            issues.append(f'{len(high_viols)}个高危违规词')

        # LQS scoring
        if lqs and lqs < 70:
            score -= 5
            issues.append(f'LQS偏低({lqs})')

        score = max(0, score)
        grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 55 else 'D'

        amz_results.append({
            'country': country,
            'platform': 'Amazon',
            'shop': shop,
            'owner': owner,
            'asin': asin,
            'brand': brand,
            'l3_category': l3_cat,
            'total_score': score,
            'grade': grade,
            'original_title': title,
            'optimized_title': optimized_title,
            'features_suggestion': features_suggestion,
            'image_suggestion': image_suggestion,
            'aplus_suggestion': aplus_suggestion,
            'violation_words': violation_words,
            'typo_words': typo_words,
            'bsr': bsr,
            'rating': rating,
            'reviews': reviews,
            'lqs': lqs,
            'price': price,
            'variations': variations,
            'has_detail': has_detail,
            'issues': issues,
        })

amz_results.sort(key=lambda x: x['total_score'])
amz_grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
for r in amz_results:
    amz_grades[r['grade']] += 1

print(f'  AMZ: {len(amz_results)} ASINs, avg={sum(r["total_score"] for r in amz_results)/len(amz_results):.1f}')
print(f'  Grades: {amz_grades}')
print(f'  Violations: {len(amz_violations)}, Typos: {len(amz_typos_found)}')

# ============ Process TikTok Products ============
print('\nProcessing TikTok products...')
tk_results = []
tk_violations = []
tk_typos_found = []

if tk_data:
    for shop_key, shop_data in tk_data.get('shops', {}).items():
        shop_owner = ''
        if config:
            for ts in config.get('tiktok_shops', []):
                if ts.get('shop_key', '') == shop_key or shop_key in ts.get('seller_id', ''):
                    shop_owner = ts.get('owner', '')

        for prod in shop_data.get('products', []):
            product_id = str(prod.get('product_id', ''))
            title = prod.get('title', '')

            cat = prod.get('category', {})
            l3_name = ''
            if cat:
                l3_info = cat.get('l3', {})
                l3_name = l3_info.get('name', '')

            # Merge FastMoss product_detail_info data
            tk_extra = tk_detail_map.get(product_id, {})
            tk_raw = tk_extra.get('raw_detail', {})
            tk_product_info = tk_raw.get('product', {}) if isinstance(tk_raw, dict) else {}
            has_tk_detail = bool(tk_extra)

            extra_video_count = tk_extra.get('video_count', 0) or tk_product_info.get('linked_video_count', 0) or 0
            extra_creator_count = tk_product_info.get('linked_creator_count', 0) or 0
            extra_review_count = tk_product_info.get('review_count', 0) or 0
            extra_stock = tk_product_info.get('stock_count', 0) or 0
            extra_viral = tk_product_info.get('viral_index', 0) or 0
            extra_commission = tk_product_info.get('commission_rate_percent', None)
            extra_is_off_shelf = tk_product_info.get('is_off_shelf', False)
            extra_has_paid = tk_product_info.get('has_paid_promotion', False)
            extra_cover = tk_extra.get('images', [])
            has_cover = tk_extra.get('image_count', 0) > 0

            # Merge scraped data (actual images + description from page)
            tk_sc = tk_scrape_map.get(product_id, {})
            scraped_img_count = tk_sc.get('image_count', 0)
            scraped_desc = tk_sc.get('description', '')
            scraped_desc_len = tk_sc.get('description_length', 0)

            # Generate title suggestion
            optimized_title = generate_title_suggestion(title, '', l3_name)

            # Description suggestion — real analysis based on title + scraped description
            desc_parts = []
            if scraped_desc_len > 0:
                desc_parts.append(f'当前描述{scraped_desc_len}字符')
                if scraped_desc_len < 500:
                    desc_parts.append('描述偏短，建议扩充至500+字符')
                elif scraped_desc_len > 3000:
                    desc_parts.append('描述较长，注意移动端阅读体验')
            if title:
                if len(title) > 100:
                    desc_parts.append(f'标题较长({len(title)}字符)，详情描述可精简重复信息')
                key_attrs = []
                attr_words = ['ml', 'oz', 'pack', 'set', 'pcs', 'inch', 'cm', 'count']
                for w in title.split():
                    wl = w.lower().strip(',-()[]')
                    if any(a in wl for a in attr_words):
                        key_attrs.append(w.strip(',-()[]'))
                if key_attrs:
                    desc_parts.append(f'规格属性({", ".join(key_attrs[:3])})应在描述首段突出')
            desc_parts.append('建议描述结构: 1)核心卖点(前2行抓眼球) 2)产品规格/成分 3)使用方法 4)适用场景/人群 5)售后保障')
            if l3_name:
                desc_parts.append(f'嵌入品类关键词"{l3_name}"及相关长尾词')
            desc_parts.append('使用短段落+emoji分隔提升移动端阅读体验')
            desc_suggestion = '; '.join(desc_parts)

            # Image suggestion — specific advice based on actual scraped data
            img_parts = []
            cat_hint = f'"{l3_name}"' if l3_name else '该品类'
            if scraped_img_count > 0:
                if scraped_img_count >= 8:
                    img_parts.append(f'图片{scraped_img_count}张(充足)，确保包含: 主图+信息图+场景图+成分/材质+包装')
                elif scraped_img_count >= 5:
                    img_parts.append(f'图片{scraped_img_count}张(达标)，建议补充至8+张: 增加使用场景图、对比图、尺寸参考图')
                else:
                    img_parts.append(f'图片仅{scraped_img_count}张(不足)，建议补充至8+张: 主图+功效信息图+场景图+成分图+对比图+包装图')
            elif has_cover:
                img_parts.append('有封面图，建议上传5+张高质量详情图')
            else:
                img_parts.append('缺少图片，需立即上传: 主图(白底纯产品)+信息图+场景图+成分图+包装图')

            if extra_video_count > 0:
                img_parts.append(f'已有{extra_video_count}个关联视频(好)')
            else:
                img_parts.append(f'无关联视频，建议为{cat_hint}产品拍摄开箱/使用教程短视频，或联系达人产出内容')

            if scraped_desc_len > 0 and scraped_desc_len < 500:
                img_parts.append(f'描述仅{scraped_desc_len}字符，建议补充产品卖点、使用方法、适用人群至500+字符')
            img_suggestion = '; '.join(img_parts)

            # Violations — check title + scraped description
            full_text = title + (' ' + scraped_desc if scraped_desc else '')
            violations = check_prohibited(full_text, tk_words, tk_replacements)
            violation_words = ', '.join(set(v['word'] for v in violations)) if violations else ''

            # Typos
            typos = check_typos(full_text)
            typo_words = ', '.join(set(f"{t['wrong']}→{t['correct']}" for t in typos)) if typos else ''

            for v in violations:
                loc = '标题' if v['word'].lower() in title.lower() else '描述'
                tk_violations.append({
                    'product_id': product_id, 'platform': 'TikTok', 'shop': shop_key,
                    'word': v['word'], 'category': v['category'], 'severity': v['severity'],
                    'location': loc, 'context': v['context'], 'replacement': v['replacement'],
                })
            for t in typos:
                loc = '标题' if t['wrong'].lower() in title.lower() else '描述'
                tk_typos_found.append({
                    'product_id': product_id, 'platform': 'TikTok', 'shop': shop_key,
                    'wrong': t['wrong'], 'correct': t['correct'],
                    'location': loc, 'context': t['context'],
                })

            # Scoring with real data
            score = 100
            issues = []

            if not title:
                score -= 25
                issues.append('标题缺失')
            elif len(title) < 50:
                score -= 5
                issues.append(f'标题过短({len(title)}字符)')
            elif len(title) > 128:
                score -= 3
                issues.append(f'标题过长({len(title)}字符>128)')

            high_viols = [v for v in violations if v['severity'] == 'high']
            if high_viols:
                score -= min(10, len(high_viols) * 5)
                issues.append(f'{len(high_viols)}个高危违规词')

            creator_count = prod.get('creator_count', 0) or extra_creator_count or 0
            if creator_count == 0:
                score -= 5
                issues.append('无达人推广')

            # Image scoring (use actual scraped count)
            if scraped_img_count > 0:
                if scraped_img_count < 3:
                    score -= 8
                    issues.append(f'图片严重不足({scraped_img_count}张<3)')
                elif scraped_img_count < 5:
                    score -= 4
                    issues.append(f'图片不足({scraped_img_count}张<5)')
            elif not has_cover:
                score -= 5
                issues.append('缺少封面图')

            # Description scoring (use scraped description length)
            if scraped_desc_len > 0:
                if scraped_desc_len < 200:
                    score -= 5
                    issues.append(f'描述过短({scraped_desc_len}字符)')
                elif scraped_desc_len < 500:
                    score -= 2
                    issues.append(f'描述偏短({scraped_desc_len}字符)')
            else:
                score -= 3
                issues.append('无描述内容')

            if extra_video_count == 0:
                score -= 5
                issues.append('无关联视频')

            if extra_review_count < 5:
                score -= 3
                issues.append(f'评论数少({extra_review_count})')

            if extra_is_off_shelf:
                score -= 10
                issues.append('商品已下架')

            if extra_stock == 0 and not extra_is_off_shelf:
                score -= 5
                issues.append('库存为0')

            if extra_viral >= 80:
                score += 3

            score = max(0, min(100, score))
            grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 55 else 'D'

            gmv28 = prod.get('day28_gmv', 0) or 0
            gmv_total = prod.get('total_gmv', 0) or tk_product_info.get('total_gmv', 0) or 0
            total_units = prod.get('total_units_sold', 0) or tk_product_info.get('total_units_sold', 0) or 0

            tk_results.append({
                'country': 'US',
                'platform': 'TikTok',
                'shop': shop_key,
                'owner': shop_owner,
                'product_id': product_id,
                'total_score': score,
                'grade': grade,
                'original_title': title[:200],
                'optimized_title': optimized_title,
                'description_suggestion': desc_suggestion,
                'image_suggestion': img_suggestion,
                'violation_words': violation_words,
                'typo_words': typo_words,
                'day28_units_sold': prod.get('day28_units_sold', 0),
                'day28_gmv': gmv28,
                'total_gmv': gmv_total,
                'total_units_sold': total_units,
                'creator_count': creator_count,
                'product_rating': prod.get('product_rating', 0) or tk_product_info.get('product_rating', 0) or 0,
                'commission_rate': prod.get('commission_rate', None) or extra_commission,
                'video_count': extra_video_count,
                'review_count': extra_review_count,
                'stock_count': extra_stock,
                'viral_index': extra_viral,
                'has_paid_promotion': extra_has_paid,
                'is_off_shelf': extra_is_off_shelf,
                'issues': issues,
            })

tk_results.sort(key=lambda x: -(x.get('day28_gmv') or 0))
tk_grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
for r in tk_results:
    tk_grades[r['grade']] += 1

print(f'  TK: {len(tk_results)} products, avg={sum(r["total_score"] for r in tk_results)/len(tk_results):.1f}')
print(f'  Grades: {tk_grades}')
print(f'  Violations: {len(tk_violations)}, Typos: {len(tk_typos_found)}')

# ============ Generate detailed ad strategies ============
print('\nGenerating detailed ad strategies...')
ads_raw = load_json(os.path.join(OUTPUT, 'ads_analysis.json'))

amz_lookup = {}
for r in amz_results:
    amz_lookup[r['asin']] = r

ads_results = []
if ads_raw:
    for r in ads_raw.get('results', []):
        asin = r['asin']
        amz_item = amz_lookup.get(asin, {})
        ad_struct = r.get('ad_structure', {})
        traffic = r.get('traffic', {})
        camp_types = ad_struct.get('campaign_types', {})
        total_camps = ad_struct.get('total_campaigns', 0)
        organic = traffic.get('organic_pct')
        ad_pct = traffic.get('ad_pct')
        total_score = traffic.get('total_score')

        brand = amz_item.get('brand', '')
        l3_cat = amz_item.get('l3_category', '')
        price_raw = amz_item.get('price', 0)
        price = float(price_raw) if isinstance(price_raw, (int, float)) else 10
        reviews = amz_item.get('reviews', 0) or 0
        bsr = amz_item.get('bsr', 0)
        lqs = amz_item.get('lqs', 0)
        grade = amz_item.get('grade', '')

        parts = []

        # Campaign structure analysis
        sp = camp_types.get('SP', 0)
        sb = camp_types.get('SB', 0)
        sbv = camp_types.get('SBV', 0)
        sd = camp_types.get('SD', 0)

        if total_camps == 0:
            parts.append(f'【无广告】建议立即开启: 1)SP自动广告(竞价建议${max(0.3, (price or 10)*0.05):.2f}-${max(0.5, (price or 10)*0.08):.2f})测试2周收集关键词数据')
            parts.append(f'2)SP手动精准匹配投放品类核心词3-5个')
            if reviews and reviews > 50:
                parts.append(f'3)已有{reviews}条评论，可同步开SB品牌广告抢占搜索顶部')
        else:
            if sp > 0 and sb == 0 and sbv == 0:
                parts.append(f'【仅SP {sp}个campaign】建议增加: 1)SB品牌广告(视频+标题，抢占搜索顶部banner)')
                if reviews and reviews > 30:
                    parts.append(f'2)SBV视频广告(利用{reviews}条评论的社交证明)')
            elif sp > 0 and sb > 0 and sbv == 0:
                parts.append(f'【SP{sp}+SB{sb}】建议增加SBV视频广告(视频内容展示产品使用场景，转化率通常高于图片广告20-30%)')
            elif total_camps > 5:
                parts.append(f'【{total_camps}个campaign(SP{sp}+SB{sb}+SBV{sbv})】结构完整')

        # Traffic mix analysis
        if organic is not None and ad_pct is not None:
            if ad_pct > 60:
                parts.append(f'⚠️自然流量仅{organic:.0f}%，广告依赖度过高({ad_pct:.0f}%)。建议: 1)优化Listing关键词覆盖提升自然排名 2)逐步降低高CPC词出价 3)增加长尾词投放降低ACOS')
            elif ad_pct > 30:
                parts.append(f'流量结构: 自然{organic:.0f}%/广告{ad_pct:.0f}%，比例正常。建议优化广告ACOS: 否定不相关搜索词，提升广告转化率')
            elif ad_pct > 0:
                parts.append(f'自然流量主导({organic:.0f}%)，广告占比{ad_pct:.0f}%。可适度增加广告预算扩大流量份额，特别是品类关键词')
            else:
                parts.append(f'纯自然流量({organic:.0f}%)。有campaign但无广告流量→检查广告状态是否暂停/预算耗尽/竞价过低')
        elif total_camps > 0:
            parts.append('有campaign但无流量数据→检查广告状态/预算/竞价')

        # Traffic score analysis
        if total_score is not None:
            if total_score < 5000:
                parts.append(f'总流量评分极低({total_score})，需多渠道引流: 站外Deal+社媒+Vine评论')
            elif total_score < 20000:
                parts.append(f'流量评分偏低({total_score})，建议加大核心关键词投放+优化listing转化率')

        # Listing quality based recommendations
        if grade in ('C', 'D'):
            parts.append(f'⚠️Listing质量{grade}级，建议先优化Listing再加大广告投入(低质量Listing广告转化率低)')
        if lqs and lqs < 70:
            parts.append(f'LQS仅{lqs}分，优化Listing质量可显著降低ACOS')

        strategy_detail = '; '.join(parts) if parts else '数据不足，建议开启SP自动广告测试'

        ads_results.append({
            'asin': asin,
            'shop': r.get('shop', amz_item.get('shop', '')),
            'ad_structure': ad_struct,
            'traffic': traffic,
            'strategy': r.get('strategy', ''),
            'strategy_detail': strategy_detail,
        })

    print(f'  Generated strategies for {len(ads_results)} ASINs')

# Save enriched ads
if ads_results:
    ads_enriched = {
        'total_asins': len(ads_results),
        'success': sum(1 for r in ads_results if r.get('traffic', {}).get('organic_pct') is not None),
        'no_ads': sum(1 for r in ads_results if r.get('ad_structure', {}).get('total_campaigns', 0) == 0),
        'results': ads_results,
    }
    ads_path = os.path.join(OUTPUT, 'ads_analysis.json')
    with open(ads_path, 'w', encoding='utf-8') as f:
        json.dump(ads_enriched, f, ensure_ascii=False, indent=1)
    print(f'  Saved enriched ads to {ads_path}')

# Save output
output = {
    'amz_summary': {
        'total': len(amz_results),
        'with_detail': sum(1 for r in amz_results if r['has_detail']),
        'avg_score': round(sum(r['total_score'] for r in amz_results) / len(amz_results), 1) if amz_results else 0,
        'grades': amz_grades,
        'violations': len(amz_violations),
        'typos': len(amz_typos_found),
    },
    'tk_summary': {
        'total': len(tk_results),
        'avg_score': round(sum(r['total_score'] for r in tk_results) / len(tk_results), 1) if tk_results else 0,
        'grades': tk_grades,
        'violations': len(tk_violations),
        'typos': len(tk_typos_found),
        'total_28d_gmv': sum(r.get('day28_gmv', 0) or 0 for r in tk_results),
    },
    'amz_results': amz_results,
    'tk_results': tk_results,
    'amz_violations': amz_violations,
    'tk_violations': tk_violations,
    'amz_typos': amz_typos_found,
    'tk_typos': tk_typos_found,
}

out_path = os.path.join(OUTPUT, 'phase3_diagnosis_v3.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(f'\nSaved to {out_path}')
