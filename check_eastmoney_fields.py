"""
检查天天基金网数据的字段完整性
"""

import requests
import json

print("="*80)
print("天天基金网数据字段检查")
print("="*80)

url = "http://fund.eastmoney.com/data/rankhandler.aspx"
params = {
    'op': 'ph',
    'dt': 'kf',
    'ft': 'all',
    'rs': '',
    'gs': '0',
    'sc': 'qjzf',
    'st': 'desc',
    'sd': '2024-01-01',
    'ed': '2026-01-31',
    'qdii': '',
    'tabSubtype': ',,,,,',
    'pi': '1',
    'pn': '5',  # 只取5条测试
    'dx': '1'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'http://fund.eastmoney.com/'
}

r = requests.get(url, params=params, headers=headers, timeout=10)

if r.status_code == 200 and 'var rankData' in r.text:
    start = r.text.find('[')
    end = r.text.rfind(']') + 1
    data_str = r.text[start:end]
    data_list = json.loads(data_str)
    
    print(f"\n获取到 {len(data_list)} 条数据")
    print(f"\n第一条原始数据:")
    first = data_list[0]
    print(first)
    
    print(f"\n数据共有 {len(first.split(','))} 个字段")
    print("\n字段索引对照:")
    
    parts = first.split(',')
    field_map = {
        0: '基金代码',
        1: '基金名称',
        2: '拼音缩写',
        3: '净值日期',
        4: '单位净值',
        5: '累计净值',
        6: '日增长率',
        7: '近1周',
        8: '近1月',
        9: '近3月',
        10: '近6月',
        11: '近1年',
        12: '近2年',
        13: '近3年',
        14: '今年来',
        15: '成立来',
        16: '成立日期',
        17: '暂停标识',
        18: '涨跌额估算',
        19: '申购费率',
        20: '赎回费率',
        21: '暂停标识2',
        22: '赎回费率2',
        23: '申购状态',
        24: '赎回状态',
        25: '未知字段1',
        26: '资产规模',
        27: '基金经理',
        28: '基金类型',
    }
    
    for i, value in enumerate(parts[:30]):
        field_name = field_map.get(i, f'未知字段{i}')
        has_value = '✅' if value else '❌'
        print(f"{i:2d}. {has_value} {field_name:15s}: {value[:30] if value else '(空)'}")
    
    print("\n" + "="*80)
    print("字段映射到old_code格式:")
    print("="*80)
    
    mapping = {
        'symbol': (0, '基金代码', parts[0]),
        'sname': (1, '基金名称', parts[1]),
        'per_nav': (4, '单位净值', parts[4]),
        'total_nav': (5, '累计净值', parts[5]),
        'yesterday_nav': (-1, '前一日净值', '❌ 接口无此字段'),
        'nav_rate': (6, '增长率', parts[6]),
        'nav_a': (-1, '涨跌额', '❌ 接口无此字段'),
        'sg_states': (23, '申购状态', parts[23] if len(parts) > 23 else ''),
        'nav_date': (3, '净值日期', parts[3]),
        'fund_manager': (27, '基金经理', parts[27] if len(parts) > 27 else ''),
        'jjlx': (28, '基金类型', parts[28] if len(parts) > 28 else ''),
        'jjzfe': (26, '基金总份额/规模', parts[26] if len(parts) > 26 else ''),
    }
    
    print("\nold_code需要的12个字段:")
    for i, (key, (idx, name, value)) in enumerate(mapping.items(), 1):
        status = '✅' if idx >= 0 and value else '❌'
        print(f"{i:2d}. {status} {name:15s} (索引{idx:2d}): {str(value)[:40]}")
    
    print("\n" + "="*80)
    print("缺失字段汇总")
    print("="*80)
    
    missing = []
    empty = []
    
    for key, (idx, name, value) in mapping.items():
        if idx < 0:
            missing.append(name)
        elif not value:
            empty.append(name)
    
    if missing:
        print("\n❌ 接口完全没有的字段:")
        for field in missing:
            print(f"  - {field}")
    
    if empty:
        print("\n⚠️ 接口有但当前数据为空的字段:")
        for field in empty:
            print(f"  - {field}")
    
    print("\n✅ 接口有且有数据的字段:")
    for key, (idx, name, value) in mapping.items():
        if idx >= 0 and value:
            print(f"  - {name}")
