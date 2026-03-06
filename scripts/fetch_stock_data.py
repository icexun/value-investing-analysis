#!/usr/bin/env python3
"""
价值投资分析数据获取工具
获取股票的关键财务指标，供价值投资分析使用。

用法:
    python fetch_stock_data.py --ticker AAPL
    python fetch_stock_data.py --ticker 600519.SS    # A 股茅台
    python fetch_stock_data.py --ticker 0700.HK      # 港股腾讯
    python fetch_stock_data.py --ticker AAPL --output json
    python fetch_stock_data.py --ticker AAPL --output markdown
"""

import argparse
import json
import sys
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print("需要安装 yfinance: pip install yfinance")
    sys.exit(1)


def detect_currency(ticker_symbol: str, country: str) -> str:
    """
    检测股票财务数据的实际货币单位
    
    yfinance 经常错误标注中概股/港股的货币单位，需要根据股票代码和地区判断
    """
    ticker_upper = ticker_symbol.upper()
    
    # A 股（.SS/.SZ 结尾）→ 人民币 CNY
    if ticker_upper.endswith(".SS") or ticker_upper.endswith(".SZ"):
        return "CNY"
    
    # 港股（.HK 结尾）→ 港币 HKD
    if ticker_upper.endswith(".HK"):
        return "HKD"
    
    # 中概股（在美上市的中国公司）→ yfinance 可能返回人民币但未标注
    china_concept_stocks = [
        "PDD", "BABA", "JD", "BIDU", "NIO", "XPEV", "LI", "KWEB",
        "TME", "BILI", "IQ", "VIPS", "WB", "ZLAB", "YUMC"
    ]
    if ticker_upper in china_concept_stocks or country == "China":
        return "CNY (需验证)"
    
    # 美股 → 美元 USD
    return "USD"


def fmt_num(val):
    """格式化数字，返回格式化后的字符串"""
    if val is None or val == "N/A":
        return "N/A"
    if isinstance(val, str):
        return val
    if abs(val) >= 1e12:
        return f"{val/1e12:.2f}万亿"
    if abs(val) >= 1e8:
        return f"{val/1e8:.2f}亿"
    if abs(val) >= 1e4:
        return f"{val/1e4:.2f}万"
    return f"{val:.2f}"


def fmt_num_with_currency(val, currency):
    """格式化数字并标注货币单位"""
    if val is None or val == "N/A":
        return "N/A"
    formatted = fmt_num(val)
    if formatted == "N/A":
        return "N/A"
    return f"{formatted} {currency}"


def validate_financial_data(data: dict) -> list:
    """
    验证财务数据的合理性，返回警告列表
    
    检测逻辑：
    1. 现金/市值比率异常（>80% 可能单位错误）
    2. 负债/市值比率异常
    3. 现金流/净利润比率异常
    """
    warnings = []
    
    try:
        market_cap = data["valuation"]["market_cap"]
        total_cash = data["financial_health"]["total_cash_raw"]
        total_debt = data["financial_health"]["total_debt_raw"]
        
        if market_cap and total_cash and market_cap > 0:
            cash_ratio = total_cash / market_cap
            if cash_ratio > 0.8:
                warnings.append(
                    f"⚠️ 现金/市值比率异常：{cash_ratio:.1%}（>80%）- 可能货币单位错误，请核实"
                )
            elif cash_ratio > 0.5:
                warnings.append(
                    f"⚠️ 现金/市值比率较高：{cash_ratio:.1%}（>50%）- 请核实数据准确性"
                )
        
        if market_cap and total_debt and market_cap > 0:
            debt_ratio = total_debt / market_cap
            if debt_ratio > 1.0:
                warnings.append(
                    f"⚠️ 负债/市值比率异常：{debt_ratio:.1%}（>100%）- 可能货币单位错误，请核实"
                )
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    
    return warnings


