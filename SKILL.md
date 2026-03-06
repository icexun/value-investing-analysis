---
name: value-investing-analysis
version: 2.1.0
description: "基于段永平和巴菲特价值投资理念的股票深度分析工具。当用户提到分析股票、价值投资、某只股票值不值得买、段永平怎么看、巴菲特视角等关键词时触发。从商业模式、企业文化、估值三大维度进行系统性分析，并生成专业级 PDF 研报。"
author: ice
---

# 价值投资深度分析

**基于段永平 + 巴菲特投资体系，对一只股票进行系统性价值分析。**

核心信仰：买股票就是买公司，买公司就是买其未来现金流折现。

---

## 分析触发条件

当用户提出以下类型请求时触发本技能：
- "分析XX股票"、"XX值不值得投资"
- "用价值投资视角看XX"、"段永平/巴菲特会怎么看XX"
- "XX的商业模式怎么样"、"XX的护城河如何"
- 任何涉及个股价值分析的请求

---

## 分析流程

### ⚠️ 重要说明：技能架构边界

本技能采用**人机协作**设计：

| 脚本 | 职责 | 自动化程度 |
|------|------|-----------|
| `fetch_stock_data.py` | 获取财务数据（来自 yfinance） | ✅ 全自动 |
| **AI 分析** | 生成定性分析内容（商业模式/文化/估值） | 🤖 需要 AI 参与 |
| `generate_report.py` | 从完整 JSON 生成 PDF | ✅ 全自动 |

**`fetch_stock_data.py` 只能获取财务数据**，无法自动生成定性分析。完整报告需要 AI 基于财务数据 + 认知，生成三维度分析内容。

---

### 第一步：数据获取

使用 `scripts/fetch_stock_data.py` 获取目标公司的关键财务数据：

```bash
python scripts/fetch_stock_data.py --ticker AAPL
python scripts/fetch_stock_data.py --ticker AAPL --output json
```

核心指标：市值、股价、PE/PB/PS、ROE、毛利率、净利率、资产负债率、自由现金流、分红/回购等。

#### ⚠️ 货币单位说明（重要）

**yfinance 对中概股/港股的财务数据货币单位标注经常错误**，已修复：

| 股票类型 | 示例 | 实际货币 | yfinance 标注 | 修复方式 |
|---------|------|---------|-------------|---------|
| A 股 | 600519.SS | CNY | CNY ✅ | 无需修复 |
| 港股 | 0700.HK | HKD | HKD ✅ | 无需修复 |
| 中概股 | PDD, BABA, JD | CNY | USD ❌ | 自动检测并标注 |
| 美股 | AAPL, META | USD | USD ✅ | 无需修复 |

**修复后**：
- `fetch_stock_data.py` 会自动检测中概股，标注"财务数据货币单位：CNY (需验证)"
- 添加数据验证：现金/市值比率>80% 时发出警告
- JSON 输出包含 `data_currency_note` 和 `data_warnings` 字段

**AI 分析时请注意**：
- 如果看到 `data_warnings`，请核实数据准确性
- 中概股的现金、负债、现金流数据单位是**人民币**，不是美元
- 市值单位是**美元**（yfinance 正确标注）

### 第二步：三维度分析 → 构建 JSON

**这一步需要 AI 参与**，无法自动化。

按照 **Right Business → Right People → Right Price** 的顺序，结合财务数据和对公司的认知，完成三大维度的定性分析。每个维度需言之有物、直达本质，避免空洞辞藻。

分析完成后，将所有内容组织为 JSON 文件（数据结构见下文"JSON 数据结构"章节），保存为 `{ticker}_analysis.json`。

**推荐做法：** 让 AI 助手直接生成完整 JSON，例如：
> "请用价值投资技能分析腾讯，生成完整的 analysis.json 文件"

### 第三步：生成专业报告（仅 PDF）

报告**统一存放在专用目录**，按**天**建子目录，便于管理：

- 默认路径：`{工作区}/reports/YYYY-MM-DD/`（例如 `reports/2026-03-05/`）
- 可通过 `--output` 指定报告根目录，报告仍会落在 `根目录/reports/YYYY-MM-DD/` 下

```bash
# 用完整分析 JSON 生成 PDF 报告
python scripts/generate_report.py --input {ticker}_analysis.json
# 使用样例试跑：--input samples/0700_analysis.json

# 指定报告根目录（报告落在 指定路径/reports/YYYY-MM-DD/）
python scripts/generate_report.py --input {ticker}_analysis.json --output /path/to/base
```

