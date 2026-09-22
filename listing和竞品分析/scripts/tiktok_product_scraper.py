"""
TikTok Shop 产品页全量数据提取工具 v1.0
策略: SeleniumBase UC模式 → SSR数据提取(描述+图片+评论+评分分布)

替代 Browser get_page_text，解决 TikTok 反爬验证拦截问题。
复用 tiktok_review_scraper.py 的 SeleniumBase UC 反爬能力，扩展提取范围。

输出: scripts/product_data/product_{product_id}.json
数据: 产品描述正文 + 图片列表(含URL) + 3条SSR评论 + 全量评分分布

用法:
  python tiktok_product_scraper.py <product_id>
  python tiktok_product_scraper.py <product_id> --method http
  python tiktok_product_scraper.py <product_id> -o custom_output.json
"""

import json
import re
import time
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "product_data"


def parse_ssr_full(html_or_json_str):
    """Parse __MODERN_ROUTER_DATA__ — extracts product info + reviews + ratings."""
    if isinstance(html_or_json_str, str) and html_or_json_str.strip().startswith('{'):
        data = json.loads(html_or_json_str)
    else:
        m = re.search(
            r'<script\s+id="__MODERN_ROUTER_DATA__"[^>]*>(.*?)</script>',
            html_or_json_str, re.DOTALL,
        )
        if not m:
            return None
        data = json.loads(m.group(1))

    result = {
        "product_info": None,
        "description": None,
        "images": [],
        "review_info": None,
    }

    def find_page_data(obj, depth=0):
        if depth > 8 or not isinstance(obj, dict):
            return None
        for k, v in obj.items():
            if "product-detail" in str(k) and isinstance(v, dict):
                return v
            if isinstance(v, dict):
                r = find_page_data(v, depth + 1)
                if r:
                    return r
        return None

    page_data = find_page_data(data)
    if not page_data:
        loader = data.get("loaderData", {})
        for k, v in loader.items():
            if "product" in k.lower() and isinstance(v, dict):
                page_data = v
                break

    if not page_data:
        page_data = data

    # --- Extract product info ---
    product_info = _find_nested(page_data, "product_info") or _find_nested(page_data, "productInfo") or {}
    result["product_info"] = _extract_product_info(product_info, page_data)

    # --- Extract description ---
    desc = (
        product_info.get("desc")
        or product_info.get("description")
        or _find_nested(page_data, "description")
        or _find_nested(page_data, "desc")
    )
    if isinstance(desc, dict):
        desc = desc.get("text") or desc.get("content") or json.dumps(desc, ensure_ascii=False)
    result["description"] = str(desc).strip() if desc else None

    # --- Extract images ---
    images = _extract_images(product_info, page_data)
    result["images"] = images

    # --- Extract reviews + rating distribution ---
    review_data = _extract_reviews(page_data)
    result["review_info"] = review_data

    return result


def _find_nested(obj, key, depth=0):
    if depth > 10 or not isinstance(obj, dict):
        return None
    if key in obj:
        return obj[key]
    for v in obj.values():
        if isinstance(v, dict):
            r = _find_nested(v, key, depth + 1)
            if r is not None:
                return r
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    r = _find_nested(item, key, depth + 1)
                    if r is not None:
                        return r
    return None


def _extract_product_info(product_info, page_data):
    info = {}
    info["title"] = product_info.get("title") or _find_nested(page_data, "title") or ""
    info["product_id"] = product_info.get("product_id") or product_info.get("id") or ""

    price_info = product_info.get("price") or product_info.get("priceInfo") or {}
    if isinstance(price_info, dict):
        info["price"] = price_info.get("sale_price") or price_info.get("price") or price_info.get("min_price") or ""
        info["original_price"] = price_info.get("original_price") or price_info.get("max_price") or ""
    elif isinstance(price_info, (str, int, float)):
        info["price"] = str(price_info)

    info["rating"] = product_info.get("rating") or product_info.get("product_rating") or ""
    info["review_count"] = product_info.get("review_count") or product_info.get("sold_count") or ""

    # SKU/variants
    skus = product_info.get("skus") or product_info.get("sku_list") or _find_nested(page_data, "skus") or []
    if isinstance(skus, list):
        info["sku_count"] = len(skus)
        info["sku_names"] = []
        for sku in skus:
            if isinstance(sku, dict):
                name = sku.get("title") or sku.get("name") or sku.get("sku_name") or ""
                if name:
                    info["sku_names"].append(str(name))

    return info


