"""
最终数据验证对比
对比天天基金网、akshare和新浪财经的数据
"""

import requests
import json
import re
import akshare as ak
import pandas as pd
import time

def get_eastmoney_detail(code):
    """从天天基金网估值接口获取单个基金实时估算数据"""
    try:
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'http://fund.eastmoney.com/'
        }
        
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            text = r.text.strip()
            if text.startswith('jsonpgz(') and text.endswith(');'):
                json_str = text[8:-2]
                data = json.loads(json_str)
                return {
                    'symbol': data.get('fundcode', ''),
                    'sname': data.get('name', ''),
                    'nav_date': data.get('jzrq', ''),
                    'per_nav': data.get('dwjz', ''),
                    'gsz': data.get('gsz', ''),  # 估算净值
                    'nav_rate': data.get('gszzl', ''),  # 估算增长率
                }
    except:
        pass
    return None

def get_eastmoney_rank(code):
    """从天天基金网排行榜接口获取单个基金数据"""
    try:
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
            'pn': '5000',
            'dx': '1'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'http://fund.eastmoney.com/'
        }
        
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200 and 'var rankData' in r.text:
            start = r.text.find('[')
            end = r.text.rfind(']') + 1
            data_str = r.text[start:end]
            data_list = json.loads(data_str)
            
            for item in data_list:
                parts = item.split(',')
                if parts[0] == code:
                    return {
                        'symbol': parts[0],
                        'sname': parts[1],
                        'nav_date': parts[3],
                        'per_nav': parts[4],
                        'total_nav': parts[5],
                        'nav_rate': parts[6],
                        'week_rate': parts[7],
                        'month_rate': parts[8],
                        'sg_states': parts[23] if len(parts) > 23 else '',
                        'fund_manager': parts[27] if len(parts) > 27 else '',
                        'fund_type': parts[28] if len(parts) > 28 else '',
                    }
    except Exception as e:
        print(f"    排行榜获取失败: {e}")
    return None

def get_akshare_data(code):
    """从akshare获取基金数据"""
    result = {}
    
    # 1. 排行榜数据
    try:
        df = ak.fund_open_fund_rank_em(symbol="全部")
        fund_row = df[df['基金代码'] == code]
        if not fund_row.empty:
            row = fund_row.iloc[0]
            result.update({
                'symbol': row['基金代码'],
                'sname': row['基金简称'],
                'nav_date': row['日期'],
                'per_nav': str(row['单位净值']),
                'total_nav': str(row['累计净值']),
                'nav_rate': str(row['日增长率']),
                'week_rate': str(row['近1周']),
                'month_rate': str(row['近1月']),
            })
    except Exception as e:
        print(f"    排行数据获取失败: {e}")
        return None
    
    # 2. 详细信息
    try:
        df = ak.fund_individual_basic_info_xq(symbol=code)
        for _, row in df.iterrows():
            if row['item'] == '基金经理':
                result['fund_manager'] = row['value']
            elif row['item'] == '最新规模':
                result['scale'] = row['value']
            elif row['item'] == '基金类型':
                result['fund_type'] = row['value']
    except:
        pass
    
    # 3. 前一日净值
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势", period="1月")
        if len(df) >= 2:
            today_nav = df.iloc[-1]['单位净值']
            yesterday_nav = df.iloc[-2]['单位净值']
            nav_a = today_nav - yesterday_nav
            result['yesterday_nav'] = yesterday_nav
            result['nav_a'] = nav_a
    except:
        pass
    
    return result

