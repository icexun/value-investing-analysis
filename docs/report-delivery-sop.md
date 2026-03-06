# 股票分析报告发送 SOP

## 场景
当使用 `value-investing-analysis` 技能生成股票分析报告（PDF/PNG）后，需要主动将报告文件发送给用户。

## 触发条件
- `generate_report.py` 成功执行，生成报告文件
- 报告路径：`reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis.{png|pdf}`

## 自动化流程（已实现 ✅）

### 报告生成时自动提取核心结论并生成发送指令
`generate_report.py` 在生成 PDF/PNG 后，会**自动提取核心结论**并生成一个发送指令文件：

```
reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis_send_instructions.json
```

该文件包含：
- 公司基本信息（名称、代码、评分、建议）
- 执行摘要
- **自动提取的 3 个核心结论**
- 文件路径（PNG/PDF）
- 预生成的消息模板（PNG/PDF caption）

### AI 助手发送流程
1. 报告生成成功后，AI 助手读取 `send_instructions.json` 文件（已包含**自动提取的 3 个核心结论**）
2. 使用 `message` 工具发送 PNG 和 PDF 文件
3. 使用预生成的 caption 模板（或稍作调整）

## 手动发送流程（备选）

### 1. 读取发送指令文件
```bash
# 查看发送指令
cat reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis_send_instructions.json
```

### 2. 发送 PNG 版本（预览图）
使用 `message` 工具发送 PNG 文件：

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "5198192317",
  "media": "reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis.png",
  "caption": "📊 {股票名称}价值投资分析报告（PNG 版）\n\n基于段永平 + 巴菲特价值投资体系，从商业模式、企业文化、估值三维度深度分析。\n\n综合评分：{X}/5 | 建议：{recommendation}"
}
```

### 3. 发送 PDF 版本（完整报告）
使用 `message` 工具发送 PDF 文件：

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "5198192317",
  "media": "reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis.pdf",
  "caption": "📄 {股票名称}价值投资分析报告（PDF 版）\n\n方便打印和存档的完整报告版本。\n\n核心结论：\n• {关键点 1}\n• {关键点 2}\n• {关键点 3}"
}
```

## 发送规范

### 文件路径格式
- **Windows**: `C:\Users\ice\.openclaw\workspace\reports\YYYY-MM-DD\{股票名称}_{日期}_value_analysis.{png|pdf}`
- **路径转义**: 在 JSON 中使用双反斜杠 `\\` 转义

### Caption 文案规范

#### PNG 版本
- 开头用 📊 emoji 标识
- 包含股票名称
- 说明是 PNG 预览版
- 提及分析框架（段永平 + 巴菲特）
- 包含综合评分和建议

#### PDF 版本
- 开头用 📄 emoji 标识
- 包含股票名称
- 说明是 PDF 完整版（方便打印/存档）
- 列出 3-4 个核心结论（bullet points，**自动生成报告时自动提取**）

### 发送顺序
1. 先发送 PNG（快速预览）
2. 再发送 PDF（完整存档）
3. 两条消息间隔无需等待，连续发送即可

## 示例：美团分析报告发送

### 自动生成的发送指令文件
```json
{
  "company": "美团",
  "ticker": "3690.HK",
  "score": 4,
  "recommendation": "值得关注",
  "key_points": [
    "商业模式顶级——本地生活网络效应 + 高频刚需，护城河宽",
    "估值处于低位——PE 13.98 倍接近历史最低，已反映大部分悲观预期",
    "财务健康——净现金 900 亿+，自由现金流转正，无生存风险"
  ],
  "message_templates": {
    "png_caption": "📊 美团价值投资分析报告（PNG 版）...",
    "pdf_caption": "📄 美团价值投资分析报告（PDF 版）..."
  }
}
```

### AI 助手执行发送
```json
// PNG 版本
{
  "action": "send",
  "channel": "telegram",
  "target": "5198192317",
  "media": "C:\\Users\\ice\\.openclaw\\workspace\\reports\\2026-03-05\\美团_2026-03-05_value_analysis.png",
  "caption": "📊 美团价值投资分析报告（PNG 版）\n\n基于段永平 + 巴菲特价值投资体系，从商业模式、企业文化、估值三维度深度分析。\n\n综合评分：4/5 | 建议：值得关注"
}

// PDF 版本
{
  "action": "send",
  "channel": "telegram",
  "target": "5198192317",
  "media": "C:\\Users\\ice\\.openclaw\\workspace\\reports\\2026-03-05\\美团_2026-03-05_value_analysis.pdf",
  "caption": "📄 美团价值投资分析报告（PDF 版）\n\n方便打印和存档的完整报告版本。\n\n核心结论：\n• 商业模式顶级——本地生活网络效应 + 高频刚需，护城河宽\n• 估值处于低位——PE 13.98 倍接近历史最低\n• 财务健康——净现金 900 亿+，自由现金流转正"
}
```

## 注意事项

1. **文件路径**: 确保路径正确，使用绝对路径
2. **中文字符**: 股票名称可能包含中文，确保路径编码正确
3. **文件大小**: PNG 约 2-3MB，PDF 约 1-2MB，Telegram 支持发送
4. **发送时机**: 报告生成成功后立即发送，避免遗忘
5. **用户偏好**: 如用户表示不需要某个格式，可只发送一个版本
6. **发送指令文件**: 报告生成后会自动生成（含**自动提取的核心结论**），无需手动编写 caption

---

**创建日期**: 2026-03-05  
**最后更新**: 2026-03-05（添加**自动提取**核心结论功能）  
**关联技能**: value-investing-analysis