def _extract_images(product_info, page_data):
    images = []
    seen_urls = set()

    def add_image(url, img_type="product"):
        if not url or not isinstance(url, str):
            return
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        if url in seen_urls or not url.startswith("http"):
            return
        seen_urls.add(url)
        images.append({"url": url, "type": img_type})

    # Method 1: product_info.images
    pi_images = product_info.get("images") or product_info.get("image_list") or product_info.get("product_images") or []
    if isinstance(pi_images, list):
        for img in pi_images:
            if isinstance(img, str):
                add_image(img)
            elif isinstance(img, dict):
                add_image(img.get("url") or img.get("uri") or img.get("thumb_url") or img.get("origin_url") or "")

    # Method 2: cover image
    cover = product_info.get("cover") or product_info.get("cover_url") or product_info.get("main_image") or ""
    if isinstance(cover, dict):
        cover = cover.get("url") or cover.get("uri") or ""
    add_image(cover, "cover")

    # Method 3: search in page_data for image arrays
    for key in ("productImages", "product_images", "gallery", "media"):
        found = _find_nested(page_data, key)
        if isinstance(found, list):
            for img in found:
                if isinstance(img, str):
                    add_image(img)
                elif isinstance(img, dict):
                    add_image(img.get("url") or img.get("uri") or img.get("src") or "")

    return images


def _extract_reviews(page_data):
    review_result = {
        "total_reviews": 0,
        "avg_rating": None,
        "rating_distribution": None,
        "reviews": [],
    }

    ri = _find_nested(page_data, "review_info")
    if not ri or not isinstance(ri, dict):
        return review_result

    total = ri.get("total") or ri.get("total_reviews") or 0
    if isinstance(total, str) and total.isdigit():
        total = int(total)

    raw = ri.get("reviews") or ri.get("product_reviews") or []

    # Rating distribution from review_ratings
    rr = ri.get("review_ratings") or {}
    if rr:
        rc = rr.get("review_count")
        if rc and str(rc).isdigit():
            total = max(int(total) if isinstance(total, (int, float)) else 0, int(rc))
        if rr.get("overall_score"):
            review_result["avg_rating"] = float(rr["overall_score"])
        rd = rr.get("rating_result") or {}
        if rd:
            review_result["rating_distribution"] = {
                str(k): int(v) if str(v).isdigit() else 0
                for k, v in rd.items()
            }

    review_result["total_reviews"] = int(total) if isinstance(total, (int, float)) else 0

    reviews = []
    for r in raw:
        ts = r.get("review_time", "")
        if ts and str(ts).isdigit():
            ts_val = int(ts)
            if ts_val > 1e12:
                ts_val = ts_val / 1000
            date_str = time.strftime("%Y-%m-%d", time.localtime(ts_val))
        else:
            date_str = str(ts) if ts else ""

        review_images = []
        for img in (r.get("review_images") or []):
            if isinstance(img, str):
                review_images.append(img)
            elif isinstance(img, dict):
                u = img.get("url") or img.get("uri") or img.get("thumb_url") or ""
                if u:
                    review_images.append(u)

        reviews.append({
            "review_id": r.get("review_id", ""),
            "rating": r.get("review_rating"),
            "text": r.get("review_text", ""),
            "reviewer_name": r.get("reviewer_name", ""),
            "review_time": date_str,
            "country": r.get("review_country", ""),
            "sku_spec": r.get("sku_specification", ""),
            "images": review_images or None,
            "source": "ssr",
        })

    review_result["reviews"] = reviews
    return review_result


