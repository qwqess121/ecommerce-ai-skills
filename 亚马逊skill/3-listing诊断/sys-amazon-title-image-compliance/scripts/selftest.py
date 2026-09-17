#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""amazon-title-image-compliance 一键自测脚本。

用法（在 skill 根目录下运行）:
    python scripts/selftest.py

它会:
  1. 在临时目录生成样例数据（含各类违规标题 + 6 张占位图片 + 映射表）
  2. 依次运行 make-rules / clean-titles / optimize-titles / rename-images
  3. 断言关键输出，打印 PASS/FAIL 汇总

退出码: 0=全部通过, 1=有失败。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amazon_compliance.py")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable

PRODUCTS = """sku,item_name
SKU001,SUPER !!! Best Seller Wireless Earbuds _Premium_ Bluetooth 5.0 Free Shipping Worldwide 2024 Wireless Earbuds Wireless Earbuds
SKU002,AMAZONBASICS USB CABLE ??? HIGH QUALITY {cable} cable cable cable for Charging
SKU003,Nike Air Max Shoes, Black/White, Size 10
SKU004,Stainless Steel Water Bottle Insulated Thermos Flask Water Bottle Travel Outdoor Sports Gym Fitness Hiking Camping Running Yoga Office School Home Kitchen Garden Beach Pool Lake River Mountain Forest Park Water Bottle Trail Camping Bottle Cup Mug
SKU005,Cool~Gadget#123 <10pk> *new* Premium Phone Holder with Strong Grip and Grip
"""

PRODUCTS_OPT = """sku,brand,primary_keyword,item_name
SKU001,SoundWave,wireless earbuds,SUPER !!! Best Seller Wireless Earbuds _Premium_ Bluetooth 5.0 Free Shipping Worldwide 2024 Wireless Earbuds Wireless Earbuds
SKU002,AmazonBasics,usb cable,AMAZONBASICS USB CABLE ??? HIGH QUALITY {cable} cable cable cable for Charging
SKU003,Nike,running shoes,Nike Air Max Shoes, Black/White, Size 10
SKU004,HoogaLife,car air freshener,Car Air Freshener 2-Pack Premium Bamboo Charcoal Purifier for Car Interior with Strong Grip
"""

MAP = """key,original_file,index
SKU001,img_old_a.jpg,0
SKU001,img_old_b.jpg,1
SKU002,img_old_c.jpg,0
SKU003,img_old_d.jpg,0
SKU003,img_old_e.jpg,1
SKU003,img_old_f.jpg,2
"""


def run(args, cwd):
    r = subprocess.run([PYTHON, SCRIPT] + args, cwd=cwd, capture_output=True, text=True)
    return r


def main():
    tmp = tempfile.mkdtemp(prefix="amz_skill_")
    print(f"临时目录: {tmp}\n")
    try:
        # 1. 准备样例文件
        with open(os.path.join(tmp, "products.csv"), "w", encoding="utf-8") as f:
            f.write(PRODUCTS)
        with open(os.path.join(tmp, "products_opt.csv"), "w", encoding="utf-8") as f:
            f.write(PRODUCTS_OPT)
        with open(os.path.join(tmp, "map.csv"), "w", encoding="utf-8") as f:
            f.write(MAP)
        os.makedirs(os.path.join(tmp, "imgs"), exist_ok=True)
        for name in ["img_old_a.jpg", "img_old_b.jpg", "img_old_c.jpg",
                     "img_old_d.jpg", "img_old_e.jpg", "img_old_f.jpg"]:
            open(os.path.join(tmp, "imgs", name), "w").close()

        results = []
        # 2. make-rules
        r = run(["make-rules", "--out", "rules.json"], tmp)
        results.append(("make-rules", r.returncode == 0 and os.path.exists(os.path.join(tmp, "rules.json")), r.stdout))

        # 3. clean-titles
        r = run(["clean-titles", "--input", "products.csv", "--output", "cleaned.csv",
                 "--rules", "rules.json"], tmp)
        ok = r.returncode == 0 and os.path.exists(os.path.join(tmp, "cleaned.csv"))
        if ok:
            with open(os.path.join(tmp, "cleaned.csv"), encoding="utf-8-sig") as f:
                content = f.read()
            ok = "SKU001" in content and "SKU003" in content and "SKU004" in content
        results.append(("clean-titles", ok, r.stdout))

        # 4. optimize-titles
        r = run(["optimize-titles", "--input", "products_opt.csv", "--output", "optimized.csv",
                 "--rules", "rules.json"], tmp)
        ok = r.returncode == 0 and os.path.exists(os.path.join(tmp, "optimized.csv"))
        if ok:
            with open(os.path.join(tmp, "optimized.csv"), encoding="utf-8-sig") as f:
                content = f.read()
            # 主关键词前置：SoundWave 后应紧跟 Wireless Earbuds
            ok = "SoundWave Wireless Earbuds" in content
        results.append(("optimize-titles", ok, r.stdout))

        # 5. rename-images
        r = run(["rename-images", "--mapping", "map.csv", "--image-dir", "imgs",
                 "--output-dir", "renamed", "--rules", "rules.json"], tmp)
        ok = r.returncode == 0 and os.path.exists(os.path.join(tmp, "renamed", "SKU001.jpg")) \
             and os.path.exists(os.path.join(tmp, "renamed", "SKU001_01.jpg")) \
             and os.path.exists(os.path.join(tmp, "renamed", "SKU003_02.jpg"))
        results.append(("rename-images", ok, r.stdout))

        # 6. 汇总
        print("=" * 50)
        all_ok = True
        for name, ok, out in results:
            print(f"[{'PASS' if ok else 'FAIL'}] {name}")
            if not ok:
                all_ok = False
            for line in (out or "").strip().splitlines()[-3:]:
                print(f"      {line}")
        print("=" * 50)
        print(f"结果: {'全部通过 ✅' if all_ok else '存在失败 ❌'}")
        print(f"产物目录: {tmp}（需保留请复制，脚本结束会保留）")
        return 0 if all_ok else 1
    finally:
        # 保留产物便于检查；如需清理改为 shutil.rmtree(tmp)
        pass


if __name__ == "__main__":
    sys.exit(main())
