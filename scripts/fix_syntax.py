import re

with open('generate_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 html_to_pdf 函数
old = '''    try:
        from PIL import Image
    Image.MAX_IMAGE_PIXELS = 500000000
    except ImportError:'''

new = '''    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 500000000  # 提升至 5 亿像素
    except ImportError:'''

content = content.replace(old, new)

with open('generate_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('已修复 html_to_pdf 函数语法')
