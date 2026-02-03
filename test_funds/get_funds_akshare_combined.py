"""
使用 akshare 组合接口获取完整基金数据

方案: 组合2个接口
1. fund_open_fund_rank_em() - 获取基金排行数据（主要数据）
2. fund_name_em() - 获取基金类型

覆盖字段: 7/12 = 58%
可计算字段: 2个（前一日净值、涨跌额需要历史数据）
仍缺失: 申购状态、基金经理、基金总份额
"""

import akshare as ak
import pandas as pd
from datetime import date
import time

def get_all_funds_with_akshare():
    """
    使用akshare组合接口获取基金数据
    """
    print("="*80)
    print("使用 akshare 组合接口获取基金数据")
    print("="*80)
    
    # 1. 获取基金排行数据（主数据）
    print("\n步骤1: 获取基金排行数据...")
    df_rank = ak.fund_open_fund_rank_em(symbol="全部")
    print(f"✓ 获取 {len(df_rank)} 个基金的排行数据")
    
    # 2. 获取基金类型数据
    print("\n步骤2: 获取基金类型数据...")
    df_type = ak.fund_name_em()
    print(f"✓ 获取 {len(df_type)} 个基金的类型数据")
    
    # 3. 合并数据
    print("\n步骤3: 合并数据...")
    # 将基金类型数据转换为字典，便于快速查询
    type_dict = dict(zip(df_type['基金代码'], df_type['基金类型']))
    
    # 构建完整数据
    result = []
    for idx, row in df_rank.iterrows():
        fund_code = row['基金代码']
        fund_type = type_dict.get(fund_code, '')
        
        fund_info = {
            'symbol': fund_code,
            'sname': row['基金简称'],
            'per_nav': row['单位净值'],
            'total_nav': row['累计净值'],
            'yesterday_nav': '',  # akshare排行接口不提供
            'nav_rate': row['日增长率'],
            'nav_a': '',  # 需要计算，但缺少前一日净值
            'sg_states': '',  # akshare不提供
            'nav_date': row['日期'],
            'fund_manager': '',  # akshare排行接口不提供
            'jjlx': fund_type,
            'jjzfe': ''  # akshare不提供
        }
        result.append(fund_info)
    
    print(f"✓ 合并完成，共 {len(result)} 条数据")
    
    return result

def save_to_csv(data, filename):
    """保存为CSV文件，格式与旧代码一致"""
    print(f"\n保存数据到: {filename}")
    
    # 字段顺序（与旧代码一致）
    fieldnames = ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav', 
                  'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager', 'jjlx', 'jjzfe']
    
    # 中文标题
    title = '基金代码,基金名称,单位净值,累计净值,前一日净值,增长率,涨跌额,申购状态,净值日期,基金经理,基金类型,基金zfe'
    
    with open(filename, 'w', encoding='utf-8-sig') as f:
        # 写入标题
        f.write(title + '\n')
        
        # 写入数据
        for item in data:
            row = []
            for field in fieldnames:
                value = item.get(field, '')
                row.append(str(value))
            f.write(','.join(row) + '\n')
    
    print(f"✓ 保存完成")

if __name__ == "__main__":
    try:
        # 获取数据
        funds_data = get_all_funds_with_akshare()
        
        # 保存文件
        time_str = date.today()
        filename = f'基金-akshare-{time_str}.csv'
        save_to_csv(funds_data, filename)
        
        # 统计信息
        print("\n" + "="*80)
        print("数据统计")
        print("="*80)
        print(f"总基金数: {len(funds_data)}")
        
        # 字段覆盖情况
        print("\n字段覆盖情况:")
        field_coverage = {
            'symbol': '基金代码',
            'sname': '基金名称',
            'per_nav': '单位净值',
            'total_nav': '累计净值',
            'nav_rate': '增长率',
            'nav_date': '净值日期',
            'jjlx': '基金类型'
        }
        
        for field, name in field_coverage.items():
            count = sum(1 for item in funds_data if item.get(field))
            coverage = count / len(funds_data) * 100
            print(f"  ✓ {name:12s}: {count:5d} / {len(funds_data)} ({coverage:.1f}%)")
        
        print("\n缺失字段:")
        missing = ['前一日净值', '涨跌额', '申购状态', '基金经理', '基金总份额']
        for field in missing:
            print(f"  ✗ {field}")
        
        print("\n" + "="*80)
        print("总结")
        print("="*80)
        print("""
akshare 组合方案:
  ✓ 接口1: fund_open_fund_rank_em() - 主数据
  ✓ 接口2: fund_name_em() - 基金类型
  
  覆盖率: 7/12 = 58%
  
  优点:
    - 简单易用，2个接口即可
    - 数据稳定可靠
    - 完全免费
    - 覆盖19,000+基金
  
  缺点:
    - 缺少部分字段（前一日净值、申购状态等）
  
  建议:
    - 如需完整字段，使用天天基金网组合接口
    - 如只需基本分析，akshare足够
""")
        
        # 显示前5条数据
        print("\n前5条数据示例:")
        for i, fund in enumerate(funds_data[:5], 1):
            symbol = str(fund['symbol'])
            sname = str(fund['sname'])
            per_nav = str(fund['per_nav'])
            jjlx = str(fund['jjlx'])
            nav_rate = str(fund['nav_rate'])
            print(f"{i}. {symbol:8s} {sname:30s} "
                  f"净值:{per_nav:>8s} 类型:{jjlx:15s} "
                  f"增长率:{nav_rate:>6s}%")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按 回车 结束")
