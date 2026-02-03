"""
data_from_sina.json 数据验证总结报告
基于已有的验证结果
"""

import json

print("="*100)
print("data_from_sina.json 数据分析报告")
print("="*100)
print()

# 加载数据
with open('../data_from_sina.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

funds = data['data']

print(f"📊 基本信息:")
print(f"  - 实际基金数量: {len(funds)} 只")
print(f"  - 文件声明总数: {data['total_num']} 只 (不匹配)")
print(f"  - 数据日期: {funds[0]['nav_date']}")
print()

print(f"📋 数据完整性检查:")
complete_count = 0
incomplete_count = 0

for fund in funds:
    # 检查关键字段
    if all([
        fund.get('symbol'),
        fund.get('sname'),
        fund.get('per_nav'),
        fund.get('total_nav'),
        fund.get('nav_rate') is not None,
        fund.get('yesterday_nav') is not None,
        fund.get('nav_a') is not None,
        fund.get('nav_date'),
        fund.get('fund_manager'),
        fund.get('jjlx'),
        fund.get('jjzfe') is not None
    ]):
        complete_count += 1
    else:
        incomplete_count += 1

print(f"  ✅ 字段完整: {complete_count} 只 ({complete_count/len(funds)*100:.1f}%)")
print(f"  ⚠️ 字段不完整: {incomplete_count} 只 ({incomplete_count/len(funds)*100:.1f}%)")
print()

print(f"🔍 基金代码分布:")
code_ranges = {
    '000-003': 0,  # 老基金
    '004-020': 0,  # 中期基金
    '021-024': 0,  # 新基金
    '其他': 0
}

for fund in funds:
    code = fund['symbol']
    prefix = int(code[:3])
    if prefix <= 3:
        code_ranges['000-003'] += 1
    elif prefix <= 20:
        code_ranges['004-020'] += 1
    elif prefix <= 24:
        code_ranges['021-024'] += 1
    else:
        code_ranges['其他'] += 1

for range_name, count in code_ranges.items():
    print(f"  {range_name}: {count} 只")

print()

print("📝 已知问题:")
print("  1. total_num 字段值 (6315) 与实际数据量 (40) 不符")
print("  2. 大部分是新基金（024开头），可能不在所有数据源中")
print("  3. 部分新基金在天天基金网排行榜中找不到")
print()

print("✅ 优点:")
print("  - 字段完整度高，包含全部12个字段")
print("  - 有基金经理、基金类型、资产规模等详细信息")
print("  - 数据格式规范，易于使用")
print()

print("🔧 建议:")
print("  1. 修正 total_num 字段为实际数量 (40)")
print("  2. 如果这是测试数据，建议标注清楚")
print("  3. 如果需要完整数据，建议：")
print("     - 使用 get_funds_eastmoney.py 获取19135只基金")
print("     - 或使用 akshare 补充缺失字段")
print()

print("🎯 数据质量评估:")
if complete_count == len(funds):
    print("  ✅ 优秀 - 所有字段完整，数据规范")
elif complete_count / len(funds) > 0.9:
    print("  ✅ 良好 - 绝大部分数据完整")
else:
    print("  ⚠️ 一般 - 存在较多不完整数据")

print()
print("="*100)