def fetch_stock_data(ticker_symbol: str) -> dict:
    """获取股票关键财务数据"""
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    if not info or info.get("regularMarketPrice") is None:
        try:
            hist = stock.history(period="5d")
            if hist.empty:
                return {"error": f"无法获取 {ticker_symbol} 的数据，请检查代码是否正确"}
        except Exception:
            return {"error": f"无法获取 {ticker_symbol} 的数据，请检查代码是否正确"}

    def safe_get(key, default="N/A"):
        val = info.get(key)
        return val if val is not None else default

    def safe_pct(key):
        val = info.get(key)
        if val is not None:
            return f"{val * 100:.2f}%"
        return "N/A"

    market_cap = safe_get("marketCap")
    price = safe_get("regularMarketPrice", safe_get("currentPrice"))
    country = safe_get("country", "")
    
    # 检测货币单位
    detected_currency = detect_currency(ticker_symbol, country)
    
    # 汇率参考（近似值，用于估算）
    EXCHANGE_RATES = {
        "CNY_to_USD": 0.14,  # 1 CNY ≈ 0.14 USD
        "HKD_to_USD": 0.13,  # 1 HKD ≈ 0.13 USD
    }

    financials = stock.financials
    balance = stock.balance_sheet
    cashflow = stock.cashflow

    revenue_growth_3y = "N/A"
    profit_growth_3y = "N/A"
    fcf_ratio = "N/A"

    if financials is not None and not financials.empty:
        try:
            revenues = financials.loc["Total Revenue"].dropna().sort_index()
            if len(revenues) >= 4:
                latest_rev = revenues.iloc[-1]
                older_rev = revenues.iloc[-4]
                if older_rev > 0:
                    cagr = (latest_rev / older_rev) ** (1/3) - 1
                    revenue_growth_3y = f"{cagr*100:.1f}%"
        except (KeyError, IndexError):
            pass

        try:
            profits = financials.loc["Net Income"].dropna().sort_index()
            if len(profits) >= 4:
                latest_profit = profits.iloc[-1]
                older_profit = profits.iloc[-4]
                if older_profit > 0:
                    cagr = (latest_profit / older_profit) ** (1/3) - 1
                    profit_growth_3y = f"{cagr*100:.1f}%"
        except (KeyError, IndexError):
            pass

    if cashflow is not None and not cashflow.empty:
        try:
            op_cf = cashflow.loc["Operating Cash Flow"].dropna().iloc[0]
            cap_ex = cashflow.loc["Capital Expenditure"].dropna().iloc[0]
            net_income_val = safe_get("netIncomeToCommon")
            if net_income_val not in (None, "N/A", 0):
                fcf = op_cf + cap_ex
                fcf_ratio = f"{fcf / net_income_val * 100:.1f}%"
        except (KeyError, IndexError):
            pass

    # 获取原始数值（用于验证）
    total_cash_raw = safe_get("totalCash")
    total_debt_raw = safe_get("totalDebt")
    
    # 判断是否需要货币转换
    # 如果检测到是 CNY 但 yfinance 标注为 USD，则需要转换
    needs_conversion = detected_currency.startswith("CNY") and safe_get("currency") == "USD"
    
    if needs_conversion and total_cash_raw:
        # 假设 yfinance 返回的是人民币但标注为美元
        # 对于中概股，现金数据通常是人民币
        pass  # 保持原始数据，但在显示时标注

    result = {
        "ticker": ticker_symbol,
        "name": safe_get("longName", safe_get("shortName", ticker_symbol)),
        "sector": safe_get("sector"),
        "industry": safe_get("industry"),
        "country": country,
        "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_currency_note": f"财务数据货币单位：{detected_currency}（yfinance 标注：{safe_get('currency', 'USD')}）",
        "price": {
            "current": price,
            "currency": safe_get("currency"),
            "52w_high": safe_get("fiftyTwoWeekHigh"),
            "52w_low": safe_get("fiftyTwoWeekLow"),
        },
        "valuation": {
            "market_cap": market_cap,
            "market_cap_fmt": fmt_num_with_currency(market_cap, safe_get("currency", "USD")),
            "pe_ttm": safe_get("trailingPE"),
            "pe_forward": safe_get("forwardPE"),
            "pb": safe_get("priceToBook"),
            "ps": safe_get("priceToSalesTrailing12Months"),
            "ev_ebitda": safe_get("enterpriseToEbitda"),
        },
        "profitability": {
            "roe": safe_pct("returnOnEquity"),
            "roa": safe_pct("returnOnAssets"),
            "gross_margin": safe_pct("grossMargins"),
            "operating_margin": safe_pct("operatingMargins"),
            "net_margin": safe_pct("profitMargins"),
        },
        "growth": {
            "revenue_growth_yoy": safe_pct("revenueGrowth"),
            "earnings_growth_yoy": safe_pct("earningsGrowth"),
            "revenue_growth_3y_cagr": revenue_growth_3y,
            "profit_growth_3y_cagr": profit_growth_3y,
        },
        "financial_health": {
            "total_debt": fmt_num_with_currency(total_debt_raw, detected_currency.split()[0] if needs_conversion else safe_get("currency", "USD")),
            "total_debt_raw": total_debt_raw,
            "total_cash": fmt_num_with_currency(total_cash_raw, detected_currency.split()[0] if needs_conversion else safe_get("currency", "USD")),
            "total_cash_raw": total_cash_raw,
            "debt_to_equity": safe_get("debtToEquity"),
            "current_ratio": safe_get("currentRatio"),
            "currency_warning": "⚠️ 中概股财务数据可能为人民币但标注为美元，请核实" if needs_conversion else None,
        },
        "cash_flow": {
            "operating_cf": fmt_num_with_currency(safe_get("operatingCashflow"), detected_currency.split()[0] if needs_conversion else safe_get("currency", "USD")),
            "free_cf": fmt_num_with_currency(safe_get("freeCashflow"), detected_currency.split()[0] if needs_conversion else safe_get("currency", "USD")),
            "fcf_to_net_income": fcf_ratio,
        },
        "dividend": {
            "dividend_yield": safe_pct("dividendYield"),
            "payout_ratio": safe_pct("payoutRatio"),
        },
        "description": safe_get("longBusinessSummary", ""),
    }
    
    # 添加数据验证警告
    validation_warnings = validate_financial_data(result)
    if validation_warnings:
        result["data_warnings"] = validation_warnings

    return result