def get_sina_fund(code):
    """从新浪财经获取单个基金数据"""
    try:
        url = 'https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen'
        
        params = {
            'page': 1,
            'num': 100,
            'sort': 'form_year',
            'asc': 0,
            'ccode': code,
            'type2': '0',
            'type3': ''
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://vip.stock.finance.sina.com.cn/fund_center/index.html'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            text = response.text
            match = re.search(r'\((.*)\)', text, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                
                if 'data' in data and len(data['data']) > 0:
                    item = data['data'][0]
                    return {
                        'symbol': item.get('symbol', ''),
                        'sname': item.get('sname', ''),
                        'nav_date': item.get('nav_date', ''),
                        'per_nav': item.get('per_nav', ''),
                        'total_nav': item.get('total_nav', ''),
                        'yesterday_nav': item.get('yesterday_nav', ''),
                        'nav_rate': item.get('nav_rate', ''),
                        'nav_a': item.get('nav_a', ''),
                        'sg_states': item.get('sg_states', ''),
                        'fund_manager': item.get('fund_manager', ''),
                        'jjlx': item.get('jjlx', ''),
                        'jjzfe': item.get('jjzfe', ''),
                    }
    except:
        pass
    return None

def compare_field(name, val1, val2, val3=None):
    """对比字段值"""
    try:
        # 尝试数值对比
        num1 = float(val1) if val1 else 0
        num2 = float(val2) if val2 else 0
        num3 = float(val3) if val3 else 0
        
        if val3:
            match = abs(num1 - num2) < 0.01 and abs(num2 - num3) < 0.01
        else:
            match = abs(num1 - num2) < 0.01
    except:
        # 字符串对比
        if val3:
            match = str(val1) == str(val2) == str(val3)
        else:
            match = str(val1) == str(val2)
    
    status = "✅" if match else "❌"
    
    if val3:
        print(f"  {status} {name:12s}: 天天={str(val1):15s} | akshare={str(val2):15s} | 新浪={str(val3):15s}")
    else:
        print(f"  {status} {name:12s}: 天天={str(val1):15s} | akshare={str(val2):15s}")

print("="*120)
print("最终数据验证：天天基金网 vs akshare vs 新浪财经")
print("="*120)

# 测试基金
test_codes = ["000001", "000003", "110022", "161005"]

print("\n正在获取并对比数据...\n")

for i, code in enumerate(test_codes, 1):
    print("="*120)
    print(f"【基金{i}】代码: {code}")
    print("="*120)
    
    # 1. 天天基金网（排行榜接口）
    print("\n1️⃣  天天基金网排行榜数据:")
    em_rank = get_eastmoney_rank(code)
    if em_rank:
        print(f"  基金名称: {em_rank['sname']}")
        print(f"  净值日期: {em_rank['nav_date']}")
        print(f"  单位净值: {em_rank['per_nav']}")
        print(f"  累计净值: {em_rank['total_nav']}")
        print(f"  日增长率: {em_rank['nav_rate']}%")
        print(f"  申购状态: {em_rank['sg_states']}")
    else:
        print("  ❌ 获取失败")
    
    # 2. akshare
    print("\n2️⃣  akshare数据:")
    ak_data = get_akshare_data(code)
    if ak_data:
        print(f"  基金名称: {ak_data['sname']}")
        print(f"  净值日期: {ak_data['nav_date']}")
        print(f"  单位净值: {ak_data['per_nav']}")
        print(f"  累计净值: {ak_data['total_nav']}")
        print(f"  日增长率: {ak_data['nav_rate']}%")
        print(f"  基金经理: {ak_data.get('fund_manager', '无')}")
        print(f"  基金类型: {ak_data.get('fund_type', '无')}")
        if 'yesterday_nav' in ak_data:
            print(f"  前一日净值: {ak_data['yesterday_nav']}")
            print(f"  涨跌额: {ak_data['nav_a']:.4f}")
    else:
        print("  ❌ 获取失败")
    
    # 3. 新浪财经
    print("\n3️⃣  新浪财经数据:")
    sina_data = get_sina_fund(code)
    if sina_data:
        print(f"  基金名称: {sina_data['sname']}")
        print(f"  净值日期: {sina_data['nav_date']}")
        print(f"  单位净值: {sina_data['per_nav']}")
        print(f"  累计净值: {sina_data['total_nav']}")
        print(f"  日增长率: {sina_data['nav_rate']}%")
        print(f"  前一日净值: {sina_data['yesterday_nav']}")
        print(f"  涨跌额: {sina_data['nav_a']}")
        print(f"  基金经理: {sina_data['fund_manager']}")
        print(f"  基金类型: {sina_data['jjlx']}")
    else:
        print("  ⚠️ 获取失败（可能仍被限制）")
    
    # 4. 数据对比
    if em_rank and ak_data:
        print("\n4️⃣  数据对比（天天 vs akshare）:")
        compare_field('基金名称', em_rank['sname'], ak_data['sname'])
        compare_field('单位净值', em_rank['per_nav'], ak_data['per_nav'])
        compare_field('累计净值', em_rank['total_nav'], ak_data['total_nav'])
        compare_field('日增长率', em_rank['nav_rate'], ak_data['nav_rate'])
        compare_field('近1周', em_rank['week_rate'], ak_data.get('week_rate', ''))
        compare_field('近1月', em_rank['month_rate'], ak_data.get('month_rate', ''))
        
        if sina_data:
            print("\n5️⃣  三源数据对比:")
            compare_field('单位净值', em_rank['per_nav'], ak_data['per_nav'], sina_data['per_nav'])
            compare_field('累计净值', em_rank['total_nav'], ak_data['total_nav'], sina_data['total_nav'])
    
    print("\n")
    if i < len(test_codes):
        time.sleep(1)

print("="*120)
print("总结")
print("="*120)
print("""
验证结论:

1. 数据一致性分析:
   - 天天基金网排行榜和akshare的基础数据（净值、增长率）应该一致
   - 如果两者一致，说明数据源可靠
   - 新浪财经如果可用，可以作为第三方验证

2. 字段覆盖情况:
   ✅ 天天基金网排行榜: 净值、增长率、近1周/1月增长率 (7/12字段)
   ✅ akshare: 以上字段 + 基金经理、基金类型、前一日净值、涨跌额 (11/12字段)
   ✅ 新浪财经（如可用）: 完整12字段

3. 最终推荐方案:
   方案A - 天天基金网为主:
     - 使用天天基金网排行榜获取主要数据（快速、稳定）
     - 使用akshare补充缺失字段（基金经理、前一日净值等）
     - 优点：快速稳定
     - 缺点：需要两个数据源，有少量字段仍缺失
   
   方案B - 纯akshare:
     - 全部使用akshare获取数据
     - 优点：代码简单，字段完整度高
     - 缺点：速度稍慢
   
   方案C - 等待新浪解封:
     - 使用原有新浪财经接口
     - 优点：字段最完整
     - 缺点：有反爬风险，不稳定
""")
