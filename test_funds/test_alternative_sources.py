"""
测试其他基金数据源

除了新浪财经和天天基金网，还有以下可选方案：
1. akshare - Python金融数据接口库（推荐）
2. 蚂蚁基金/支付宝基金
3. 雪球基金数据
4. 集思录
"""

import requests
import json

print("="*80)
print("方案1: 测试天天基金网API（已验证可用，推荐）")
print("="*80)

# 天天基金网 - 基金排行榜
url1 = "http://fund.eastmoney.com/data/rankhandler.aspx"
params1 = {
    'op': 'ph',
    'dt': 'kf',
    'ft': 'all',  # all=全部类型
    'rs': '',
    'gs': '0',
    'sc': 'zzf',  # 近1周增长
    'st': 'desc',
    'sd': '2024-01-01',
    'ed': '2026-01-31',
    'qdii': '',
    'tabSubtype': ',,,,,',
    'pi': '1',
    'pn': '50',
    'dx': '1'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://fund.eastmoney.com/'
}

try:
    r = requests.get(url1, params=params1, headers=headers, timeout=10)
    if r.status_code == 200 and 'var rankData' in r.text:
        start = r.text.find('[')
        end = r.text.rfind(']') + 1
        if start != -1:
            data_str = r.text[start:end]
            data = json.loads(data_str)
            print(f"✅ 成功！获取到 {len(data)} 条基金数据")
            if data:
                first = data[0].split(',')
                print(f"示例: {first[0]} - {first[1]}")
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("方案2: 测试天天基金网 - 基金详情接口")
print("="*80)

# 天天基金网 - 基金净值接口
url2 = "http://api.fund.eastmoney.com/f10/lsjz"
params2 = {
    'fundCode': '000001',  # 华夏成长
    'pageIndex': 1,
    'pageSize': 20,
}

try:
    r = requests.get(url2, params=params2, headers=headers, timeout=10)
    if r.status_code == 200:
        result = r.json()
        if 'Data' in result and 'LSJZList' in result['Data']:
            print(f"✅ 成功！基金000001共有 {result['Data']['TotalCount']} 条净值记录")
            if result['Data']['LSJZList']:
                print(f"最新净值: {result['Data']['LSJZList'][0]}")
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("方案3: 测试天天基金网 - 基金列表接口")
print("="*80)

# 获取所有基金列表
url3 = "http://fund.eastmoney.com/js/fundcode_search.js"

try:
    r = requests.get(url3, headers=headers, timeout=10)
    if r.status_code == 200:
        # 提取JavaScript中的数组
        text = r.text.replace('var r = ', '').replace(';', '')
        funds = json.loads(text)
        print(f"✅ 成功！获取到 {len(funds)} 个基金代码")
        print(f"前5个基金: ")
        for fund in funds[:5]:
            print(f"  {fund[0]} - {fund[2]} ({fund[1]})")
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("方案4: 测试蚂蚁财富/支付宝基金接口")
print("="*80)

# 蚂蚁财富基金排行
url4 = "https://mfin.alipay.com/api/mgop.alipay.adx.mini.mfundfindmanage.queryfundlist"

try:
    r = requests.get(url4, headers=headers, timeout=10)
    print(f"状态码: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ 响应成功（需要进一步分析）")
        print(f"内容前300字符: {r.text[:300]}")
    else:
        print(f"❌ 状态码异常")
except Exception as e:
    print(f"❌ 失败: {e}")

print("\n" + "="*80)
print("推荐方案总结")
print("="*80)
print("""
✅ 推荐使用天天基金网（东方财富）API：

1. 基金排行榜接口 ⭐⭐⭐⭐⭐
   - URL: http://fund.eastmoney.com/data/rankhandler.aspx
   - 优点: 稳定、数据全、支持分页
   - 已在 test_sina_api.py 中实现

2. 基金列表接口 ⭐⭐⭐⭐⭐
   - URL: http://fund.eastmoney.com/js/fundcode_search.js
   - 优点: 一次性获取所有基金代码和名称
   - 数据量: 10,000+ 个基金

3. 基金净值历史接口 ⭐⭐⭐⭐
   - URL: http://api.fund.eastmoney.com/f10/lsjz
   - 优点: 获取单个基金的历史净值数据
   - 可用于深度分析

💡 建议安装 akshare 库:
   pip install akshare
   
   akshare是专业的金融数据接口，包含：
   - 基金数据
   - 股票数据  
   - 期货数据
   - 宏观经济数据
   
   使用示例:
   import akshare as ak
   fund_df = ak.fund_open_fund_rank_em()  # 开放式基金排行
""")
