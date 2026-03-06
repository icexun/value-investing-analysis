#!/usr/bin/env python3
"""
测试货币单位修复逻辑
"""

def detect_currency(ticker_symbol: str, country: str) -> str:
    """检测股票财务数据的实际货币单位"""
    ticker_upper = ticker_symbol.upper()
    
    # A 股（.SS/.SZ 结尾）→ 人民币 CNY
    if ticker_upper.endswith(".SS") or ticker_upper.endswith(".SZ"):
        return "CNY"
    
    # 港股（.HK 结尾）→ 港币 HKD
    if ticker_upper.endswith(".HK"):
        return "HKD"
    
    # 中概股（在美上市的中国公司）
    china_concept_stocks = [
        "PDD", "BABA", "JD", "BIDU", "NIO", "XPEV", "LI", "KWEB",
        "TME", "BILI", "IQ", "VIPS", "WB", "ZLAB", "YUMC"
    ]
    if ticker_upper in china_concept_stocks or country == "China":
        return "CNY (需验证)"
    
    # 美股 → 美元 USD
    return "USD"


def test_stocks():
    """测试股票列表"""
    stocks = [
        ("PDD", "China", "CNY (需验证)"),
        ("BABA", "China", "CNY (需验证)"),
        ("600519.SS", "China", "CNY"),
        ("0700.HK", "China", "HKD"),
        ("AAPL", "United States", "USD"),
        ("META", "United States", "USD"),
        ("NVO", "Denmark", "USD"),
    ]
    
    print("货币单位检测测试")
    print("=" * 60)
    
    all_passed = True
    for ticker, country, expected in stocks:
        result = detect_currency(ticker, country)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"{status} {ticker:12} ({country:15}) -> {result:15} (expected: {expected})")
    
    print("=" * 60)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED, please check logic")
    
    # 测试 PDD 数据验证
    print("\nPDD 数据验证示例")
    print("=" * 60)
    total_cash_cny = 4237.69  # 亿人民币
    market_cap_usd = 1430.15  # 亿美元
    exchange_rate = 0.14  # CNY to USD
    
    cash_usd = total_cash_cny * exchange_rate
    cash_ratio = cash_usd / market_cap_usd
    
    print(f"总现金：{total_cash_cny:.2f}亿人民币 ≈ {cash_usd:.2f}亿美元")
    print(f"市值：{market_cap_usd:.2f}亿美元")
    print(f"现金/市值比率：{cash_ratio:.1%}")
    
    if cash_ratio > 0.8:
        print("WARNING: Cash/Market Cap ratio abnormal (>80%)")
    elif cash_ratio > 0.5:
        print("WARNING: Cash/Market Cap ratio high (>50%)")
    else:
        print("OK: Cash/Market Cap ratio reasonable")
    
    print("=" * 60)


if __name__ == "__main__":
    test_stocks()
