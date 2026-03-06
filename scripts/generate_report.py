#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资分析报告生成器
将分析数据渲染为专业级 PDF 报告（仅 PDF，不再生成 PNG）。

技术方案：Jinja2 渲染 HTML -> Chrome Headless 直接打印 PDF
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("pip install jinja2")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"
WORKSPACE_DIR = SCRIPT_DIR.parent.parent


def find_browser():
    """查找可用的 Chrome/Edge 浏览器"""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def html_to_pdf(html_path, pdf_path, browser, width=1200):
    """Chrome headless 直接打印 PDF（高清）"""
    if not browser:
        print("错误：未找到浏览器")
        return False
    
    html_str = str(html_path)
    cmd = [
        browser, "--headless", "--disable-gpu", "--no-sandbox",
        f"--print-to-pdf={pdf_path}",
        f"--window-size={width},30000",
        "--hide-scrollbars", "--force-device-scale-factor=2",
        "--disable-dev-shm-usage", "--lang=zh-CN",
        "--virtual-time-budget=5000",
        "--pdf-paper-size=A4", "--pdf-margin-top=10", "--pdf-margin-bottom=10",
        "--pdf-margin-left=10", "--pdf-margin-right=10",
        html_str if html_str.startswith('file:') else f"file://{os.path.abspath(html_str)}",
    ]
    
    proc = subprocess.run(cmd, capture_output=True, timeout=90, text=True)
    if proc.returncode != 0:
        print(f"PDF 生成失败：{proc.stderr[:500]}")
        return False
    
    print(f"PDF 已生成：{pdf_path}")
    return True


def render_report(input_json, output_dir=None):
    """渲染报告（仅 PDF）"""
    # 加载数据
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 设置输出目录
    if output_dir:
        base_dir = Path(output_dir) / f"reports/{datetime.now().strftime('%Y-%m-%d')}"
    else:
        ws = os.environ.get("OPENCLAW_WORKSPACE", "C:/Users/ice/.openclaw/workspace")
        base_dir = Path(ws) / f"reports/{datetime.now().strftime('%Y-%m-%d')}"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 渲染 HTML
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    html_content = template.render(**data)
    
    html_path = base_dir / f"{data['company_name']}_{data['date']}_value_analysis.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # 查找浏览器
    browser = find_browser()
    
    # 生成 PDF
    pdf_path = base_dir / f"{data['company_name']}_{data['date']}_value_analysis.pdf"
    pdf_ok = html_to_pdf(html_path, pdf_path, browser)
    
    # 生成发送指令（仅 PDF）
    if pdf_ok:
        send_data = {
            "created_at": datetime.now().isoformat(),
            "company": data["company_name"],
            "ticker": data["ticker"],
            "score": data["overall_score"],
            "recommendation": data["recommendation"],
            "executive_summary": data["executive_summary"],
            "key_points": data["conclusion_reasons"][:3],
            "files": {
                "png": None,
                "pdf": str(pdf_path),
            },
            "message_templates": {
                "pdf_caption": f"📄 {data['company_name']}价值投资分析报告（PDF 版）\n\n基于段永平 + 巴菲特价值投资体系，从商业模式、企业文化、估值三维度深度分析。\n\n综合评分：{data['overall_score']}/5 | 建议：{data['recommendation']}\n\n核心结论：\n" + "\n".join([f"• {p}" for p in data["conclusion_reasons"][:3]]),
            }
        }
        send_path = base_dir / f"{data['company_name']}_{data['date']}_value_analysis_send_instructions.json"
        with open(send_path, 'w', encoding='utf-8') as f:
            json.dump(send_data, f, ensure_ascii=False, indent=2)
        print(f"发送指令已生成：{send_path}")
    
    # 清理中间文件
    try:
        os.unlink(input_json)
        print(f"已清理输入文件：{input_json}")
        # 删除 HTML 临时文件
        os.unlink(html_path)
        print(f"已清理 HTML 文件：{html_path}")
    except:
        pass
    
    return pdf_ok


def main():
    parser = argparse.ArgumentParser(description="价值投资分析报告生成器（仅 PDF）")
    parser.add_argument("--input", "-i", help="输入 JSON 文件")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--demo", action="store_true", help="演示模式")
    
    args = parser.parse_args()
    
    if args.demo:
        demo_json = SCRIPT_DIR.parent / "samples/0700_analysis.json"
        if demo_json.exists():
            args.input = str(demo_json)
        else:
            print("未找到演示文件")
            sys.exit(1)
    
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    if not os.path.exists(args.input):
        print(f"文件不存在：{args.input}")
        sys.exit(1)
    
    success = render_report(args.input, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
