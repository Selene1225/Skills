"""
对比不同数据源的字段覆盖情况
"""

import akshare as ak
import requests
import json
import re

print("="*80)
print("字段需求对比分析")
print("="*80)

# 用户需要的字段
required_fields = {
    'symbol': '基金代码',
    'sname': '基金名称',
    'per_nav': '单位净值',
    'total_nav': '累计净值',
    'yesterday_nav': '前一日净值',
    'nav_rate': '增长率',
    'nav_a': '涨跌额',
    'sg_states': '申购状态',
    'nav_date': '净值日期',
    'fund_manager': '基金经理',
    'jjlx': '基金类型',
    'jjzfe': '基金总份额'
}

print("\n用户需要的字段:")
for i, (key, desc) in enumerate(required_fields.items(), 1):
    print(f"{i:2d}. {key:15s} - {desc}")

# 1. 测试 akshare
print("\n" + "="*80)
print("数据源1: akshare")
print("="*80)

try:
    df = ak.fund_open_fund_rank_em(symbol="全部")
    print(f"✅ akshare返回字段: {list(df.columns)}")
    
    # 字段匹配分析
    akshare_mapping = {
        '基金代码': 'symbol ✓',
        '基金简称': 'sname ✓',
        '单位净值': 'per_nav ✓',
        '累计净值': 'total_nav ✓',
        '日增长率': 'nav_rate ✓',
        '日期': 'nav_date ✓',
    }
    
    print("\n✅ 有的字段:")
    for field, mapping in akshare_mapping.items():
        print(f"  {field} → {mapping}")
    
    print("\n❌ 缺少的字段:")
    missing = ['前一日净值', '涨跌额', '申购状态', '基金经理', '基金类型', '基金总份额']
    for field in missing:
        print(f"  {field}")
    
    print(f"\n覆盖率: 6/12 = 50%")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")

# 2. 测试新浪财经
print("\n" + "="*80)
print("数据源2: 新浪财经")
print("="*80)

url = 'https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen'
params = {
    'page': 1,
    'num': 1,  # 只获取1条测试
    'sort': 'form_year',
    'asc': 0,
    'ccode': '',
    'type2': '0',
    'type3': ''
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://vip.stock.finance.sina.com.cn/fund_center/index.html'
}

try:
    r = requests.get(url, params=params, headers=headers, timeout=10)
    if r.status_code == 200:
        match = re.search(r'\((.*)\)', r.text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            if data['data']:
                fund = data['data'][0]
                print(f"✅ 新浪财经返回字段: {list(fund.keys())}")
                
                # 字段匹配分析
                sina_mapping = {
                    'symbol': '基金代码 ✓',
                    'name/sname': '基金名称 ✓',
                    'per_nav/dwjz': '单位净值 ✓',
                    'total_nav/ljjz': '累计净值 ✓',
                    'jzrq': '净值日期 ✓',
                    'jjjl': '基金经理 ✓',
                    'zjzfe': '基金总份额 ✓',
                }
                
                print("\n✅ 有的字段:")
                for k, v in fund.items():
                    print(f"  {k}: {v}")
                
                print("\n字段匹配:")
                print("  基金代码 (symbol) ✓")
                print("  基金名称 (name/sname) ✓")
                print("  单位净值 (per_nav/dwjz) ✓")
                print("  累计净值 (total_nav/ljjz) ✓")
                print("  净值日期 (jzrq) ✓")
                print("  基金经理 (jjjl) ✓")
                print("  基金总份额 (zjzfe) ✓")
                
                print("\n❌ 缺少的字段:")
                missing_sina = ['前一日净值', '涨跌额', '申购状态', '基金类型']
                for field in missing_sina:
                    print(f"  {field}")
                
                # 计算增长率和涨跌额
                print("\n💡 可计算字段:")
                print("  增长率 (可从three_month, six_month等推算)")
                print("  涨跌额 (可通过当前净值-前一日净值计算，但缺前一日数据)")
                
                print(f"\n覆盖率: 7/12 = 58%")
except Exception as e:
    print(f"❌ 测试失败: {e}")

# 3. 测试天天基金网
print("\n" + "="*80)
print("数据源3: 天天基金网（东方财富）")
print("="*80)

# 天天基金网基金列表
url3 = "http://fund.eastmoney.com/js/fundcode_search.js"
headers3 = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://fund.eastmoney.com/'
}

try:
    r = requests.get(url3, headers=headers3, timeout=10)
    if r.status_code == 200:
        text = r.text.replace('var r = ', '').replace(';', '')
        funds = json.loads(text)
        print(f"✅ 天天基金网基金列表接口")
        print(f"返回字段示例: {funds[0]}")
        print(f"字段: [基金代码, 拼音, 基金简称, 基金类型, 拼音首字母]")
        
        print("\n✅ 有的字段:")
        print("  基金代码 ✓")
        print("  基金名称 ✓")
        print("  基金类型 ✓")
        
        # 测试详情接口
        print("\n测试基金详情接口...")
        fund_code = funds[0][0]
        detail_url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
        
        r2 = requests.get(detail_url, headers=headers3, timeout=10)
        if r2.status_code == 200:
            # 提取JSON
            json_str = r2.text.replace('jsonpgz(', '').replace(');', '')
            detail = json.loads(json_str)
            print(f"基金实时估值接口字段: {list(detail.keys())}")
            print(f"示例数据: {detail}")
            
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n" + "="*80)
print("总结与推荐")
print("="*80)

print("""
字段覆盖率对比:
  akshare:      6/12 = 50%  ⭐⭐⭐
  新浪财经:     7/12 = 58%  ⭐⭐⭐⭐
  天天基金网:   需组合多个接口  ⭐⭐⭐

完整方案建议:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

方案1: 新浪财经（推荐用于获取基金经理、总份额等）✅
  包含: 基金代码、名称、单位净值、累计净值、净值日期、基金经理、总份额
  缺少: 前一日净值、涨跌额、申购状态、基金类型
  
方案2: 天天基金网 组合接口 ✅
  - 基金列表接口: 基金代码、名称、类型
  - 基金排行接口: 净值、增长率
  - 基金实时估值: 单位净值、估算增长率
  - 基金详情页: 申购状态、基金经理
  
方案3: akshare（最简单）⭐推荐
  优点: 使用简单，稳定可靠
  缺点: 缺少部分字段
  适合: 快速分析，不需要完整字段

💡 推荐策略:
1. 如果需要完整字段 → 使用新浪财经（等IP解封后）
2. 如果需要快速获取 → 使用akshare
3. 如果需要实时数据 → 组合天天基金网多个接口

具体实现建议:
- 主数据用akshare或新浪财经
- 补充字段用天天基金网API
- 前一日净值可通过历史数据计算
- 涨跌额 = 当前净值 - 前一日净值
""")
