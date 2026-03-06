#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资分析报告生成器
将分析数据渲染为专业级 PDF 报告（仅 PDF，不再生成 PNG）。

技术方案：Jinja2 渲染 HTML -> Playwright 导出 PDF
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("pip install jinja2")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("需要安装 playwright: pip install playwright")
    print("首次使用建议执行: python -m playwright install chromium")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"
WORKSPACE_DIR = SCRIPT_DIR.parent.parent


def find_browser_channel():
    """优先使用本机已安装的 Chrome/Edge channel。"""
    if os.path.isfile(r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        return "chrome"
    if os.path.isfile(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        return "chrome"
    if os.path.isfile(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"):
        return "msedge"
    return None


def html_to_pdf(html_path, pdf_path, browser_channel=None, width=1200):
    """使用 Playwright 渲染 HTML 并导出 PDF。"""
    html_uri = html_path.as_uri()
    launch_kwargs = {
        "headless": True,
        "args": ["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
    }
    if browser_channel:
        launch_kwargs["channel"] = browser_channel

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page(
                viewport={"width": width, "height": 3000},
                locale="zh-CN",
            )
            page.goto(html_uri, wait_until="networkidle", timeout=60000)
            page.emulate_media(media="print")
            # 等待字体与布局稳定，减少分页抖动
            page.wait_for_timeout(500)
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                display_header_footer=False,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
        print(f"PDF 已生成：{pdf_path}")
        return True
    except Exception as e:
        print(f"PDF 生成失败（Playwright）：{e}")
        return False


def render_report(input_json, output_dir=None, no_clean=False, timed=False):
    """渲染报告（仅 PDF）。timed=True 时打印各阶段耗时。"""
    t0 = time.perf_counter()
    # 加载数据
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if output_dir:
        base_dir = Path(output_dir) / f"reports/{datetime.now().strftime('%Y-%m-%d')}"
    else:
        ws = os.environ.get("OPENCLAW_WORKSPACE", "C:/Users/ice/.openclaw/workspace")
        base_dir = Path(ws) / f"reports/{datetime.now().strftime('%Y-%m-%d')}"
    base_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    html_content = template.render(**data)

    html_path = base_dir / f"{data['company_name']}_{data['date']}_value_analysis.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    t1 = time.perf_counter()
    if timed:
        print(f"[耗时] 加载 JSON + 渲染 HTML: {t1 - t0:.2f}s")

    browser_channel = find_browser_channel()
    t2 = time.perf_counter()
    if timed:
        print(f"[耗时] 检测浏览器 channel: {t2 - t1:.2f}s")

    pdf_path = base_dir / f"{data['company_name']}_{data['date']}_value_analysis.pdf"
    pdf_ok = html_to_pdf(html_path, pdf_path, browser_channel)
    t3 = time.perf_counter()
    if timed:
        print(f"[耗时] Playwright 导出 PDF: {t3 - t2:.2f}s")
        print(f"[耗时] 报告生成总耗时: {t3 - t0:.2f}s")
    
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
    
    if not no_clean:
        try:
            os.unlink(input_json)
            print(f"已清理输入文件：{input_json}")
            os.unlink(html_path)
            print(f"已清理 HTML 文件：{html_path}")
        except Exception:
            pass

    return pdf_ok


def main():
    parser = argparse.ArgumentParser(description="价值投资分析报告生成器（仅 PDF）")
    parser.add_argument("--input", "-i", help="输入 JSON 文件")
    parser.add_argument("--output", "-o", help="输出目录")
    parser.add_argument("--demo", action="store_true", help="演示模式")
    parser.add_argument("--no-clean", action="store_true", help="不删除输入 JSON 和临时 HTML（调试/计时用）")
    parser.add_argument("--timed", action="store_true", help="打印各阶段耗时")

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

    success = render_report(args.input, args.output, no_clean=args.no_clean, timed=args.timed)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
