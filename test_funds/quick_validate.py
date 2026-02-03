"""
快速验证 data_from_sina.json 数据
"""

import json
import requests
import akshare as ak

# 加载新浪数据
with open('../data_from_sina.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    sina_funds = data['data']

print(f"data_from_sina.json 共有 {len(sina_funds)} 只基金")
print()

# 只验证前10个
sample_codes = [f['symbol'] for f in sina_funds[:10]]

print("验证前10只基金:")
for fund in sina_funds[:10]:
    print(f"  {fund['symbol']} {fund['sname']} 净值={fund['per_nav']} 增长率={fund['nav_rate']}%")

print()
print("正在从akshare获取数据对比...")

try:
    df = ak.fund_open_fund_rank_em(symbol="全部")
    
    match_count = 0
    diff_count = 0
    
    for sina_fund in sina_funds[:10]:
        code = sina_fund['symbol']
        fund_row = df[df['基金代码'] == code]
        
        if not fund_row.empty:
            row = fund_row.iloc[0]
            ak_nav = float(row['单位净值'])
            sina_nav = float(sina_fund['per_nav'])
            
            if abs(ak_nav - sina_nav) < 0.01:
                match_count += 1
                print(f"✅ {code} 数据一致 (净值={sina_nav})")
            else:
                diff_count += 1
                print(f"❌ {code} 数据不一致: 新浪={sina_nav}, akshare={ak_nav}, 差异={abs(ak_nav-sina_nav):.4f}")
        else:
            print(f"⚠️ {code} akshare中未找到")
    
    print()
    print(f"验证结果: ✅一致 {match_count}/10, ❌差异 {diff_count}/10")
    
except Exception as e:
    print(f"验证失败: {e}")
