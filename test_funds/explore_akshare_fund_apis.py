"""
探索 akshare 的基金相关接口
查找能补充缺失字段的接口
"""

import akshare as ak
import pandas as pd

print("="*80)
print("探索 akshare 基金相关接口")
print("="*80)

# 测试基金代码
test_fund_code = "000001"  # 华夏成长

print(f"\n使用测试基金: {test_fund_code} (华夏成长)\n")

# 1. 基金排行接口（已知）
print("="*80)
print("1. 基金排行接口 - fund_open_fund_rank_em()")
print("="*80)
try:
    df = ak.fund_open_fund_rank_em(symbol="全部")
    print(f"字段: {list(df.columns)}")
    
    # 找到测试基金
    test_row = df[df['基金代码'] == test_fund_code]
    if not test_row.empty:
        print(f"\n基金 {test_fund_code} 的数据:")
        for col in df.columns:
            print(f"  {col}: {test_row.iloc[0][col]}")
except Exception as e:
    print(f"失败: {e}")

# 2. 基金基本信息
print("\n" + "="*80)
print("2. 基金基本信息 - fund_individual_basic_info_xq()")
print("="*80)
try:
    info = ak.fund_individual_basic_info_xq(symbol=test_fund_code)
    print(f"返回类型: {type(info)}")
    if isinstance(info, pd.DataFrame):
        print(f"字段: {list(info.columns)}")
        print(info)
    elif isinstance(info, dict):
        print("字段:")
        for k, v in info.items():
            print(f"  {k}: {v}")
except Exception as e:
    print(f"失败: {e}")

# 3. 基金档案信息
print("\n" + "="*80)
print("3. 基金档案 - fund_individual_detail_info_xq()")
print("="*80)
try:
    detail = ak.fund_individual_detail_info_xq(symbol=test_fund_code, indicator="基金信息")
    print(f"返回类型: {type(detail)}")
    if isinstance(detail, pd.DataFrame):
        print(f"字段: {list(detail.columns)}")
        print(detail)
    elif isinstance(detail, dict):
        print("字段:")
        for k, v in detail.items():
            print(f"  {k}: {v}")
except Exception as e:
    print(f"失败: {e}")

# 4. 基金经理信息
print("\n" + "="*80)
print("4. 基金经理信息 - fund_individual_detail_info_xq(indicator='基金经理')")
print("="*80)
try:
    manager = ak.fund_individual_detail_info_xq(symbol=test_fund_code, indicator="基金经理")
    print(f"返回类型: {type(manager)}")
    print(manager)
except Exception as e:
    print(f"失败: {e}")

# 5. 基金净值历史
print("\n" + "="*80)
print("5. 历史净值 - fund_open_fund_info_em()")
print("="*80)
try:
    # 尝试不同的参数名
    try:
        history = ak.fund_open_fund_info_em(symbol=test_fund_code, indicator="单位净值走势")
        print(f"返回类型: {type(history)}")
        if isinstance(history, pd.DataFrame):
            print(f"字段: {list(history.columns)}")
            print(f"数据行数: {len(history)}")
            print("\n最近5条记录:")
            print(history.head())
    except:
        # 尝试其他参数
        history = ak.fund_em_open_fund_info(fund=test_fund_code, indicator="单位净值走势")
        print(f"返回类型: {type(history)}")
        if isinstance(history, pd.DataFrame):
            print(f"字段: {list(history.columns)}")
            print(history.head())
except Exception as e:
    print(f"失败: {e}")

# 6. 基金份额持有人结构
print("\n" + "="*80)
print("6. 基金份额 - fund_share_hold_structure_em()")
print("="*80)
try:
    share = ak.fund_share_hold_structure_em(symbol=test_fund_code)
    print(f"返回类型: {type(share)}")
    print(share)
except Exception as e:
    print(f"失败: {e}")

# 7. 查找所有基金相关函数
print("\n" + "="*80)
print("7. 查找 akshare 所有基金相关函数")
print("="*80)
try:
    import inspect
    fund_functions = [name for name in dir(ak) if 'fund' in name.lower() and callable(getattr(ak, name))]
    print(f"找到 {len(fund_functions)} 个基金相关函数:\n")
    for i, func in enumerate(fund_functions, 1):
        print(f"{i:2d}. {func}")
except Exception as e:
    print(f"失败: {e}")

print("\n" + "="*80)
print("总结")
print("="*80)
print("""
需要测试的关键函数：
1. fund_individual_basic_info_xq() - 基本信息（可能有基金类型、经理等）
2. fund_individual_detail_info_xq() - 详细信息
3. fund_open_fund_info_em() - 历史净值（可获取前一日净值）
4. fund_em_* 系列函数

通过组合这些接口，可能可以获取所有缺失字段。
""")