报告生成后：
- **输入 JSON** 会在成功生成后**自动删除**，避免遗留中间文件。
- **HTML 临时文件** 会在 PDF 生成后自动删除。
- **自动生成发送指令文件**：`reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis_send_instructions.json`（包含核心结论和预生成的 caption 模板）

依赖安装：`pip install jinja2`（使用系统 Edge/Chrome 浏览器 Headless 模式直接打印 PDF）

### 第四步：发送报告给用户 📤

**报告生成成功后，立即执行发送流程。**

按照 `docs/report-delivery-sop.md` 执行：

1. **读取发送指令文件**：`reports/YYYY-MM-DD/{股票名称}_{日期}_value_analysis_send_instructions.json`
   - 获取自动提取的 3 个核心结论
   - 获取预生成的 caption 模板

2. **发送 PDF 版本**（完整存档）：
   - 使用 `message` 工具发送 PDF 文件
   - 使用预生成的 `pdf_caption` 模板（包含 3 个核心结论）

**发送规范**：
- 使用绝对路径（Windows 注意路径转义）

**示例**：
```json
// 读取发送指令文件
{
  "company": "福耀玻璃",
  "ticker": "600660.SS",
  "score": 4.0,
  "recommendation": "值得关注",
  "key_points": ["核心结论 1", "核心结论 2", "核心结论 3"],
  "message_templates": {
    "png_caption": "📊 福耀玻璃价值投资分析报告（PNG 版）...",
    "pdf_caption": "📄 福耀玻璃价值投资分析报告（PDF 版）..."
  }
}
```

---

## 维度一：商业模式（Right Business）

这是最重要的维度。段永平："老巴说生意模式最重要。这句话值 100 顿午餐。"

### 1.1 生意模式本质

回答以下问题：
- 公司靠什么赚钱？净现金流从何而来？
- 这个模式能不能长期持续产生大量净现金流？
- 是不是"好的生意模式就是能长期产生很多净现金流的模式"？

判断标准：好的生意模式 = 轻资产 + 高毛利 + 强定价权 + 可重复。

### 1.2 差异化

段永平："没有差异化产品的商业模式基本不是好的商业模式。"

检查清单：
- 产品/服务有什么差异化？用户需要但竞争对手满足不了的是什么？
- 是否在追求"性价比"？（追求性价比的公司大多在为低价找借口）
- 差异化是否可持续？能否长期维持？
- 行业是否类似航空/光伏（产品无差异化，只能价格战）？

### 1.3 护城河

护城河是生意模式的一部分。好的生意模式往往具有很宽的护城河。

评估维度：
| 护城河类型 | 检查要点 |
|-----------|---------|
| 品牌忠诚度 | 用户是否因品牌而非价格购买？转换意愿低？ |
| 转换成本 | 用户切换到竞品的成本有多高？ |
| 网络效应 | 用户越多产品越有价值？ |
| 规模优势 | 规模带来的成本优势是否显著且可持续？ |
| 技术/专利 | 是否有难以复制的技术壁垒？ |
| 特许经营权 | 是否有牌照/许可/独占资源？ |

### 1.4 长长的坡，厚厚的雪

段永平："长长的坡不光指行业，还包括企业本身能否长跑，所以企业文化很重要。"

- 行业天花板够不够高？坡够不够长？
- 雪够不够厚？（利润率、定价权）
- 是否属于"短短的坡少少的雪"要回避的类型？

### 1.5 资本结构

- 资本支出占收入比重？是不是"资本黑洞"（利润全部再投入都不够）？
- 负债水平如何？有无长期有息贷款？
- 段永平："资本支出大的行业不容易出现好企业。"
- 段永平："我个人一般对有负债的公司不太愿意重仓。"

---

## 维度二：企业文化（Right People）

段永平："好的商业模式加好的企业文化一般是好公司的特征。"

### 2.1 管理层：造钟人还是报时人？

- CEO 是在建立可传世的企业文化和系统（造钟人），还是靠个人魅力驱动（报时人）？
- 段永平："从5年10年的角度看CEO至关重要，从10-50年角度看董事会很重要，从更长角度看企业文化更重要。"
- 判断管理层是否"不对"比判断是否"对"更容易，不对的就不碰。
- 正直和诚信（integrity）是所有 great 企业的共性。

### 2.2 利润之上的追求

