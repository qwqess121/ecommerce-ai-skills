"""
TikTok Shop 评论获取工具 v5.2 (Production)
策略: SeleniumBase UC模式 → SSR数据提取(评论样本+评分分布)
适用: FastMoss product_review_list 返回0的小评论量商品(<500评论)

输出: scripts/reviews/reviews_{product_id}.json
数据: 3条SSR评论样本(含原文/评分/日期/图片) + 全量评分分布(所有评论的1-5星计数) + 平均评分

v5.2: headless遇验证码自动重试visible模式 + --visible参数

技术限制（2026-09 实测）:
  SSR 固定只含 3 条评论，TikTok 的 get_product_reviews API 使用一次性 token 保护，
  DOM 翻页在 headless 模式下因 Service Worker 限制无法工作。
  因此本工具只能获取 3 条评论样本 + 全量评分分布。
  评论原文主力来源应为 FastMoss product_review_list API（≥500评论商品有数据）。

用法:
  python tiktok_review_scraper.py <product_id> [--output reviews.json]
  python tiktok_review_scraper.py <product_id> --visible
  python tiktok_review_scraper.py <product_id> --method http
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
REVIEWS_DIR = SCRIPT_DIR / "reviews"


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


def parse_ssr_data(html_or_json_str):
    """Parse __MODERN_ROUTER_DATA__ — extracts reviews + full rating distribution."""
    if isinstance(html_or_json_str, str) and html_or_json_str.startswith('{'):
        data = json.loads(html_or_json_str)
    else:
        m = re.search(
            r'<script\s+id="__MODERN_ROUTER_DATA__"[^>]*>(.*?)</script>',
            html_or_json_str, re.DOTALL,
        )
        if not m:
            return 0, [], {}
        data = json.loads(m.group(1))

    def find_reviews(obj, depth=0):
        if depth > 10 or not isinstance(obj, dict):
            return None
        if "review_info" in obj:
            ri = obj["review_info"]
            if isinstance(ri, dict) and ("reviews" in ri or "product_reviews" in ri):
                return ri
        for v in obj.values():
            if isinstance(v, dict):
                r = find_reviews(v, depth + 1)
                if r:
                    return r
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        r = find_reviews(item, depth + 1)
                        if r:
                            return r
        return None

    ri = find_reviews(data)
    if not ri:
        return 0, [], {}

    total = ri.get("total") or ri.get("total_reviews") or 0
    if isinstance(total, str) and total.isdigit():
        total = int(total)
    raw = ri.get("reviews") or ri.get("product_reviews") or []

    # Extract rating distribution from review_ratings (SSR has full data)
    rating_meta = {}
    rr = ri.get("review_ratings") or {}
    if rr:
        rc = rr.get("review_count")
        if rc and str(rc).isdigit():
            total = max(int(total) if isinstance(total, (int, float)) else 0, int(rc))
        if rr.get("overall_score"):
            rating_meta["avg_rating"] = float(rr["overall_score"])
        rd = rr.get("rating_result") or {}
        if rd:
            rating_meta["rating_distribution"] = {
                str(k): int(v) if str(v).isdigit() else 0
                for k, v in rd.items()
            }

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

        images = []
        for img in (r.get("review_images") or []):
            if isinstance(img, str):
                images.append(img)
            elif isinstance(img, dict):
                u = img.get("url") or img.get("uri") or img.get("thumb_url") or ""
                if u:
                    images.append(u)

        reviews.append({
            "review_id": r.get("review_id", ""),
            "rating": r.get("review_rating"),
            "text": r.get("review_text", ""),
            "reviewer_name": r.get("reviewer_name", ""),
            "review_time": date_str,
            "is_verified_purchase": bool(r.get("is_verified_purchase")),
            "is_incentivized": bool(r.get("is_incentivized_review")),
            "country": r.get("review_country", ""),
            "sku_spec": r.get("sku_specification", ""),
            "images": images or None,
            "source": "ssr",
        })

    return int(total) if isinstance(total, (int, float)) else 0, reviews, rating_meta


def scrape_browser(product_id, force_visible=False):
    """Primary: SeleniumBase UC mode — bypasses anti-bot, extracts SSR data.

    Strategy: headless first → if CAPTCHA, retry visible (needs display).
    Use --visible on office desktops for better CAPTCHA handling.
    """
    if not ensure_seleniumbase():
        return None

    if force_visible:
        return _review_browser_attempt(product_id, headless=False)

    result = _review_browser_attempt(product_id, headless=True)
    if result is not None:
        return result

    print("[Browser] Headless failed — retrying with visible browser...")
    try:
        return _review_browser_attempt(product_id, headless=False)
    except Exception as e:
        print(f"[Browser] Visible mode unavailable: {e}")
        return None


def _review_browser_attempt(product_id, headless=True):
    """Single browser attempt for review extraction."""
    from seleniumbase import SB

    url = f"https://shop.tiktok.com/us/pdp/-/{product_id}"
    mode = "headless" if headless else "visible"
    all_reviews = []
    seen = set()
    total_reported = 0
    rating_meta = {}

    def add(reviews):
        nonlocal all_reviews, seen
        for r in reviews:
            key = r.get("review_id") or (
                r.get("review_time", "") + "|" + r.get("reviewer_name", "") + "|" + (r.get("text") or "")[:40]
            )
            if key and key not in seen:
                seen.add(key)
                all_reviews.append(r)

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
                    print(f"[Browser] CAPTCHA in headless mode — auto-click not possible")
                    return None

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

            print(f"[Browser] Page loaded: {sb.get_title()[:60]}")

            try:
                ssr_text = sb.execute_script(
                    "var el = document.getElementById('__MODERN_ROUTER_DATA__');"
                    "return el ? el.textContent : null;"
                )
                if ssr_text:
                    total_reported, ssr_reviews, rating_meta = parse_ssr_data(ssr_text)
                    add(ssr_reviews)
                    print(f"[SSR] {len(ssr_reviews)} reviews extracted, total reported: {total_reported}")
                    if rating_meta.get("rating_distribution"):
                        print(f"[SSR] Rating distribution: {rating_meta['rating_distribution']}")
                    if rating_meta.get("avg_rating"):
                        print(f"[SSR] Average rating: {rating_meta['avg_rating']}")
            except Exception as e:
                print(f"[SSR] Extraction error: {e}")

    except Exception as e:
        print(f"[Browser] Error ({mode}): {e}")
        if all_reviews:
            return build_result(product_id, all_reviews, total_reported, rating_meta)
        return None

    if not all_reviews:
        return None
    return build_result(product_id, all_reviews, total_reported, rating_meta)


def scrape_http(product_id, cookies=None):
    """Fallback: HTTP with cookies — requires Chrome closed for cookie extraction."""
    from urllib.request import Request, urlopen

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "identity",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
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
            print("[HINT] Close Chrome first, or use --cookies-file")
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

    total, reviews, rating_meta = parse_ssr_data(html)
    print(f"[HTTP] Extracted {len(reviews)} reviews, total: {total}")
    return build_result(product_id, reviews, total, rating_meta)


def build_result(product_id, reviews, total_reported, rating_meta=None):
    """Build standardized output."""
    unique = []
    seen = set()
    for r in reviews:
        key = r.get("review_id") or (r.get("review_time", "") + r.get("reviewer_name", "") + (r.get("text") or "")[:40])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    result = {
        "product_id": product_id,
        "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_reviews": len(unique),
        "total_reviews_reported": total_reported,
        "reviews": unique,
    }

    # Rating stats from scraped reviews (sample)
    ratings = [r["rating"] for r in unique if r.get("rating") and isinstance(r["rating"], (int, float))]
    if ratings:
        result["avg_rating"] = round(sum(ratings) / len(ratings), 2)
        result["rating_distribution"] = {str(s): ratings.count(s) for s in range(5, 0, -1)}

    # Full rating distribution from SSR (complete data for all reviews)
    if rating_meta:
        if rating_meta.get("avg_rating"):
            result["avg_rating_page"] = rating_meta["avg_rating"]
        if rating_meta.get("rating_distribution"):
            result["rating_distribution_page"] = rating_meta["rating_distribution"]

    result["reviews_with_text"] = sum(1 for r in unique if r.get("text") and len(r["text"]) > 5)
    result["reviews_with_images"] = sum(1 for r in unique if r.get("images"))
    result["verified_purchases"] = sum(1 for r in unique if r.get("is_verified_purchase"))

    return result


def _safe_print(text):
    """Print with fallback for Windows GBK console."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def print_summary(result):
    """Print human-readable summary."""
    _safe_print(f"\n{'='*50}")
    _safe_print("Review Extraction Result")
    _safe_print(f"{'='*50}")
    _safe_print(f"Product ID: {result['product_id']}")
    _safe_print(f"Scrape Time: {result['scrape_time']}")
    _safe_print(f"Reviews Got: {result['total_reviews']}")
    if result.get("total_reviews_reported"):
        _safe_print(f"Total Reviews: {result['total_reviews_reported']}")
    if result.get("avg_rating_page"):
        _safe_print(f"Avg Rating: {result['avg_rating_page']}")
    elif result.get("avg_rating"):
        _safe_print(f"Avg Rating (sample): {result['avg_rating']}")
    if result.get("rating_distribution_page"):
        _safe_print("Distribution:")
        dist = result["rating_distribution_page"]
        total = sum(dist.values()) or 1
        for star in ["5", "4", "3", "2", "1"]:
            count = dist.get(star, 0)
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            _safe_print(f"  {star}*: {count:3d} ({pct:5.1f}%) {bar}")
    elif result.get("rating_distribution"):
        _safe_print("Distribution (sample):")
        for star in ["5", "4", "3", "2", "1"]:
            count = result["rating_distribution"].get(star, 0)
            total = max(result["total_reviews"], 1)
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            _safe_print(f"  {star}*: {count:3d} ({pct:5.1f}%) {bar}")
    _safe_print(f"With text: {result.get('reviews_with_text', 0)}")
    _safe_print(f"With images: {result.get('reviews_with_images', 0)}")
    _safe_print(f"Verified: {result.get('verified_purchases', 0)}")


