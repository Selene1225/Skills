import requests
import re
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'http://fund.eastmoney.com/data/rankhandler.aspx'
params = {
    'op': 'ph',
    'dt': 'kf',
    'ft': 'all',
    'rs': '',
    'gs': '0',
    'sc': 'zzf',
    'st': 'desc',
    'sd': '2020-01-01',
    'ed': '2099-12-31',
    'qdii': '',
    'tabSubtype': ',,,,,',
    'pi': '1',
    'pn': '10',
    'dx': '1'
}

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://fund.eastmoney.com/data/fundranking.html'
}

r = requests.get(url, params=params, headers=headers)
print(f"状态码: {r.status_code}")
print(f"响应长度: {len(r.text)}")
print(f"\n前500字符:")
print(r.text[:500])

# 提取datas
m = re.search(r'datas:\[(.*?)\]', r.text, re.DOTALL)
if m:
    datas_str = m.group(1)
    # datas可能是字符串列表形式: ["fund1","fund2",...]
    funds = [s.strip().strip('"') for s in datas_str.split('","')]
    print(f"\n基金数量: {len(funds)}")
    print(f"第一个基金数据:")
    print(funds[0])

    # 解析第一个基金的字段
    fields = funds[0].split(',')
    print(f"\n字段数量: {len(fields)}")
    print("\n字段内容:")
    for i, field in enumerate(fields[:20]):
        print(f"  [{i}]: {field}")

# 提取TotalCount
m2 = re.search(r'TotalCount:(\d+)', r.text)
if m2:
    print(f"\n总基金数: {m2.group(1)}")
