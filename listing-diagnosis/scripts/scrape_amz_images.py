"""
Amazon product scraper: images + A+ content structure
Uses requests + regex (Playwright blocked by CAPTCHA)
"""
import json, os, sys, time, re
import requests

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def scrape_asin(session, asin, marketplace='us'):
    domain = 'amazon.com' if marketplace == 'us' else 'amazon.ca'
    url = f'https://www.{domain}/dp/{asin}'

    result = {
        'asin': asin,
        'marketplace': marketplace,
        'url': url,
        'images': [],
        'image_count': 0,
        'has_video': False,
        'aplus': {
            'exists': False,
            'modules': [],
            'module_count': 0,
            'has_brand_story': False,
            'has_comparison_table': False,
            'has_video': False,
            'image_count': 0,
            'text_length': 0,
        },
        'error': None,
    }

    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            result['error'] = f'HTTP {r.status_code}'
            return result

        html = r.text
        if len(html) < 5000 or 'captcha' in html.lower():
            result['error'] = 'CAPTCHA or blocked'
            return result

        # Extract initial variant images from colorImages parseJSON block
        idx = html.find("'initial'")
        if idx >= 0:
            m_pj = re.search(r"parseJSON\('(\[.*?\])'\)", html[idx:idx+50000], re.DOTALL)
            if m_pj:
                try:
                    items = json.loads(m_pj.group(1))
                    result['images'] = [it['hiRes'] for it in items if it.get('hiRes')]
                    result['image_source'] = 'colorImages_initial'
                except (json.JSONDecodeError, KeyError):
                    pass

        # Fallback: all hiRes (less precise, includes variant images)
        if not result['images']:
            hi_res = re.findall(r'"hiRes"\s*:\s*"(https://[^"]+)"', html)
            if hi_res:
                result['images'] = list(dict.fromkeys(hi_res))
                result['image_source'] = 'colorImages_all'
            else:
                large = re.findall(r'"large"\s*:\s*"(https://[^"]+)"', html)
                if large:
                    result['images'] = list(dict.fromkeys(large))
                    result['image_source'] = 'colorImages_large'

        # If only 1 image and initial had null hiRes, it's a parent/variant page
        if len(result['images']) <= 1:
            idx2 = html.find("'initial'")
            if idx2 >= 0:
                m_check = re.search(r"parseJSON\('(\[.*?\])'\)", html[idx2:idx2+50000], re.DOTALL)
                if m_check:
                    try:
                        items = json.loads(m_check.group(1))
                        null_count = sum(1 for it in items if it.get('hiRes') is None)
                        if null_count > 0 and len(items) <= 1:
                            result['is_parent_page'] = True
                    except (json.JSONDecodeError, KeyError):
                        pass

        result['image_count'] = len(result['images'])

        # Detect video
        if 'play-button-overlay' in html or '"videoCount"' in html or 'videoBlockIngress' in html:
            result['has_video'] = True

        # Extract A+ content - find the actual <div id="aplus_feature_div"> element
        aplus_div = re.search(r'<div[^>]+id=["\']aplus_feature_div["\'][^>]*>', html)
        if aplus_div:
            aplus_start = aplus_div.start()
            aplus_chunk = html[aplus_start:aplus_start+50000]

            # Count images (both src and data-src for lazy-loaded)
            src_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', aplus_chunk)
            lazy_imgs = re.findall(r'data-src=["\']([^"\']+)["\']', aplus_chunk)
            all_aplus_imgs = src_imgs + lazy_imgs
            all_aplus_imgs = [u for u in all_aplus_imgs if 'amazon' in u.lower() and not u.endswith('.gif')]

            # Extract text (strip style/script)
            text_chunk = re.sub(r'<style[^>]*>.*?</style>', '', aplus_chunk, flags=re.DOTALL)
            text_chunk = re.sub(r'<script[^>]*>.*?</script>', '', text_chunk, flags=re.DOTALL)
            aplus_text = re.sub(r'<[^>]+>', ' ', text_chunk)
            aplus_text = re.sub(r'\s+', ' ', aplus_text).strip()

            if len(all_aplus_imgs) > 0 or len(aplus_text) > 50:
                result['aplus']['exists'] = True
                result['aplus']['image_count'] = len(all_aplus_imgs)
                result['aplus']['text_length'] = len(aplus_text)

                modules = []
                if 'Brand Story' in aplus_chunk or 'brandStory' in aplus_chunk or 'aplusBrandStory' in aplus_chunk:
                    result['aplus']['has_brand_story'] = True
                    modules.append('brand_story')
                if '<table' in aplus_chunk:
                    result['aplus']['has_comparison_table'] = True
                    modules.append('comparison_table')
                if all_aplus_imgs:
                    modules.append(f'images({len(all_aplus_imgs)})')
                if len(aplus_text) > 100:
                    modules.append(f'text({len(aplus_text)}chars)')
                result['aplus']['modules'] = modules
                result['aplus']['module_count'] = len(modules)

    except requests.RequestException as e:
        result['error'] = str(e)[:200]
    except Exception as e:
        result['error'] = f'Parse error: {str(e)[:180]}'

    return result


