"""
TikTok Shop 产品页全量数据提取工具 v1.2
策略: SeleniumBase UC模式 → SSR数据提取(描述+图片+评论样本+评分分布)

替代 Browser get_page_text，解决 TikTok 反爬验证拦截问题。

输出: scripts/product_data/product_{product_id}.json
数据: 产品描述正文 + 图片列表(含URL) + 3条SSR评论样本 + 全量评分分布

v1.2 改进:
  - 自动重试：headless 遇到验证码 → 自动切换 visible 模式重试（需要桌面环境）
  - --visible 参数：强制使用可见浏览器（适合办公电脑）
  - headless 遇到验证码不再浪费时间尝试 uc_gui_click_captcha（headless 下必然失败）

评论获取限制（2026-09 实测）:
  - SSR 永远只包含 3 条评论，无法通过 URL 参数改变
  - get_product_reviews API 受 X-Tts-Oec-Bsid 一次性 token 保护，无法直接调用
  - DOM 翻页在 headless 模式下不工作（Service Worker + React 状态管理限制）
  - 因此评论原文以 FastMoss product_review_list 为主（≥500评论有数据），本脚本 3 条 SSR 评论仅作兜底样本

用法:
  python tiktok_product_scraper.py <product_id>
  python tiktok_product_scraper.py <product_id> --visible        # 办公电脑推荐
  python tiktok_product_scraper.py <product_id> --method http
  python tiktok_product_scraper.py <product_id> -o custom_output.json
"""

import json
import re
import sys
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "product_data"


def ensure_seleniumbase():
    """Auto-install seleniumbase if missing. Returns True if available."""
    try:
        import seleniumbase  # noqa: F401
        return True
    except ImportError:
        print("[AUTO-INSTALL] seleniumbase not found, installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "seleniumbase", "-q"],
                stdout=subprocess.DEVNULL,
            )
            import seleniumbase  # noqa: F401
            print("[AUTO-INSTALL] seleniumbase installed successfully")
            return True
        except Exception as e:
            print(f"[AUTO-INSTALL] Failed to install seleniumbase: {e}")
            print("[HINT] Run manually: pip install seleniumbase")
            return False


def parse_ssr_full(html_or_json_str):
    """Parse __MODERN_ROUTER_DATA__ — extracts product info + reviews + ratings.

    TikTok SSR structure (2026):
    loaderData → (region)/pdp/.../page → page_config → components_map[3]
      → component_data → product_info.product_model (title/desc/images/skus)
                       → review_info (reviews + rating_distribution)
    """
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

    # Step 1: Find the page loader data
    page_data = None
    loader = data.get("loaderData", {})
    for k, v in loader.items():
        if ("pdp" in k or "product" in k.lower()) and isinstance(v, dict):
            page_data = v
            break
    if not page_data:
        page_data = data

    # Step 2: Find component_data from components_map (new TikTok SSR structure)
    comp_data = None
    page_config = page_data.get("page_config", {})
    components = page_config.get("components_map", [])
    for comp in components:
        if comp.get("component_type") == "product_info":
            comp_data = comp.get("component_data", {})
            break

    # Step 3: Extract from component_data (preferred) or fallback to page_data
    if comp_data:
        pi_wrapper = comp_data.get("product_info", {})
        product_model = pi_wrapper.get("product_model", {})

        result["product_info"] = _extract_product_info(product_model, comp_data)

        desc = product_model.get("description") or product_model.get("desc")
        if isinstance(desc, dict):
            desc = desc.get("text") or desc.get("content") or json.dumps(desc, ensure_ascii=False)
        result["description"] = str(desc).strip() if desc else None

        result["images"] = _extract_images(product_model, comp_data)

        review_data = _extract_reviews(comp_data)
        result["review_info"] = review_data
    else:
        # Fallback: old SSR structure or flat layout
        product_info = _find_nested(page_data, "product_info") or {}
        if isinstance(product_info, dict) and "product_model" in product_info:
            product_info = product_info["product_model"]
        result["product_info"] = _extract_product_info(product_info, page_data)

        desc = (
            product_info.get("description") or product_info.get("desc")
            or _find_nested(page_data, "description")
        )
        if isinstance(desc, dict):
            desc = desc.get("text") or desc.get("content") or json.dumps(desc, ensure_ascii=False)
        result["description"] = str(desc).strip() if desc else None

        result["images"] = _extract_images(product_info, page_data)
        result["review_info"] = _extract_reviews(page_data)

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
    info["title"] = (
        product_info.get("name")
        or product_info.get("title")
        or product_info.get("product_name")
        or ""
    )
    info["product_id"] = product_info.get("product_id") or product_info.get("id") or ""
    info["sold_count"] = product_info.get("sold_count") or ""

    price_info = product_info.get("price") or product_info.get("priceInfo") or {}
    if isinstance(price_info, dict):
        info["price"] = price_info.get("sale_price") or price_info.get("price") or price_info.get("min_price") or ""
        info["original_price"] = price_info.get("original_price") or price_info.get("max_price") or ""
    elif isinstance(price_info, (str, int, float)):
        info["price"] = str(price_info)

    info["rating"] = product_info.get("rating") or product_info.get("product_rating") or ""
    info["review_count"] = product_info.get("review_count") or ""

    skus = product_info.get("skus") or product_info.get("sku_list") or []
    if isinstance(skus, list):
        info["sku_count"] = len(skus)
        info["sku_names"] = []
        for sku in skus:
            if isinstance(sku, dict):
                name = sku.get("sku_name") or sku.get("title") or sku.get("name") or ""
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

    def extract_url_from_img(img):
        if isinstance(img, str):
            return img
        if isinstance(img, dict):
            url_list = img.get("url_list", [])
            if url_list and isinstance(url_list, list):
                return url_list[0]
            return (img.get("url") or img.get("uri") or img.get("thumb_url")
                    or img.get("origin_url") or "")
        return ""

    pi_images = product_info.get("images") or product_info.get("image_list") or []
    if isinstance(pi_images, list):
        for img in pi_images:
            add_image(extract_url_from_img(img))

    cover = product_info.get("cover") or product_info.get("cover_url") or ""
    if isinstance(cover, dict):
        cover = extract_url_from_img(cover)
    add_image(cover, "cover")

    sku_images = product_info.get("sku_property_image_map", {})
    if isinstance(sku_images, dict):
        for prop_id, img_obj in sku_images.items():
            add_image(extract_url_from_img(img_obj), "sku")

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
        for img in (r.get("review_images") or r.get("images") or []):
            if isinstance(img, str):
                review_images.append(img)
            elif isinstance(img, dict):
                url_list = img.get("url_list", [])
                if url_list:
                    review_images.append(url_list[0])
                else:
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