- 公司是否有超越利润的价值追求？是消费者导向还是利润导向？
- 段永平："利润之上的追求指的是把消费者需求放在公司短期利益前面。"
- "真正好的能持续经营的企业大多不是着眼于利润的，利润不过是水到渠成的结果。"
- 有"利润之上追求"的企业成为好企业的概率大很多，时间越长差别越大。

### 2.3 企业文化健康度

- 是否有清晰的 Stop Doing List（知道什么不该做）？
- 企业文化是否支撑长期发展？
- 做销售的人经营公司时，做产品的人就不再重要——这是衰败的信号。

---

## 维度三：估值（Right Price）

段永平："right price 没那么重要，因为时间可以降低其重要性。"但不能完全忽略。

### 3.1 未来现金流毛估估

未来现金流折现是思维方式，不是公式。千万不要套公式。

- 5-10年后这家公司一年能赚多少钱？（大致判断，毛估估）
- 基于什么逻辑？行业增速？市场份额？定价能力？
- 这个判断有多大把握？是在能力圈内还是在猜？

### 3.2 当前估值

- 当前市值相对于未来盈利能力是否合理？
- 是否满足"四毛买一块"的安全边际？
- 和无风险回报率（国债利率）比，持有这家公司的机会成本如何？
- 段永平："以一般的价格买下一家非同一般的好公司，要比用非同一般的好价格买下一家一般的公司好得多。"

### 3.3 十年思维

- 能不能想清楚这家公司10年后的样子？
- "如果你不想拥有一家公司十年，你甚至不要拥有一分钟。"
- 封仓十年你敢不敢？如果不敢，要想清楚为什么。

---

## 风险检查清单（Stop Doing List 过滤器）

以下任何一条命中，都应该认真考虑是否要回避：

- [ ] 我是否真的看懂了这家公司？（不懂不做是第一原则）
- [ ] 公司是否有做假账的嫌疑？
- [ ] 管理层是否有诚信问题？
- [ ] 行业是否缺乏差异化（航空/光伏式陷阱）？
- [ ] 公司是否高负债或过度依赖杠杆？
- [ ] 是否存在 CEO 离开公司就不行的风险（报时人依赖）？
- [ ] 产品是否有被颠覆的风险？
- [ ] 我是不是因为股价涨了才想买？（追涨是投机）
- [ ] 是不是在追求"性价比"而非真正的差异化？
- [ ] 我是不是在试图走捷径？

---

## JSON 数据结构

分析完成后，将所有内容组织为以下 JSON 结构。该 JSON 将直接传给 `generate_report.py --input` 生成报告。

**标注说明：** `[必填]` = 报告核心内容；`[可选]` = 有则更好，没有也不影响报告生成。

