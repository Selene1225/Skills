"""
直接对比修复 data_from_sina.json
使用akshare作为标准数据源
"""

import json
import akshare as ak
import time

print("="*100)
print("验证并修复 data_from_sina.json")
print("="*100)
print()

# 1. 加载新浪数据
print("1. 加载 data_from_sina.json...")
with open('../data_from_sina.json', 'r', encoding='utf-8') as f:
    sina_data = json.load(f)

sina_funds = sina_data['data']
print(f"   ✅ 共 {len(sina_funds)} 只基金")
print()

# 2. 获取akshare最新数据
print("2. 从akshare获取最新数据...")
try:
    df_rank = ak.fund_open_fund_rank_em(symbol="全部")
    print(f"   ✅ akshare共 {len(df_rank)} 只基金")
except Exception as e:
    print(f"   ❌ 获取失败: {e}")
    exit(1)

print()

# 3. 对比验证
print("3. 对比验证数据...")
print()

issues = []
matched = 0
not_in_ak = 0
value_diff = 0

for i, sina_fund in enumerate(sina_funds):
    code = sina_fund['symbol']
    
    # 在akshare中查找
    fund_row = df_rank[df_rank['基金代码'] == code]
    
    if fund_row.empty:
        not_in_ak += 1
        issues.append({
            'code': code,
            'name': sina_fund['sname'],
            'issue': 'akshare中不存在',
            'action': '保留原数据'
        })
        continue
    
    # 对比数据
    row = fund_row.iloc[0]
    ak_nav = float(row['单位净值'])
    sina_nav = float(sina_fund['per_nav'])
    
    if abs(ak_nav - sina_nav) < 0.01:
        matched += 1
    else:
        value_diff += 1
        issues.append({
            'code': code,
            'name': sina_fund['sname'],
            'issue': f'单位净值不一致',
            'sina_value': sina_nav,
            'ak_value': ak_nav,
            'diff': abs(ak_nav - sina_nav),
            'action': '可更新为akshare值'
        })
        
        if i < 10:  # 只打印前10个差异
            print(f"   {code} {sina_fund['sname'][:20]:20s}: 新浪={sina_nav}, akshare={ak_nav}, 差异={abs(ak_nav - sina_nav):.4f}")

print()
print("验证统计:")
print(f"   ✅ 数据一致: {matched} 只 ({matched/len(sina_funds)*100:.1f}%)")
print(f"   ❌ 数值差异: {value_diff} 只 ({value_diff/len(sina_funds)*100:.1f}%)")
print(f"   ⚠️ akshare中不存在: {not_in_ak} 只 ({not_in_ak/len(sina_funds)*100:.1f}%)")
print()

# 4. 询问是否修复
if value_diff > 0:
    print(f"发现 {value_diff} 只基金数据不一致")
    print()
    print("数据差异可能原因：")
    print("  1. 数据更新时间不同（新浪数据较旧）")
    print("  2. 数据源统计口径不同")
    print()
    
    # 显示前5个差异示例
    print("差异示例（前5个）:")
    diff_examples = [iss for iss in issues if 'diff' in iss][:5]
    for ex in diff_examples:
        print(f"  {ex['code']} {ex['name'][:25]:25s}: 新浪={ex['sina_value']:.4f}, akshare={ex['ak_value']:.4f}, 差={ex['diff']:.4f}")
    print()
    
    choice = input("是否用akshare数据更新这些基金? (y/n): ").strip().lower()
    
    if choice == 'y':
        print()
        print("4. 更新数据...")
        updated = 0
        
        for sina_fund in sina_funds:
            code = sina_fund['symbol']
            fund_row = df_rank[df_rank['基金代码'] == code]
            
            if not fund_row.empty:
                row = fund_row.iloc[0]
                
                # 更新基础字段
                sina_fund['per_nav'] = str(row['单位净值'])
                sina_fund['total_nav'] = str(row['累计净值'])
                sina_fund['nav_rate'] = float(row['日增长率'])
                sina_fund['nav_date'] = row['日期']
                sina_fund['sname'] = row['基金简称']
                
                # 计算yesterday_nav和nav_a
                try:
                    nav_rate_decimal = sina_fund['nav_rate'] / 100
                    per_nav = float(sina_fund['per_nav'])
                    yesterday_nav = per_nav / (1 + nav_rate_decimal)
                    nav_a = per_nav - yesterday_nav
                    
                    sina_fund['yesterday_nav'] = round(yesterday_nav, 4)
                    sina_fund['nav_a'] = round(nav_a, 4)
                except:
                    pass
                
                updated += 1
        
        # 保存更新后的数据
        sina_data['data'] = sina_funds
        
        backup_file = '../data_from_sina_backup.json'
        output_file = '../data_from_sina_fixed.json'
        
        # 备份原文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(sina_data, f, ensure_ascii=False, indent=4)
        print(f"   ✅ 原数据已备份到: {backup_file}")
        
        # 保存修复后的数据
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sina_data, f, ensure_ascii=False, indent=4)
        print(f"   ✅ 修复后数据已保存到: {output_file}")
        print(f"   ✅ 共更新 {updated} 只基金数据")
        print()
        print("修复完成！")
    else:
        print("取消更新")
else:
    print("✅ 所有数据一致，无需修复")
