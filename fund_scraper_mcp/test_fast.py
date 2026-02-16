import requests
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'http://fund.eastmoney.com/data/rankhandler.aspx'
params = {
    'op': 'ph', 'dt': 'kf', 'ft': 'all', 'rs': '', 'gs': '0',
    'sc': 'zzf', 'st': 'desc', 'sd': '2020-01-01', 'ed': '2099-12-31',
    'qdii': '', 'tabSubtype': ',,,,,', 'pi': '1', 'pn': '500', 'dx': '1'
}
headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'http://fund.eastmoney.com/data/fundranking.html'}

print("正在请求...")
r = requests.get(url, params=params, headers=headers, timeout=30)
print(f"状态: {r.status_code}, 长度: {len(r.text)}")

m = re.search(r'allRecords:(\d+)', r.text)
if m:
    print(f"总数: {m.group(1)}")

m2 = re.search(r'datas:\[(.*?)\]', r.text, re.DOTALL)
if m2:
    datas_str = m2.group(1)
    funds = [s.strip().strip('"') for s in datas_str.split('","')]
    print(f"本页基金数: {len(funds)}")
    if len(funds) > 0:
        print(f"第一个: {funds[0][:100]}")
