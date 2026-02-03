"""
使用 akshare 获取完整基金数据（10/12字段）

组合4个接口:
1. fund_open_fund_rank_em() - 主数据（基金代码、名称、净值、增长率等）
2. fund_name_em() - 基金类型
3. fund_individual_basic_info_xq() - 基金经理（单个查询）
4. fund_open_fund_info_em() - 前一日净值（单个查询）

覆盖率: 10/12 = 83%
缺失: 申购状态、基金总份额

注意: 此方案需要逐个查询基金详情，速度较慢
"""

import akshare as ak
import pandas as pd
from datetime import date
import time
import random

def get_fund_manager_and_yesterday_nav(code):
    """
    获取单个基金的经理和前一日净值
    """
    result = {
        'fund_manager': '',
        'yesterday_nav': '',
        'nav_a': ''
    }
    
    try:
        # 1. 获取基金经理
        df_info = ak.fund_individual_basic_info_xq(symbol=code)
        manager_row = df_info[df_info['item'] == '基金经理']
        if not manager_row.empty:
            result['fund_manager'] = manager_row.iloc[0]['value']
    except:
        pass
    
    try:
        # 2. 获取前一日净值
        df_nav = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势", period="1月")
        if len(df_nav) >= 2:
            # 最新的在最后
            today_nav = df_nav.iloc[-1]['单位净值']
            yesterday_nav = df_nav.iloc[-2]['单位净值']
            nav_a = today_nav - yesterday_nav
            
            result['yesterday_nav'] = str(yesterday_nav)
            result['nav_a'] = f"{nav_a:.4f}"
    except:
        pass
    
    return result

def get_all_funds_complete():
    """
    获取所有基金的完整数据
    """
    print("="*80)
    print("使用 akshare 组合接口获取完整基金数据")
    print("="*80)
    
    # 步骤1: 获取基金排行数据（主数据）
    print("\n步骤1: 获取基金排行数据...")
    df_rank = ak.fund_open_fund_rank_em(symbol="全部")
    print(f"✓ 获取 {len(df_rank)} 个基金的排行数据")
    
    # 步骤2: 获取基金类型数据
    print("\n步骤2: 获取基金类型数据...")
    df_type = ak.fund_name_em()
    print(f"✓ 获取 {len(df_type)} 个基金的类型数据")
    type_dict = dict(zip(df_type['基金代码'], df_type['基金类型']))
    
    # 步骤3: 构建基础数据
    print("\n步骤3: 合并基础数据...")
    result = []
    for idx, row in df_rank.iterrows():
        fund_code = row['基金代码']
        fund_type = type_dict.get(fund_code, '')
        
        fund_info = {
            'symbol': fund_code,
            'sname': row['基金简称'],
            'per_nav': row['单位净值'],
            'total_nav': row['累计净值'],
            'yesterday_nav': '',
            'nav_rate': row['日增长率'],
            'nav_a': '',
            'sg_states': '',  # akshare无此字段
            'nav_date': row['日期'],
            'fund_manager': '',
            'jjlx': fund_type,
            'jjzfe': ''  # akshare无此字段
        }
        result.append(fund_info)
    
    print(f"✓ 合并完成，共 {len(result)} 条数据")
    
    # 步骤4: 补充详细信息（可选，较慢）
    print("\n步骤4: 是否补充基金经理和前一日净值？")
    print("注意: 需要逐个查询，19000+基金大约需要几小时")
    choice = input("输入基金数量限制（如100），或按回车跳过: ").strip()
    
    if choice.isdigit():
        limit = int(choice)
        print(f"\n开始补充前 {limit} 个基金的详细信息...")
        
        for i in range(min(limit, len(result))):
            fund_code = result[i]['symbol']
            print(f"  {i+1}/{limit} 查询 {fund_code}...", end='')
            
            details = get_fund_manager_and_yesterday_nav(fund_code)
            result[i].update(details)
            
            print(f" 经理:{details['fund_manager'][:10] if details['fund_manager'] else '无'}")
            
            # 随机延迟避免请求过快
            if (i+1) % 10 == 0:
                time.sleep(random.uniform(0.5, 1.0))
            else:
                time.sleep(random.uniform(0.1, 0.3))
        
        print(f"✓ 补充完成")
    else:
        print("跳过补充步骤")
    
    return result

def save_to_csv(data, filename):
    """保存为CSV文件，格式与旧代码一致"""
    print(f"\n保存数据到: {filename}")
    
    # 字段顺序
    fieldnames = ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav', 
                  'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager', 'jjlx', 'jjzfe']
    
    # 中文标题
    title = '基金代码,基金名称,单位净值,累计净值,前一日净值,增长率,涨跌额,申购状态,净值日期,基金经理,基金类型,基金zfe'
    
    with open(filename, 'w', encoding='utf-8-sig') as f:
        f.write(title + '\n')
        
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
        funds_data = get_all_funds_complete()
        
        # 保存文件
        time_str = date.today()
        filename = f'基金-akshare-complete-{time_str}.csv'
        save_to_csv(funds_data, filename)
        
        # 统计
        print("\n" + "="*80)
        print("数据统计")
        print("="*80)
        print(f"总基金数: {len(funds_data)}")
        
        # 统计各字段覆盖率
        stats = {}
        for field in ['symbol', 'sname', 'per_nav', 'total_nav', 'nav_rate', 
                      'nav_date', 'jjlx', 'fund_manager', 'yesterday_nav']:
            count = sum(1 for item in funds_data if item.get(field))
            stats[field] = count
        
        print("\n字段覆盖情况:")
        field_names = {
            'symbol': '基金代码',
            'sname': '基金名称',
            'per_nav': '单位净值',
            'total_nav': '累计净值',
            'yesterday_nav': '前一日净值',
            'nav_rate': '增长率',
            'nav_date': '净值日期',
            'fund_manager': '基金经理',
            'jjlx': '基金类型'
        }
        
        for field, name in field_names.items():
            count = stats.get(field, 0)
            coverage = count / len(funds_data) * 100 if len(funds_data) > 0 else 0
            status = "✅" if coverage > 50 else "⚠️"
            print(f"  {status} {name:12s}: {count:5d} / {len(funds_data)} ({coverage:.1f}%)")
        
        print("\n" + "="*80)
        print("总结")
        print("="*80)
        print("""
akshare 组合方案（完整版）:
  
  基础字段 (一次性获取):
    ✅ 基金代码、名称、净值、增长率、日期
    ✅ 基金类型
    覆盖率: 7/12
  
  详细字段 (需逐个查询):
    ✅ 基金经理
    ✅ 前一日净值
    ✅ 涨跌额（计算得出）
    覆盖率: +3 = 10/12 = 83%
  
  缺失字段:
    ❌ 申购状态
    ❌ 基金总份额
  
  速度:
    - 基础数据: 很快（约10秒）
    - 完整数据: 较慢（19000基金约需数小时）
  
  建议:
    - 只需基础分析: 使用基础版本（7字段）
    - 需要完整数据: 分批查询或使用天天基金网
""")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按 回车 结束")
