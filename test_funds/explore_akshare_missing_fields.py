"""
深度探索 akshare 接口，查找缺失字段
缺失字段: 前一日净值、涨跌额、申购状态、基金经理、基金总份额
"""

import akshare as ak
import pandas as pd

print("="*80)
print("探索 akshare 缺失字段的获取方法")
print("="*80)

test_code = "000001"  # 华夏成长
print(f"\n测试基金代码: {test_code}\n")

# 缺失字段列表
missing_fields = {
    'yesterday_nav': '前一日净值',
    'nav_a': '涨跌额',
    'sg_states': '申购状态',
    'fund_manager': '基金经理',
    'jjzfe': '基金总份额'
}

print("需要查找的字段:")
for i, (k, v) in enumerate(missing_fields.items(), 1):
    print(f"{i}. {k:15s} - {v}")

# 1. 历史净值数据（可能包含前一日净值）
print("\n" + "="*80)
print("1. fund_open_fund_info_em() - 基金信息（各种指标）")
print("="*80)

indicators = ["单位净值走势", "累计净值走势", "累计收益率走势", "同类排名走势", 
              "同类排名百分比走势", "分红送配详情", "拆分详情", "基金规模走势"]

for indicator in indicators[:3]:  # 先测试前3个
    try:
        print(f"\n测试指标: {indicator}")
        df = ak.fund_open_fund_info_em(fund=test_code, indicator=indicator)
        print(f"  ✓ 成功! 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  数据行数: {len(df)}")
            print(f"  最近2条:")
            print(df.head(2))
            
            # 检查是否可以获取前一日净值
            if '净值日期' in df.columns and '单位净值' in df.columns:
                if len(df) >= 2:
                    print(f"\n  ✅ 可获取前一日净值!")
                    print(f"     当日: {df.iloc[0]['单位净值']}")
                    print(f"     前一日: {df.iloc[1]['单位净值']}")
                    nav_a = float(df.iloc[0]['单位净值']) - float(df.iloc[1]['单位净值'])
                    print(f"     涨跌额: {nav_a:.4f}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")

# 2. 基金档案信息（可能包含基金经理）
print("\n" + "="*80)
print("2. fund_individual_basic_info_xq() - 基金基本信息（雪球）")
print("="*80)
try:
    info = ak.fund_individual_basic_info_xq(symbol=test_code)
    print(f"✓ 成功! 返回类型: {type(info)}")
    
    if isinstance(info, dict):
        print("\n字段:")
        for k, v in info.items():
            print(f"  {k}: {v}")
            if '经理' in str(k) or 'manager' in str(k).lower():
                print(f"  ✅ 找到基金经理字段!")
    elif isinstance(info, pd.DataFrame):
        print(f"字段: {list(info.columns)}")
        print(info)
except Exception as e:
    print(f"✗ 失败: {e}")

# 3. 基金持仓信息
print("\n" + "="*80)
print("3. fund_portfolio_hold_em() - 基金持仓")
print("="*80)
try:
    df = ak.fund_portfolio_hold_em(symbol=test_code, date="2025")
    print(f"✓ 成功! 字段: {list(df.columns)}")
    print(df.head())
except Exception as e:
    print(f"✗ 失败: {e}")

# 4. 基金经理信息
print("\n" + "="*80)
print("4. fund_manager_em() - 基金经理")
print("="*80)
try:
    df = ak.fund_manager_em()
    print(f"✓ 成功! 共 {len(df)} 个基金经理")
    print(f"字段: {list(df.columns)}")
    print(df.head(3))
except Exception as e:
    print(f"✗ 失败: {e}")

# 5. 基金购买状态
print("\n" + "="*80)
print("5. fund_purchase_em() - 基金申购赎回信息")
print("="*80)
try:
    df = ak.fund_purchase_em(fund=test_code)
    print(f"✓ 成功! 字段: {list(df.columns)}")
    print(df)
    
    # 检查是否有申购状态
    if '申购状态' in df.columns or '购买状态' in df.columns:
        print("  ✅ 找到申购状态字段!")
except Exception as e:
    print(f"✗ 失败: {e}")

# 6. 基金规模
print("\n" + "="*80)
print("6. fund_open_fund_info_em(indicator='基金规模走势')")
print("="*80)
try:
    df = ak.fund_open_fund_info_em(fund=test_code, indicator="基金规模走势")
    print(f"✓ 成功! 字段: {list(df.columns)}")
    print(df.head())
    
    if '资产规模' in df.columns or '基金份额' in df.columns:
        print("  ✅ 找到基金规模/份额字段!")
except Exception as e:
    print(f"✗ 失败: {e}")

# 7. 查看所有fund相关函数
print("\n" + "="*80)
print("7. 所有可能相关的 akshare 函数")
print("="*80)

fund_funcs = [name for name in dir(ak) if 'fund' in name.lower() and not name.startswith('_')]
print(f"找到 {len(fund_funcs)} 个函数:\n")

# 分类显示
categories = {
    'info': [],
    'manager': [],
    'open': [],
    'purchase': [],
    'individual': [],
    'other': []
}

for func in fund_funcs:
    if 'manager' in func.lower():
        categories['manager'].append(func)
    elif 'individual' in func.lower():
        categories['individual'].append(func)
    elif 'purchase' in func.lower() or 'buy' in func.lower():
        categories['purchase'].append(func)
    elif 'open' in func.lower():
        categories['open'].append(func)
    elif 'info' in func.lower():
        categories['info'].append(func)
    else:
        categories['other'].append(func)

for cat, funcs in categories.items():
    if funcs:
        print(f"\n{cat.upper()}相关 ({len(funcs)}个):")
        for f in funcs:
            print(f"  - {f}")

print("\n" + "="*80)
print("总结")
print("="*80)
print("""
关键发现:

1. 前一日净值 + 涨跌额:
   ✅ fund_open_fund_info_em(fund=code, indicator="单位净值走势")
   → 返回历史净值，取前2条即可计算

2. 基金经理:
   ❓ fund_individual_basic_info_xq() 或 fund_manager_em()
   → 需要进一步测试

3. 申购状态:
   ❓ fund_purchase_em() 
   → 可能包含申购赎回状态

4. 基金总份额:
   ❓ fund_open_fund_info_em(fund=code, indicator="基金规模走势")
   → 可能包含份额信息

建议测试这些接口的组合使用！
""")