def scrape_with_browser(product_id, force_visible=False):
    """Primary: SeleniumBase UC mode — bypasses anti-bot, extracts full SSR data.

    Strategy:
    - Default: try headless first (fast, no display needed).
      If CAPTCHA detected → auto-retry with visible browser (needs display).
    - --visible: skip headless, go straight to visible mode (for office desktops).

    CAPTCHA bypass depends on IP reputation — same code may pass on one machine
    but get CAPTCHA'd on another. This is TikTok's server-side decision, not a bug.
    """
    if not ensure_seleniumbase():
        return None

    if force_visible:
        print("[Browser] Visible mode requested, skipping headless attempt")
        return _browser_attempt(product_id, headless=False)

    # Attempt 1: headless (fast, works when TikTok doesn't challenge)
    result = _browser_attempt(product_id, headless=True)
    if result is not None:
        return result

    # Attempt 2: visible browser (uc_gui_click_captcha needs a real display)
    print("[Browser] Headless failed — retrying with visible browser...")
    print("[Browser] (Requires a desktop environment with display)")
    try:
        result = _browser_attempt(product_id, headless=False)
        return result
    except Exception as e:
        print(f"[Browser] Visible mode unavailable: {e}")
        return None


def _browser_attempt(product_id, headless=True):
    """Single browser attempt. Returns SSR result dict or None."""
    from seleniumbase import SB

    url = f"https://shop.tiktok.com/us/pdp/-/{product_id}"
    mode = "headless" if headless else "visible"
    print(f"[Browser] Opening {url} ({mode})")

    try:
        with SB(uc=True, headless=headless, chromium_arg="--lang=en-US",
                disable_features="OptimizationGuideModelDownloading") as sb:
            sb.uc_open_with_reconnect(url, reconnect_time=6)
            sb.sleep(4)

            title = sb.get_title().lower()
            captcha_words = ("security", "verify", "captcha", "check")
            if any(w in title for w in captcha_words):
                if headless:
                    # In headless mode, uc_gui_click_captcha cannot work (no real pixels)
                    # Don't waste time retrying — signal caller to retry with visible
                    print(f"[Browser] CAPTCHA in headless mode — auto-click not possible")
                    return None

                # Visible mode: uc_gui_click_captcha can work with a real display
                print("[Browser] CAPTCHA detected, attempting auto-click...")
                for attempt in range(3):
                    try:
                        sb.uc_gui_click_captcha()
                    except Exception:
                        pass
                    sb.sleep(5)
                    title = sb.get_title().lower()
                    if not any(w in title for w in captcha_words):
                        print(f"[Browser] CAPTCHA resolved on attempt {attempt + 1}")
                        break
                else:
                    print("[Browser] CAPTCHA not resolved after 3 attempts")
                    return None

            print(f"[Browser] Page loaded: {sb.get_title()[:80]}")

            # Extract full SSR data
            ssr_text = sb.execute_script(
                "var el = document.getElementById('__MODERN_ROUTER_DATA__');"
                "return el ? el.textContent : null;"
            )
            if not ssr_text:
                print("[Browser] No SSR data found on page")
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
                if result.get("description"):
                    print(f"[SSR] Description: Yes ({len(result['description'])} chars)")
                else:
                    print(f"[SSR] Description: No")
                print(f"[SSR] Images: {img_count}")
                print(f"[SSR] Reviews: {len(ri.get('reviews', []))} samples, "
                      f"total: {ri.get('total_reviews', 0)}")
                if ri.get("rating_distribution"):
                    print(f"[SSR] Rating distribution: {ri['rating_distribution']}")
            return result

    except Exception as e:
        print(f"[Browser] Error ({mode}): {e}")
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


