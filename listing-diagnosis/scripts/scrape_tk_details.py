"""
TikTok product scraper: images + description
Uses requests + regex (TikTok SSR data in HTML)
"""
import json, os, sys, time, re
import requests

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def scrape_product(session, product_id, title=''):
    url = f'https://www.tiktok.com/shop/pdp/{product_id}'

    result = {
        'product_id': str(product_id),
        'url': url,
        'images': [],
        'image_count': 0,
        'description': '',
        'description_length': 0,
        'og_description': '',
        'rich_text_lines': [],
        'error': None,
    }

    try:
        r = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            result['error'] = f'HTTP {r.status_code}'
            return result

        html = r.text
        if len(html) < 5000:
            result['error'] = 'Page too short (blocked?)'
            return result

        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        big_script = ''
        for s in scripts:
            if len(s) > len(big_script):
                big_script = s

        if not big_script or len(big_script) < 1000:
            result['error'] = 'No data script found'
            return result

        # === IMAGES ===
        pi_idx = big_script.find('"product_info"')
        if pi_idx >= 0:
            chunk = big_script[pi_idx:pi_idx+30000]
            img_matches = re.findall(
                r'"width":(\d+),"height":(\d+),"uri":"([^"]+)"', chunk
            )
            seen_uri = set()
            for w, h, uri in img_matches:
                clean_uri = uri.replace('\\u002F', '/')
                if clean_uri not in seen_uri and 'free_shipping' not in clean_uri and 'icon' not in clean_uri:
                    seen_uri.add(clean_uri)
                    # Find full URL
                    uri_search = uri
                    url_area_idx = chunk.find(uri_search)
                    full_url = ''
                    if url_area_idx >= 0:
                        url_list_match = re.search(
                            r'"url_list"\s*:\s*\["([^"]+)"',
                            chunk[url_area_idx:url_area_idx+500]
                        )
                        if url_list_match:
                            full_url = url_list_match.group(1).replace('\\u002F', '/')

                    result['images'].append({
                        'width': int(w),
                        'height': int(h),
                        'url': full_url or f'https://p16-oec-general.ttcdn-us.com/{clean_uri}',
                    })

        result['image_count'] = len(result['images'])

        # === DESCRIPTION ===
        og_desc = re.search(
            r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"', html
        )
        if og_desc:
            result['og_description'] = og_desc.group(1).replace('&amp;', '&').replace('&#39;', "'")

        # Extract rich_text content from product detail section
        # rich_text blocks appear after product_info in the script
        rich_idx = big_script.find('"rich_text"', pi_idx if pi_idx >= 0 else 0)
        if rich_idx >= 0:
            rich_area = big_script[rich_idx:rich_idx+30000]
            texts = re.findall(r'"text"\s*:\s*"([^"]*?[A-Za-z][^"]*?)"', rich_area)
            seen_texts = set()
            for t in texts:
                decoded = t.replace('\\u002F', '/').replace('\\n', '\n').replace('\\u2019', '\u2019')
                decoded = decoded.replace('\\u2013', '\u2013').replace('\\u2014', '\u2014')
                decoded = decoded.replace('\\u00e9', '\u00e9').replace('\\u00e8', '\u00e8')
                if len(decoded) > 5 and decoded not in seen_texts and not decoded.startswith('http'):
                    seen_texts.add(decoded)
                    result['rich_text_lines'].append(decoded)

        # Build full description
        if result['rich_text_lines']:
            result['description'] = '\n'.join(result['rich_text_lines'])
            result['description_length'] = len(result['description'])
        elif result['og_description']:
            result['description'] = result['og_description']
            result['description_length'] = len(result['og_description'])

    except requests.RequestException as e:
        result['error'] = str(e)[:200]
    except Exception as e:
        result['error'] = f'Parse error: {str(e)[:180]}'

    return result


def main():
    test_mode = '--test' in sys.argv

    tk_data = load_json(os.path.join(BASE, 'tiktok_data.json'))
    if not tk_data:
        print("ERROR: tiktok_data.json not found")
        sys.exit(1)

    products_to_scrape = []
    for shop, sv in tk_data.get('shops', {}).items():
        for p in sv.get('products', []):
            products_to_scrape.append({
                'product_id': str(p['product_id']),
                'title': p.get('title', ''),
                'shop': shop,
            })

    if test_mode:
        products_to_scrape = products_to_scrape[:5]
        print(f'TEST MODE: scraping {len(products_to_scrape)} products')
    else:
        print(f'Full scrape: {len(products_to_scrape)} products')

    results = []
    errors = []
    session = requests.Session()

    for i, prod in enumerate(products_to_scrape):
        pid = prod['product_id']
        print(f'  [{i+1}/{len(products_to_scrape)}] {pid}...', end=' ', flush=True)
        result = scrape_product(session, pid, prod.get('title', ''))

        if result['error']:
            print(f'ERROR: {result["error"][:60]}')
            errors.append(result)
        else:
            desc_info = f'desc={result["description_length"]}chars' if result['description_length'] else 'no_desc'
            print(f'imgs={result["image_count"]}, {desc_info}, lines={len(result["rich_text_lines"])}')

        results.append(result)
        time.sleep(1.5)

    output = {
        'scraped_at': time.strftime('%Y-%m-%d %H:%M'),
        'total': len(results),
        'success': sum(1 for r in results if not r['error']),
        'errors': len(errors),
        'avg_images': round(sum(r['image_count'] for r in results) / len(results), 1) if results else 0,
        'with_description': sum(1 for r in results if r['description_length'] > 0),
        'avg_desc_length': round(sum(r['description_length'] for r in results) / max(1, sum(1 for r in results if r['description_length'] > 0))),
        'results': results,
    }

    suffix = '_test' if test_mode else ''
    out_path = os.path.join(BASE, f'tk_scrape_details{suffix}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    print(f'\nSaved: {out_path}')
    print(f'Total: {output["total"]}, Success: {output["success"]}, Errors: {output["errors"]}')
    print(f'Avg images: {output["avg_images"]}, With description: {output["with_description"]}')
    print(f'Avg desc length: {output["avg_desc_length"]}')


if __name__ == '__main__':
    main()