def scrape_with_browser(product_id):
    """Primary: SeleniumBase UC mode — bypasses anti-bot, extracts full SSR data."""
    try:
        from seleniumbase import SB
    except ImportError:
        print("[SKIP] seleniumbase not installed — run: pip install seleniumbase")
        return None

    url = f"https://shop.tiktok.com/us/pdp/-/{product_id}"
    print(f"[Browser] Opening {url}")

    try:
        with SB(uc=True, headed=True, chromium_arg="--lang=en-US",
                disable_features="OptimizationGuideModelDownloading") as sb:
            sb.uc_open_with_reconnect(url, reconnect_time=6)
            sb.sleep(4)

            title = sb.get_title().lower()
            if any(w in title for w in ("security", "verify", "captcha", "check")):
                print("[Browser] CAPTCHA detected, attempting UC click...")
                try:
                    sb.uc_gui_click_captcha()
                except Exception:
                    pass
                sb.sleep(8)
                title = sb.get_title().lower()
                if any(w in title for w in ("security", "verify", "captcha")):
                    print("[Browser] CAPTCHA not resolved")
                    return None

            print(f"[Browser] Page loaded: {sb.get_title()[:80]}")

            # Extract full SSR data
            ssr_text = sb.execute_script(
                "var el = document.getElementById('__MODERN_ROUTER_DATA__');"
                "return el ? el.textContent : null;"
            )
            if not ssr_text:
                print("[Browser] No SSR data found on page")
                # Fallback: try to get page source for description
                page_source = sb.get_page_source()
                if page_source and "__MODERN_ROUTER_DATA__" in page_source:
                    result = parse_ssr_full(page_source)
                    if result:
                        return result
                return None

            result = parse_ssr_full(ssr_text)
            if result:
                pi = result.get("product_info") or {}
                ri = result.get("review_info") or {}
                img_count = len(result.get("images") or [])
                print(f"[SSR] Title: {pi.get('title', 'N/A')[:60]}")
                print(f"[SSR] Description: {'Yes' if result.get('description') else 'No'} "
                      f"({len(result['description'])} chars)" if result.get("description") else "[SSR] Description: No")
                print(f"[SSR] Images: {img_count}")
                print(f"[SSR] Reviews: {len(ri.get('reviews', []))} samples, "
                      f"total: {ri.get('total_reviews', 0)}")
                if ri.get("rating_distribution"):
                    print(f"[SSR] Rating distribution: {ri['rating_distribution']}")
            return result

    except Exception as e:
        print(f"[Browser] Fatal error: {e}")
        return None


def scrape_with_http(product_id, cookies=None):
    """Fallback: HTTP with cookies."""
    from urllib.request import Request, urlopen

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "identity",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }

    if not cookies:
        try:
            import browser_cookie3
            cj = browser_cookie3.chrome(domain_name=".tiktok.com")
            cookies = {c.name: c.value for c in cj}
            cj2 = browser_cookie3.chrome(domain_name="shop.tiktok.com")
            cookies.update({c.name: c.value for c in cj2})
            print(f"[HTTP] Extracted {len(cookies)} cookies from Chrome")
        except Exception as e:
            print(f"[HTTP] Cookie extraction failed: {e}")
            return None

    if not cookies:
        return None

    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
    url = f"https://shop.tiktok.com/us/pdp/-/{product_id}"
    print(f"[HTTP] Fetching {url}")

    try:
        req = Request(url, headers={**headers, "Cookie": cookie_str})
        with urlopen(req, timeout=20) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            html = resp.read().decode(charset, errors="replace")
    except Exception as e:
        print(f"[HTTP] Request failed: {e}")
        return None

    if "Security Check" in html or "__MODERN_ROUTER_DATA__" not in html:
        print("[HTTP] Blocked or no SSR data")
        return None

    return parse_ssr_full(html)


