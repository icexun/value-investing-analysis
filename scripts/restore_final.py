with open('generate_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 html_to_png 函数并修复
for i, line in enumerate(lines):
    # 恢复宽度为 1200
    if 'def html_to_png' in line and 'width=' in line:
        lines[i] = line.replace('width=1600', 'width=1200')
    # 移除额外参数
    if "'--disable-dev-shm-usage'," in line:
        lines[i] = ''
    if "'--lang=zh-CN'," in line:
        lines[i] = ''
    # 恢复超时时间
    if 'timeout=120' in line:
        lines[i] = line.replace('timeout=120', 'timeout=30')

with open('generate_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('已完全恢复到优化前状态')