def main():
    parser = argparse.ArgumentParser(description="TikTok Shop 评论获取工具 v5.2")
    parser.add_argument("product_id", help="TikTok Shop 产品 ID")
    parser.add_argument("--output", "-o", type=str, default=None)
    parser.add_argument("--method", choices=["auto", "browser", "http"], default="auto",
                        help="auto=browser优先, browser=仅UC模式, http=仅HTTP+cookies")
    parser.add_argument("--visible", action="store_true",
                        help="Force visible browser (skip headless). Use on office desktops.")
    parser.add_argument("--cookies-file", type=str, default=None)
    args = parser.parse_args()

    REVIEWS_DIR.mkdir(exist_ok=True)
    output_path = args.output or str(REVIEWS_DIR / f"reviews_{args.product_id}.json")
    result = None

    cookies = None
    if args.cookies_file:
        with open(args.cookies_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        cookies = {c.get("name", c.get("key", "")): c.get("value", "") for c in data} if isinstance(data, list) else data
        print(f"[INFO] Loaded {len(cookies)} cookies from file")

    if args.method in ("auto", "browser"):
        print("[INFO] Trying SeleniumBase UC mode...")
        result = scrape_browser(args.product_id, force_visible=args.visible)

    if not result and args.method in ("auto", "http"):
        print("[INFO] Trying HTTP + cookies...")
        result = scrape_http(args.product_id, cookies)

    if not result:
        result = {
            "product_id": args.product_id,
            "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "all_methods_failed",
            "total_reviews": 0,
            "total_reviews_reported": 0,
            "reviews": [],
        }
        print("[ERROR] All extraction methods failed")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {output_path}")

    print_summary(result)
    return result


if __name__ == "__main__":
    main()