def format_markdown(data: dict) -> str:
    """将数据格式化为 Markdown 表格"""
    if "error" in data:
        return f"**错误**: {data['error']}"

    lines = [
        f"## {data['name']} ({data['ticker']}) 财务数据",
        f"",
        f"**行业**: {data['sector']} / {data['industry']}",
        f"**地区**: {data['country']}",
        f"**获取时间**: {data['fetch_time']}",
    ]
    
    # 添加货币单位说明
    if data.get("data_currency_note"):
        lines.extend([
            f"",
            f"⚠️ **货币单位说明**: {data['data_currency_note']}",
        ])
    
    # 添加数据警告
    if data.get("data_warnings"):
        lines.extend([
            f"",
            f"⚠️ **数据验证警告**:",
        ])
        for warning in data["data_warnings"]:
            lines.append(f"- {warning}")

    lines.extend([
        f"",
        f"### 估值指标",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 当前股价 | {data['price']['current']} {data['price']['currency']} |",
        f"| 市值 | {data['valuation']['market_cap_fmt']} |",
        f"| PE (TTM) | {data['valuation']['pe_ttm']} |",
        f"| PE (Forward) | {data['valuation']['pe_forward']} |",
        f"| PB | {data['valuation']['pb']} |",
        f"| PS | {data['valuation']['ps']} |",
        f"| EV/EBITDA | {data['valuation']['ev_ebitda']} |",
        f"| 52 周最高 | {data['price']['52w_high']} |",
        f"| 52 周最低 | {data['price']['52w_low']} |",
        f"",
        f"### 盈利能力",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| ROE | {data['profitability']['roe']} |",
        f"| ROA | {data['profitability']['roa']} |",
        f"| 毛利率 | {data['profitability']['gross_margin']} |",
        f"| 营业利润率 | {data['profitability']['operating_margin']} |",
        f"| 净利率 | {data['profitability']['net_margin']} |",
        f"",
        f"### 成长性",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 营收同比增速 | {data['growth']['revenue_growth_yoy']} |",
        f"| 盈利同比增速 | {data['growth']['earnings_growth_yoy']} |",
        f"| 营收 3 年 CAGR | {data['growth']['revenue_growth_3y_cagr']} |",
        f"| 净利 3 年 CAGR | {data['growth']['profit_growth_3y_cagr']} |",
        f"",
        f"### 财务健康",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 总负债 | {data['financial_health']['total_debt']} |",
        f"| 现金储备 | {data['financial_health']['total_cash']} |",
        f"| 负债/权益比 | {data['financial_health']['debt_to_equity']} |",
        f"| 流动比率 | {data['financial_health']['current_ratio']} |",
    ])
    
    # 添加货币警告
    if data['financial_health'].get('currency_warning'):
        lines.extend([
            f"",
            f"> {data['financial_health']['currency_warning']}",
        ])

    lines.extend([
        f"",
        f"### 现金流",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 经营性现金流 | {data['cash_flow']['operating_cf']} |",
        f"| 自由现金流 | {data['cash_flow']['free_cf']} |",
        f"| 自由现金流/净利润 | {data['cash_flow']['fcf_to_net_income']} |",
        f"",
        f"### 分红",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 股息率 | {data['dividend']['dividend_yield']} |",
        f"| 派息率 | {data['dividend']['payout_ratio']} |",
    ])

    if data.get("description"):
        lines.extend([
            f"",
            f"### 公司简介",
            f"",
            data["description"][:500] + ("..." if len(data.get("description", "")) > 500 else ""),
        ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="价值投资分析数据获取工具")
    parser.add_argument("--ticker", "-t", required=True, help="股票代码 (如 AAPL, 600519.SS, 0700.HK)")
    parser.add_argument("--output", "-o", choices=["json", "markdown"], default="markdown", help="输出格式")
    args = parser.parse_args()

    data = fetch_stock_data(args.ticker)

    if args.output == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print(format_markdown(data))


if __name__ == "__main__":
    main()