def build_output(product_id, ssr_result):
    """Build final output JSON."""
    if not ssr_result:
        return {
            "product_id": product_id,
            "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "error": "all_methods_failed",
            "product_info": None,
            "description": None,
            "images": [],
            "review_info": {"total_reviews": 0, "reviews": [], "rating_distribution": None},
        }

    return {
        "product_id": product_id,
        "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "success": True,
        "product_info": ssr_result.get("product_info"),
        "description": ssr_result.get("description"),
        "images": ssr_result.get("images", []),
        "review_info": ssr_result.get("review_info", {}),
    }


def print_summary(output):
    """Print human-readable summary."""
    print(f"\n{'='*60}")
    print(f"TikTok 产品页数据提取结果")
    print(f"{'='*60}")
    print(f"产品 ID:   {output['product_id']}")
    print(f"提取时间:  {output['scrape_time']}")
    print(f"状态:      {'✅ 成功' if output['success'] else '❌ 失败'}")

    if not output["success"]:
        print(f"错误:      {output.get('error', 'unknown')}")
        return

    pi = output.get("product_info") or {}
    print(f"\n--- 产品信息 ---")
    print(f"标题:      {pi.get('title', 'N/A')[:80]}")
    print(f"价格:      {pi.get('price', 'N/A')}")
    print(f"SKU数:     {pi.get('sku_count', 'N/A')}")

    desc = output.get("description")
    if desc:
        print(f"\n--- 描述正文 ---")
        print(f"长度:      {len(desc)} 字符")
        print(f"预览:      {desc[:150]}...")
    else:
        print(f"\n--- 描述正文: 未获取到 ---")

    imgs = output.get("images", [])
    print(f"\n--- 图片 ---")
    print(f"数量:      {len(imgs)}")
    for i, img in enumerate(imgs[:5]):
        print(f"  图{i+1}: [{img.get('type','product')}] {img['url'][:80]}...")
    if len(imgs) > 5:
        print(f"  ... 还有 {len(imgs)-5} 张")

    ri = output.get("review_info", {})
    print(f"\n--- 评论与评分 ---")
    print(f"总评论数:  {ri.get('total_reviews', 0)}")
    print(f"平均评分:  {ri.get('avg_rating', 'N/A')}")
    print(f"样本评论:  {len(ri.get('reviews', []))} 条")
    if ri.get("rating_distribution"):
        print("评分分布:")
        dist = ri["rating_distribution"]
        total = sum(int(v) for v in dist.values()) or 1
        for star in ["5", "4", "3", "2", "1"]:
            count = int(dist.get(star, 0))
            pct = count / total * 100
            bar = "█" * int(pct / 2)
            print(f"  {star}★: {count:5d} ({pct:5.1f}%) {bar}")

    if ri.get("reviews"):
        print(f"\n--- 评论样本 ---")
        for r in ri["reviews"][:3]:
            stars = "★" * (r.get("rating") or 0) + "☆" * (5 - (r.get("rating") or 0))
            text = (r.get("text") or "")[:100]
            print(f"  {stars} [{r.get('sku_spec','')}] {text}")


def main():
    parser = argparse.ArgumentParser(description="TikTok Shop 产品页全量数据提取工具 v1.0")
    parser.add_argument("product_id", help="TikTok Shop 产品 ID")
    parser.add_argument("--output", "-o", type=str, default=None)
    parser.add_argument("--method", choices=["auto", "browser", "http"], default="auto")
    parser.add_argument("--cookies-file", type=str, default=None)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = args.output or str(OUTPUT_DIR / f"product_{args.product_id}.json")

    ssr_result = None
    cookies = None
    if args.cookies_file:
        with open(args.cookies_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        cookies = {c.get("name", c.get("key", "")): c.get("value", "") for c in data} if isinstance(data, list) else data

    if args.method in ("auto", "browser"):
        print("[INFO] Method 1: SeleniumBase UC mode...")
        ssr_result = scrape_with_browser(args.product_id)

    if not ssr_result and args.method in ("auto", "http"):
        print("[INFO] Method 2: HTTP + cookies...")
        ssr_result = scrape_with_http(args.product_id, cookies)

    output = build_output(args.product_id, ssr_result)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {output_path}")

    print_summary(output)
    return output


if __name__ == "__main__":
    main()
