import json

# 快速统计
with open('../data_from_sina.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"data_from_sina.json 统计:")
print(f"  总数: {len(data['data'])} 只基金")
print(f"  数据日期: {data['data'][0]['nav_date']}")
print(f"  示例基金: {data['data'][0]['symbol']} {data['data'][0]['sname']} 净值={data['data'][0]['per_nav']}")
