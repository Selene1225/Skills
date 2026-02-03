"""
使用正确的akshare接口获取所有缺失字段
"""

import akshare as ak
import pandas as pd

test_code = "000001"

print("="*80)
print("akshare完整方案测试")
print("="*80)

# 1. 基金基本信息（包含基金经理和规模）
print("\n✅ 1. fund_individual_basic_info_xq() - 基金经理、规模")
print("-"*80)
try:
    df = ak.fund_individual_basic_info_xq(symbol=test_code)
    
    # 提取基金经理
    manager_row = df[df['item'] == '基金经理']
    manager = manager_row.iloc[0]['value'] if not manager_row.empty else ''
    
    # 提取规模
    scale_row = df[df['item'] == '最新规模']
    scale = scale_row.iloc[0]['value'] if not scale_row.empty else ''
    
    print(f"✅ 基金经理: {manager}")
    print(f"✅ 最新规模: {scale}")
    
except Exception as e:
    print(f"❌ 失败: {e}")

# 2. 历史净值（前一日净值、涨跌额）
print("\n✅ 2. fund_open_fund_info_em() - 历史净值")
print("-"*80)
try:
    df = ak.fund_open_fund_info_em(symbol=test_code, indicator="单位净值走势", period="1月")
    print(f"✅ 成功! 共 {len(df)} 条记录")
    print(f"字段: {list(df.columns)}")
    print("\n最近3条:")
    print(df.head(3))
    
    if len(df) >= 2:
        today_nav = df.iloc[0]['单位净值']
        yesterday_nav = df.iloc[1]['单位净值']
        nav_a = today_nav - yesterday_nav
        print(f"\n✅ 可计算:")
        print(f"   当日净值: {today_nav}")
        print(f"   前一日净值: {yesterday_nav}")
        print(f"   涨跌额: {nav_a:.4f}")
        
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 尝试获取申购状态
print("\n❓ 3. 尝试获取申购状态")
print("-"*80)

# 方法1: 从基本信息中找
try:
    df = ak.fund_individual_basic_info_xq(symbol=test_code)
    print("基本信息中的所有字段:")
    for _, row in df.iterrows():
        print(f"  {row['item']}: {row['value']}")
        if '申购' in str(row['item']) or '赎回' in str(row['item']):
            print(f"  ✅ 找到申购相关信息!")
except Exception as e:
    print(f"失败: {e}")

# 4. 尝试获取基金份额
print("\n❓ 4. 尝试获取基金份额")
print("-"*80)
try:
    df = ak.fund_open_fund_info_em(symbol=test_code, indicator="基金规模走势", period="1年")
    print(f"✅ 成功! 共 {len(df)} 条记录")
    print(f"字段: {list(df.columns)}")
    if len(df) > 0:
        print("\n最新记录:")
        print(df.head(1))
        if '基金份额' in df.columns or '份额' in str(df.columns):
            print("✅ 找到基金份额字段!")
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("最终结论")
print("="*80)

result = {
    '基金代码': '✅ fund_open_fund_rank_em',
    '基金名称': '✅ fund_open_fund_rank_em',
    '单位净值': '✅ fund_open_fund_rank_em',
    '累计净值': '✅ fund_open_fund_rank_em',
    '前一日净值': '✅ fund_open_fund_info_em(indicator="单位净值走势")',
    '增长率': '✅ fund_open_fund_rank_em',
    '涨跌额': '✅ 可计算（当日-前一日）',
    '申购状态': '❓ 需进一步确认',
    '净值日期': '✅ fund_open_fund_rank_em',
    '基金经理': '✅ fund_individual_basic_info_xq',
    '基金类型': '✅ fund_name_em',
    '基金总份额': '❓ fund_open_fund_info_em(indicator="基金规模走势")'
}

print("\nakshare 字段覆盖情况:")
confirmed = 0
for field, api in result.items():
    print(f"  {api[0]} {field:12s} : {api}")
    if '✅' in api:
        confirmed += 1

print(f"\n确认可获取: {confirmed}/12 = {confirmed/12*100:.0f}%")
print("\n需要组合的接口:")
print("  1. fund_open_fund_rank_em() - 主数据")
print("  2. fund_name_em() - 基金类型")
print("  3. fund_individual_basic_info_xq() - 基金经理、规模")
print("  4. fund_open_fund_info_em(indicator='单位净值走势') - 前一日净值")