```json
{
  "company_name": "公司名称",                    // [必填]
  "ticker": "AAPL",                             // [必填] 股票代码
  "exchange": "NASDAQ",                          // [必填] 交易所
  "industry": "消费电子 / 科技",                   // [必填] 行业/板块
  "date": "2026-03-05",                          // [必填] 分析日期
  "recommendation": "值得关注",                    // [必填] 深度研究/值得关注/可分批建仓/买入/观望等待/观望/回避/强烈回避/能力圈外
  "overall_score": 4.5,                           // [必填] 综合评分 1-5，支持 0.5

  "executive_summary": "一句话判断...",             // [必填] 核心结论，1-3句话

  // ===== 仪表盘指标（8个卡片）=====
  "metrics": {                                    // [必填]
    "market_cap": "3.87万亿", "pe_ttm": 33.3, "roe": "152.0%",
    "gross_margin": "47.3%", "net_margin": "27.0%",
    "debt_equity": 102.6, "fcf_ratio": "83.9%", "dividend_yield": "0.39%"
  },

  // ===== 详细财务数据表（指标/数值/说明三列）=====
  "financial_table": [                            // [可选] 不提供则不显示此表
    {"label": "市值", "value": "4.56万亿港元", "note": "中国市值最大互联网公司"},
    {"label": "PE (TTM)", "value": "20.04", "note": "历史低位"}
    // ... 可添加任意多行
  ],

  // ===== 维度一：商业模式 =====
  "business_model": {
    "score": 5,                                   // [必填] 1-5
    "model": "概述段落...",                          // [必填] 生意模式概述
    "model_points": ["要点1", "要点2"],             // [可选] 核心逻辑要点列表
    "cashflow_points": ["现金流特征1", "..."],       // [可选] 现金流特征列表
    "model_quote": {"text": "引言", "author": "段永平"},  // [可选] 生意模式相关引用

    "differentiation": "差异化概述...",               // [必填]
    "diff_table": [                                // [可选] 差异化维度表格
      {"dimension": "维度名", "note": "说明"}
    ],
    "diff_highlight": "最核心差异化一句话",            // [可选] 高亮框

    "moat_table": [                                // [可选] 护城河星级评估表
      {"type": "品牌忠诚度", "rating": 5, "note": "说明"},
      {"type": "转换成本", "rating": 4, "note": "说明"}
    ],
    "moat_summary": "护城河总评...",                  // [可选] 高亮框

    "runway_space": ["行业空间要点1", "..."],          // [可选] 行业空间列表
    "runway_snow": ["雪厚要点1", "..."],              // [可选] 雪厚列表
    "runway_summary": "坡和雪的总评...",               // [可选] 高亮框

    "capital": "资本结构分析文本...",                   // [必填]（若提供 capital_points 则此字段可省略）
    "capital_points": ["要点1", "..."],               // [可选] 优先使用列表形式

    "quote": {"text": "引言", "author": "段永平"}     // [可选] 维度总引用
  },

  // ===== 维度二：企业文化 =====
  "culture": {
    "score": 4,                                    // [必填] 1-5
    "management": "管理层概述...",                     // [必填]
    "management_points": ["要点1", "..."],            // [可选]
    "clockmaker": "造钟人评价...",                     // [可选] 高亮框

    "purpose": "利润之上的追求概述...",                  // [必填]
    "purpose_points": ["要点1", "..."],               // [可选]
    "purpose_assessment": "消费者导向 vs 利润导向评价",  // [可选] 高亮框

    "health": "企业文化健康度概述...",                   // [必填]
    "culture_points": ["文化特点1", "..."],            // [可选]
    "stop_doing": ["不做的事1", "..."],                // [可选] Stop Doing List

    "quote": {"text": "引言", "author": "段永平"}      // [可选]
  },

  // ===== 维度三：估值 =====
  "valuation": {
    "score": 4,                                     // [必填] 1-5
    "future_cashflow": "未来现金流概述...",              // [必填]
    "assumptions": ["假设1", "..."],                  // [可选]
    "projections": ["展望1", "..."],                  // [可选]

    "current_valuation": "当前估值概述...",              // [必填]
    "valuation_table": [                             // [可选] 估值对比表（含历史分位）
      {"label": "PE (TTM)", "value": "20.04", "percentile": "~10%分位", "assessment": "历史极低"}
    ],
    "safety_margin": "安全边际评价...",                  // [可选] 高亮框

    "ten_year": "十年思维概述...",                       // [必填]
    "scenarios": [                                    // [可选] 情景分析（乐观/中性/悲观三列卡片）
      {
        "type": "optimistic",                         // optimistic / neutral / pessimistic
        "title": "乐观情景",
        "probability": "40%",
        "points": ["要点1", "要点2"]
      }
    ],
    "dare": "封仓十年敢不敢的判断...",                    // [可选] 高亮框

    "quote": {"text": "引言", "author": "巴菲特"}       // [可选]
  },

  // ===== 风险检查 =====
  "risk_checks": [                                    // [必填]
    {"item": "是否真看懂了？", "status": "pass", "note": "说明"},
    {"item": "被颠覆风险？", "status": "warn", "note": "说明"}
    // status: pass / warn / fail
  ],
  "policy_risks": ["政策风险1", "..."],                 // [可选] 政策风险额外关注（橙色警告框）

  // ===== 最终结论 =====
  "conclusion_reasons": [                              // [必填] 核心理由列表，支持 <strong> 标签加粗
    "<strong>商业模式顶级</strong>——说明...",
    "<strong>估值合理</strong>——说明..."
  ],
  "duan_view": "段永平视角评价...",                       // [必填] 段永平可能怎么看
  "buffett_view": "巴菲特视角评价...",                    // [可选] 巴菲特可能怎么看
  "next_steps": ["建议1", "建议2"],                     // [可选] 下一步建议
  "supplement": "补充说明文字..."                         // [可选] 底部补充说明
}
```

**分析引用：** 每个维度可附带 1 条段永平/巴菲特经典语录（从 `references/quotes.md` 中选取），全篇引用 3-5 条为宜。

---

## 重要原则

### 诚实原则

如果公司超出能力圈，**必须明确说"我看不懂"**。这本身就是最重要的价值投资原则。段永平："不懂不做。所谓懂投资的真正含义是懂得不投不懂的东西。"

