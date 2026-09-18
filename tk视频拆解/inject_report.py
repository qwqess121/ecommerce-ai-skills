"""
报告注入器 - 将数据JSON注入HTML模板，生成最终报告
用法: python inject_report.py <data.json> [template.html] [output.html]

Token优化原理:
  旧方式: Claude每次写完整HTML (~600行 ~5000tokens)
  新方式: Claude只写数据JSON (~80行 ~800tokens), 模板复用
  节省: ~85% token
"""

import json, sys, os, re
from pathlib import Path

DEFAULT_TEMPLATE = str(Path(__file__).parent / '.claude/skills/v3-report-template/template.html')

def inject(data_path: str, template_path: str = None, output_path: str = None) -> str:
    # 读模板
    tpl_path = template_path or DEFAULT_TEMPLATE
    with open(tpl_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 读数据
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 注入: 在</script>之前插入 window.REPORT_DATA = {...};
    inject_js = f'\n<script>\nwindow.REPORT_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n</script>\n'

    # 找最后一个</script>前插入（在渲染JS之前定义数据）
    # 策略: 在第一个 <script> 标签前注入
    out = template.replace('<script>', inject_js + '<script>', 1)

    # 写输出
    if not output_path:
        stem = Path(data_path).stem.replace('_data', '').replace('data_', '')
        output_path = str(Path(data_path).parent / f'report_{stem}.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(out)

    size_kb = len(out.encode()) // 1024
    print(f'[inject] {data_path} → {output_path} ({size_kb} KB)')
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python inject_report.py <data.json> [template.html] [output.html]')
        sys.exit(1)

    data_file    = sys.argv[1]
    template_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file  = sys.argv[3] if len(sys.argv) > 3 else None

    out = inject(data_file, template_file, output_file)
    print(f'Report ready: {out}')