def _safe_print(text):
    """Print with fallback for Windows GBK console."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def print_summary(output):
    """Print human-readable summary."""
    _safe_print(f"\n{'='*60}")
    _safe_print("TikTok Product Page Data Extraction Result")
    _safe_print(f"{'='*60}")
    _safe_print(f"Product ID:   {output['product_id']}")
    _safe_print(f"Scrape Time:  {output['scrape_time']}")
    _safe_print(f"Status:       {'OK' if output['success'] else 'FAILED'}")

    if not output["success"]:
        _safe_print(f"Error:        {output.get('error', 'unknown')}")
        return

    pi = output.get("product_info") or {}
    _safe_print(f"\n--- Product Info ---")
    _safe_print(f"Title:        {pi.get('title', 'N/A')[:80]}")
    _safe_print(f"Price:        {pi.get('price', 'N/A')}")
    _safe_print(f"SKU Count:    {pi.get('sku_count', 'N/A')}")

    desc = output.get("description")
    if desc:
        _safe_print(f"\n--- Description ---")
        _safe_print(f"Length:       {len(desc)} chars")
        _safe_print(f"Preview:      {desc[:150]}...")
    else:
        _safe_print(f"\n--- Description: not available ---")

    imgs = output.get("images", [])
    _safe_print(f"\n--- Images ---")
    _safe_print(f"Count:        {len(imgs)}")
    for i, img in enumerate(imgs[:5]):
        _safe_print(f"  img{i+1}: [{img.get('type','product')}] {img['url'][:80]}...")
    if len(imgs) > 5:
        _safe_print(f"  ... and {len(imgs)-5} more")

    ri = output.get("review_info", {})
    _safe_print(f"\n--- Reviews & Ratings ---")
    _safe_print(f"Total:        {ri.get('total_reviews', 0)}")
    _safe_print(f"Avg Rating:   {ri.get('avg_rating', 'N/A')}")
    _safe_print(f"Samples:      {len(ri.get('reviews', []))} reviews")
    if ri.get("rating_distribution"):
        _safe_print("Distribution:")
        dist = ri["rating_distribution"]
        total = sum(int(v) for v in dist.values()) or 1
        for star in ["5", "4", "3", "2", "1"]:
            count = int(dist.get(star, 0))
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            _safe_print(f"  {star}*: {count:5d} ({pct:5.1f}%) {bar}")

    if ri.get("reviews"):
        _safe_print(f"\n--- Review Samples ---")
        for r in ri["reviews"][:3]:
            rating = r.get("rating") or 0
            text = (r.get("text") or "")[:100]
            _safe_print(f"  [{rating}/5] [{r.get('sku_spec','')}] {text}")


def main():
    parser = argparse.ArgumentParser(description="TikTok Shop 产品页全量数据提取工具 v1.2")
    parser.add_argument("product_id", help="TikTok Shop 产品 ID")
    parser.add_argument("--output", "-o", type=str, default=None)
    parser.add_argument("--method", choices=["auto", "browser", "http"], default="auto")
    parser.add_argument("--visible", action="store_true",
                        help="Force visible browser (skip headless). Use on office desktops for better CAPTCHA handling.")
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
        ssr_result = scrape_with_browser(args.product_id, force_visible=args.visible)

    if not ssr_result and args.method in ("auto", "http"):
        print("[INFO] Method 2: HTTP + cookies...")
        ssr_result = scrape_with_http(args.product_id, cookies)

    output = build_output(args.product_id, ssr_result)

    if not output["success"]:
        print("\n[NOTE] Scraper failed. This is usually caused by TikTok anti-bot (IP reputation).")
        print("[NOTE] The skill will automatically use Layer 2/3 fallback — report generation is NOT affected.")
        if not args.visible:
            print("[HINT] Try --visible on a desktop machine for better CAPTCHA handling.")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {output_path}")

    print_summary(output)
    return output


if __name__ == "__main__":
    main()
