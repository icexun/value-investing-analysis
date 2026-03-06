with open('generate_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 if output_format in ("png", "both"): 之后添加 pdf_path 初始化
old = '''        if output_format in ("png", "both"):
            size = os.path.getsize(png_path)
            print(f"PNG 已生成：{png_path} ({size:,} bytes)")

        if output_format in ("pdf", "both"):'''

new = '''        pdf_path = None
        if output_format in ("png", "both"):
            size = os.path.getsize(png_path)
            print(f"PNG 已生成：{png_path} ({size:,} bytes)")

        if output_format in ("pdf", "both"):'''

content = content.replace(old, new)

with open('generate_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('已修复 pdf_path 未定义问题')
