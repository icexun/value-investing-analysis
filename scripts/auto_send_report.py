#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票报告自动发送辅助脚本
读取 send_instructions.json，输出 message 工具调用指令。

用法:
    python auto_send_report.py reports/2026-03-05/美团_2026-03-05_value_analysis_send_instructions.json

输出:
    打印 message 工具调用所需的 JSON 指令
"""

import json
import sys
import os
import io

# 设置 stdout 为 UTF-8 编码（Windows 兼容）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def load_instructions(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_message_call(instructions, file_type='png'):
    """生成 message 工具调用指令"""
    file_path = instructions['files'].get(file_type)
    if not file_path:
        return None
    
    caption = instructions['message_templates'].get(f'{file_type}_caption')
    
    # 转换为 Windows 路径格式（如果需要）
    if os.name == 'nt':
        file_path = file_path.replace('/', '\\')
    
    return {
        "action": "send",
        "channel": "telegram",
        "target": "5198192317",
        "media": file_path,
        "caption": caption.replace('\\n', '\n')
    }

def main():
    if len(sys.argv) < 2:
        print("用法：python auto_send_report.py <send_instructions.json 路径>")
        sys.exit(1)
    
    instructions_path = sys.argv[1]
    if not os.path.exists(instructions_path):
        print(f"错误：文件不存在：{instructions_path}")
        sys.exit(1)
    
    instructions = load_instructions(instructions_path)
    
    print("=" * 60)
    print(f"[PNG] {instructions['company']} ({instructions['ticker']}) 报告发送指令")
    print("=" * 60)
    print(f"综合评分：{instructions['score']}/5")
    print(f"建议：{instructions['recommendation']}")
    print(f"核心结论：{len(instructions['key_points'])} 条")
    print()
    
    # PNG 发送指令
    png_call = format_message_call(instructions, 'png')
    if png_call:
        print("【PNG 发送指令】")
        print(json.dumps(png_call, ensure_ascii=False, indent=2))
        print()
    
    # PDF 发送指令
    pdf_call = format_message_call(instructions, 'pdf')
    if pdf_call:
        print("【PDF 发送指令】")
        print(json.dumps(pdf_call, ensure_ascii=False, indent=2))
        print()
    
    print("=" * 60)
    print("💡 提示：将上述 JSON 传给 message 工具即可发送报告")

if __name__ == "__main__":
    main()
