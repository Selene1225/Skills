"""
快速测试 akshare 基金接口组合方案
"""

import akshare as ak
import pandas as pd

print("测试 akshare 组合接口获取完整字段\n")

# 目标字段
target_fields = {
    'symbol': '基金代码',
    'sname': '基金名称', 
    'per_nav': '单位净值',
    'total_nav': '累计净值',
    'yesterday_nav': '前一日净值',  # 缺失
    'nav_rate': '增长率',
    'nav_a': '涨跌额',  # 缺失
    'sg_states': '申购状态',  # 缺失
    'nav_date': '净值日期',
    'fund_manager': '基金经理',  # 缺失
    'jjlx': '基金类型',  # 缺失
    'jjzfe': '基金总份额'  # 缺失
}

print("需要的字段:")
for i, (k, v) in enumerate(target_fields.items(), 1):
    print(f"{i:2d}. {k:15s} - {v}")

print("\n" + "="*80)
print("方案1: fund_open_fund_rank_em() - 基金排行")
print("="*80)

df1 = ak.fund_open_fund_rank_em(symbol="全部")
print(f"获取 {len(df1)} 条数据")
print(f"字段: {list(df1.columns)[:10]}...")

# 字段映射
mapping1 = {
    '基金代码': 'symbol',
    '基金简称': 'sname',
    '单位净值': 'per_nav',
    '累计净值': 'total_nav',
    '日增长率': 'nav_rate',
    '日期': 'nav_date',
}

print("\n包含的字段:")
for cn, en in mapping1.items():
    print(f"  ✓ {cn} → {en}")

print("\n缺失的字段:")
missing = ['前一日净值', '涨跌额', '申购状态', '基金经理', '基金类型', '基金总份额']
for f in missing:
    print(f"  ✗ {f}")

print("\n" + "="*80)
print("方案2: 测试单个基金详情接口")
print("="*80)

test_code = "000001"
print(f"测试基金: {test_code}")

# 尝试获取基金名称列表
print("\n2.1 fund_name_em() - 所有基金列表")
try:
    fund_list = ak.fund_name_em()
    print(f"  ✓ 成功! 共 {len(fund_list)} 个基金")
    print(f"  字段: {list(fund_list.columns)}")
    
    # 查看是否包含基金类型
    if '基金类型' in fund_list.columns or 'type' in fund_list.columns:
        print("  ✓ 包含基金类型!")
    
    test_row = fund_list[fund_list['基金代码'] == test_code]
    if not test_row.empty:
        print(f"\n  基金 {test_code} 信息:")
        for col in fund_list.columns[:8]:
            print(f"    {col}: {test_row.iloc[0][col]}")
except Exception as e:
    print(f"  ✗ 失败: {e}")

# 测试历史净值
print("\n2.2 fund_em_open_fund_daily() - 历史净值")
try:
    # 使用正确的函数名
    history = ak.fund_em_open_fund_daily(symbol=test_code)
    print(f"  ✓ 成功! 共 {len(history)} 条历史记录")
    print(f"  字段: {list(history.columns)}")
    print(f"\n  最近2条记录:")
    print(history.head(2))
    
    # 计算前一日净值
    if len(history) >= 2:
        yesterday_nav = history.iloc[1]['单位净值']
        today_nav = history.iloc[0]['单位净值']
        nav_a = today_nav - yesterday_nav
        print(f"\n  ✓ 可计算: 前一日净值 = {yesterday_nav}, 涨跌额 = {nav_a:.4f}")
except Exception as e:
    print(f"  ✗ 失败: {e}")

print("\n" + "="*80)
print("组合方案总结")
print("="*80)

print("""
✅ 可行的组合方案:

接口1: fund_open_fund_rank_em()
  - 基金代码 ✓
  - 基金名称 ✓
  - 单位净值 ✓
  - 累计净值 ✓
  - 增长率 ✓
  - 净值日期 ✓

接口2: fund_name_em()
  - 基金类型 (可能有)
  - 基金经理 (可能有)

接口3: fund_em_open_fund_daily()
  - 前一日净值 ✓ (取历史第2条)
  - 涨跌额 ✓ (计算得出)

字段覆盖率估计: 9/12 = 75%

仍然缺失:
  - 申购状态
  - 基金总份额

这两个字段需要从基金详情页抓取或使用其他数据源。
""")
