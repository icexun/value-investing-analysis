with open('generate_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 恢复窗口高度
content = content.replace('--window-size={width},32768', '--window-size={width},16384')

# 恢复缩放因子
content = content.replace('--force-device-scale-factor=4', '--force-device-scale-factor=2')

# 恢复超时时间
content = content.replace('timeout=120', 'timeout=30')

# 移除额外参数
content = content.replace("'--disable-dev-shm-usage',\n        ", '')
content = content.replace("'--lang=zh-CN',\n        ", '')

with open('generate_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('已恢复 PNG 生成参数到优化前状态')
