"""
run_all.py — 一键运行 Listing 诊断报告生成
用法: python scripts/run_all.py [--skip-scoring] [--data-check-only]
"""
import subprocess, sys, os, json, glob
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(BASE, 'output')
SCRIPTS = os.path.dirname(os.path.abspath(__file__))

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_data():
    print("=== 数据文件检查 ===")
    required = {
        'phase0_data.json': '商品清单(领星+FastMoss)',
    }
    optional = {
        'competitor_products.json': '亚马逊竞品数据(卖酷)',
        'ads_analysis.json': '广告/流量分析(Sif)',
        'tiktok_data.json': 'TikTok商品数据(FastMoss)',
        'tk_product_details.json': 'TikTok商品详情(FastMoss)',
        'amz_scrape_images.json': '亚马逊图片采集(Playwright)',
        'tk_scrape_details.json': 'TikTok详情采集(HTTP)',
    }

    asin_files = sorted(glob.glob(os.path.join(OUTPUT, 'asin_detail_*.json')))
    total_asins = 0
    for f in asin_files:
        data = load_json(f)
        if data:
            items = data if isinstance(data, list) else data.get('results', [])
            total_asins += sum(1 for i in items if 'error' not in i and i.get('asin'))

    ok = True
    for f, desc in required.items():
        path = os.path.join(OUTPUT, f)
        if os.path.exists(path):
            sz = os.path.getsize(path)
            age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).days
            print(f"  [OK] {f} ({sz/1024:.0f}KB, {age}天前)")
        else:
            print(f"  [!!] {f} — 缺失! ({desc})")
            ok = False

    print(f"  [{'OK' if total_asins > 0 else '!!'}] asin_detail_*.json — {len(asin_files)}个文件, {total_asins}个ASIN")
    if total_asins == 0:
        ok = False

    for f, desc in optional.items():
        path = os.path.join(OUTPUT, f)
        if os.path.exists(path):
            sz = os.path.getsize(path)
            print(f"  [OK] {f} ({sz/1024:.0f}KB)")
        else:
            print(f"  [--] {f} — 可选, 未采集 ({desc})")

    return ok

def run_script(name, label):
    print(f"\n--- {label} ---")
    script_path = os.path.join(SCRIPTS, name)
    if not os.path.exists(script_path):
        print(f"ERROR: {script_path} not found")
        return False
    result = subprocess.run(
        [sys.executable, '-I', script_path],
        capture_output=True, text=True, cwd=BASE, encoding='utf-8', errors='replace'
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        print(f"FAILED (exit {result.returncode})")
        if result.stderr:
            print(result.stderr[:500])
        return False
    return True

def clean_old_reports(keep_latest=1):
    reports = sorted(glob.glob(os.path.join(OUTPUT, 'Listing诊断报告v3*.xlsx')))
    if len(reports) > keep_latest:
        for old in reports[:-keep_latest]:
            os.remove(old)
            print(f"  已删除旧报告: {os.path.basename(old)}")

def main():
    print(f"{'='*50}")
    print(f"  Listing 诊断报告 一键生成")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")

    skip_scoring = '--skip-scoring' in sys.argv
    data_check = '--data-check-only' in sys.argv

    if not check_data():
        print("\n缺少必要数据文件。请先通过 Claude 执行数据采集（Phase 0/1）。")
        if data_check:
            return
        sys.exit(1)

    if data_check:
        print("\n数据检查完成。")
        return

    if not skip_scoring:
        if not run_script('phase3_scoring_v3.py', 'Phase 3: 评分与诊断'):
            sys.exit(1)
    else:
        diag_path = os.path.join(OUTPUT, 'phase3_diagnosis_v3.json')
        if not os.path.exists(diag_path):
            print("ERROR: --skip-scoring 但 phase3_diagnosis_v3.json 不存在")
            sys.exit(1)
        print("\n--- Phase 3: 跳过评分(使用已有结果) ---")

    if not run_script('phase5_report_v3.py', 'Phase 5: 生成Excel报告'):
        sys.exit(1)

    clean_old_reports(keep_latest=1)

    reports = sorted(glob.glob(os.path.join(OUTPUT, 'Listing诊断报告v3*.xlsx')))
    if reports:
        print(f"\n{'='*50}")
        print(f"  最终报告: {os.path.basename(reports[-1])}")
        print(f"{'='*50}")

if __name__ == '__main__':
    main()