宁可错过一个好机会，也不要在不懂的地方犯错。"用我这个办法投资一生可能会失去无数机会，但犯大错的机会也很少。"

### 风格原则

- 像段永平回答问题的风格：直接、本质、不绕弯子
- 避免华丽辞藻和空洞分析
- 不做无根据的乐观或悲观判断
- 有数据说数据，有逻辑说逻辑，看不懂就直说

### 不做的事情

- 不预测股价走势和短期涨跌
- 不推荐买卖时点
- 不做技术分析（看图看线）
- 不做宏观预测
- 不做行业轮动建议
- 不因为别人买了就推荐

---

## 快速使用指南

### 场景 1：让 AI 生成完整分析报告（推荐）

```
"请用价值投资技能分析阿里巴巴，生成 PDF 和 PNG 报告"
```

AI 会：
1. 调用 `fetch_stock_data.py` 获取财务数据
2. 生成完整的三维度分析内容
3. 构建完整的 JSON 文件
4. 调用 `generate_report.py` 生成 PDF/PNG

### 场景 2：仅获取财务数据

```bash
python scripts/fetch_stock_data.py --ticker BABA --output json
```

输出仅包含财务数据，不包含定性分析。

### 场景 3：从已有 JSON 生成报告

```bash
python scripts/generate_report.py --input BABA_analysis.json --format both
```

**注意：** JSON 文件必须包含完整的三维度分析内容，否则报告会显示"待分析"。

### 场景 4：查看样例

```bash
# 查看腾讯完整分析样例
python scripts/generate_report.py --input samples/0700_analysis.json --format png
```

---

## 常见问题

### Q: 为什么生成的报告里分析内容都是"待分析"？

**A:** `fetch_stock_data.py` 只能获取财务数据，无法自动生成定性分析。需要 AI 基于财务数据 + 认知，生成完整的三维度分析内容（商业模式、企业文化、估值）。

**解决方案：** 让 AI 助手生成完整的 analysis.json 文件，再用 `generate_report.py` 转换。

### Q: 完整的 JSON 文件应该包含哪些字段？

**A:** 参考 `samples/0700_analysis.json`（腾讯完整样例）。必需字段包括：

```json
{
  "financial_table": [],      // 详细财务数据表格（17 项）
  "business_model": {
    "model_points": [],       // 商业模式要点
    "cashflow_points": [],    // 现金流特征要点
    "diff_table": [],         // 差异化维度表格
    "moat_table": [],         // 护城河 6 维度评分表
    "runway_space": [],       // 行业空间要点
    "runway_snow": []         // 利润率要点
  },
  "culture": {
    "management_points": [],  // 管理层要点
    "purpose_points": [],     // 价值观要点
    "culture_points": [],     // 文化健康度要点
    "stop_doing": []          // Stop Doing List
  },
  "valuation": {
    "assumptions": [],        // 现金流假设
    "projections": [],        // 5 年预测
    "valuation_table": [],    // 估值对比表
    "scenarios": []           // 3 种情景分析
  },
  "risk_checks": [],          // 8 项风险检查
  "conclusion_reasons": []    // 结论理由
}
```

### Q: 能否自动化生成完整报告？

**A:** 当前设计采用**人机协作**模式：
- 财务数据获取：全自动（yfinance）
- 定性分析：需要 AI 参与（无法自动化）
- 报告生成：全自动（Jinja2 + 浏览器）

未来可能添加一键脚本，但目前需要 AI 生成完整 JSON。

---

## 附加资源

- 投资哲学详细参考：[references/philosophy.md](references/philosophy.md)
- 段永平/巴菲特经典语录库：[references/quotes.md](references/quotes.md)
- 数据获取脚本：[scripts/fetch_stock_data.py](scripts/fetch_stock_data.py)
- 报告生成脚本：[scripts/generate_report.py](scripts/generate_report.py)
- 报告 HTML 模板：[scripts/templates/report.html](scripts/templates/report.html)
- **腾讯分析样例（完整 JSON）**：[samples/0700_analysis.json](samples/0700_analysis.json) ⭐ 推荐参考

### 依赖安装

```bash
pip install jinja2 yfinance Pillow
```

系统还需要 Edge 或 Chrome 浏览器（Headless 模式用于 HTML → PNG 转换）。

---

*"买股票就是买公司，买公司就是买公司的未来现金流折现，句号！" —— 段永平*
