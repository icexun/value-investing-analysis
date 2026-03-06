with open('generate_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到第 94 行（索引 93）并修复缩进
for i, line in enumerate(lines):
    if 'Image.MAX_IMAGE_PIXELS' in line and line.startswith('    Image.'):
        # 修复为正确的缩进（8 个空格）
        lines[i] = '        Image.MAX_IMAGE_PIXELS = 500000000  # 提升至 5 亿像素\n'
        print(f'已修复第 {i+1} 行')
        break

with open('generate_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('修复完成')
