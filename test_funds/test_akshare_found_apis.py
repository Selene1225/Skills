"""
测试akshare发现的关键接口
"""

import akshare as ak
import pandas as pd

test_code = "000001"

print("="*80)
print("测试akshare关键接口")
print("="*80)

# 1. 基金经理 - fund_individual_basic_info_xq
print("\n1. 测试 fund_individual_basic_info_xq() - 基金基本信息")
print("-"*80)
try:
    df = ak.fund_individual_basic_info_xq(symbol=test_code)
    print(f"✅ 成功!")
    
    # 提取基金经理
    manager_row = df[df['item'] == '基金经理']
    if not manager_row.empty:
        manager = manager_row.iloc[0]['value']
        print(f"基金经理: {manager}")
        print("✅ 可以获取基金经理!")
    
    # 提取规模
    scale_row = df[df['item'] == '最新规模']
    if not scale_row.empty:
        scale = scale_row.iloc[0]['value']
        print(f"最新规模: {scale}")
        print("✅ 可以获取基金规模!")
        
except Exception as e:
    print(f"❌ 失败: {e}")

# 2. 历史净值 - fund_open_fund_daily_em
print("\n2. 测试 fund_open_fund_daily_em() - 历史净值")
print("-"*80)
try:
    df = ak.fund_open_fund_daily_em(symbol=test_code)
    print(f"✅ 成功! 共 {len(df)} 条历史记录")
    print(f"字段: {list(df.columns)}")
    print("\n最近3条:")
    print(df.head(3))
    
    if len(df) >= 2:
        today_nav = df.iloc[0]['单位净值']
        yesterday_nav = df.iloc[1]['单位净值']
        nav_a = today_nav - yesterday_nav
        print(f"\n✅ 可以计算:")
        print(f"   当日净值: {today_nav}")
        print(f"   前一日净值: {yesterday_nav}")
        print(f"   涨跌额: {nav_a:.4f}")
        
except Exception as e:
    print(f"❌ 失败: {e}")

# 3. 申购赎回信息 - fund_purchase_em
print("\n3. 测试 fund_purchase_em() - 申购赎回信息")
print("-"*80)
try:
    # 尝试不同的参数名
    df = ak.fund_purchase_em(symbol=test_code)
    print(f"✅ 成功!")
    print(f"字段: {list(df.columns)}")
    print(df)
    
    if '申购状态' in df.columns:
        print("✅ 找到申购状态字段!")
except:
    try:
        df = ak.fund_purchase_em(code=test_code)
        print(f"✅ 成功!")
        print(f"字段: {list(df.columns)}")
        print(df)
    except Exception as e:
        print(f"❌ 失败: {e}")

# 4. 基金费用信息 - fund_fee_em
print("\n4. 测试 fund_fee_em() - 基金费用信息")
print("-"*80)
try:
    df = ak.fund_fee_em(symbol=test_code)
    print(f"✅ 成功!")
    print(f"字段: {list(df.columns)}")
    print(df)
except Exception as e:
    print(f"❌ 失败: {e}")

# 5. 基金详情 - fund_individual_detail_info_xq
print("\n5. 测试 fund_individual_detail_info_xq() - 基金详情")
print("-"*80)
try:
    df = ak.fund_individual_detail_info_xq(symbol=test_code, indicator="基金信息")
    print(f"✅ 成功!")
    print(df)
except Exception as e:
    print(f"❌ 失败: {e}")

# 6. 查找基金经理详情
print("\n6. 测试 fund_manager_em() - 查找基金经理")
print("-"*80)
try:
    df = ak.fund_manager_em()
    # 查找管理000001的经理
    fund_managers = df[df['现任基金代码'] == test_code]
    if not fund_managers.empty:
        print(f"✅ 找到基金经理:")
        print(fund_managers[['姓名', '所属公司', '累计从业时间']])
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("总结")
print("="*80)
print("""
可用接口汇总:

✅ 基金经理:
   fund_individual_basic_info_xq(symbol=code)
   → 返回 DataFrame，在 item='基金经理' 的行中

✅ 前一日净值 + 涨跌额:
   fund_open_fund_daily_em(symbol=code)
   → 返回历史净值，取前2条计算

✅ 基金规模:
   fund_individual_basic_info_xq(symbol=code)
   → item='最新规模' 的行

❓ 申购状态:
   需要继续测试 fund_purchase_em() 或其他接口

❓ 基金总份额:
   规模数据有，但具体份额可能需要其他接口
""")