def main():
    test_mode = '--test' in sys.argv

    diag = load_json(os.path.join(BASE, 'phase3_diagnosis_v3.json'))
    if not diag:
        print("ERROR: phase3_diagnosis_v3.json not found")
        sys.exit(1)

    asins_to_scrape = []
    for r in diag['amz_results']:
        marketplace = 'us' if r['country'] == 'US' else 'ca'
        asins_to_scrape.append((r['asin'], marketplace))

    if test_mode:
        test_asins = {'B0CTGVWG8M', 'B0CYLM9HFR', 'B0HB8Z741F', 'B0FXG9PR5S', 'B0H38H45W8'}
        test_list = [(a, m) for a, m in asins_to_scrape if a in test_asins]
        if len(test_list) < 5:
            test_list = [(a, m) for a, m in asins_to_scrape if m == 'us'][:5]
        asins_to_scrape = test_list
        print(f'TEST MODE: scraping {len(asins_to_scrape)} ASINs')
    else:
        print(f'Full scrape: {len(asins_to_scrape)} ASINs')

    results = []
    errors = []
    session = requests.Session()

    for i, (asin, mkt) in enumerate(asins_to_scrape):
        print(f'  [{i+1}/{len(asins_to_scrape)}] {asin} ({mkt})...', end=' ', flush=True)
        result = scrape_asin(session, asin, mkt)

        if result['error']:
            print(f'ERROR: {result["error"][:60]}')
            errors.append(result)
        else:
            aplus_info = f'A+:Y(imgs={result["aplus"]["image_count"]})' if result['aplus']['exists'] else 'A+:N'
            print(f'imgs={result["image_count"]}, {aplus_info}, video={result["has_video"]}')

        results.append(result)
        time.sleep(1.0)

    output = {
        'scraped_at': time.strftime('%Y-%m-%d %H:%M'),
        'total': len(results),
        'success': sum(1 for r in results if not r['error']),
        'errors': len(errors),
        'avg_images': round(sum(r['image_count'] for r in results) / len(results), 1) if results else 0,
        'with_aplus': sum(1 for r in results if r['aplus']['exists']),
        'with_video': sum(1 for r in results if r['has_video']),
        'results': results,
    }

    suffix = '_test' if test_mode else ''
    out_path = os.path.join(BASE, f'amz_scrape_images{suffix}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    print(f'\nSaved: {out_path}')
    print(f'Total: {output["total"]}, Success: {output["success"]}, Errors: {output["errors"]}')
    print(f'Avg images: {output["avg_images"]}, With A+: {output["with_aplus"]}, With video: {output["with_video"]}')


if __name__ == '__main__':
    main()
