"""
对比天天基金网和新浪财经的数据
验证数据的准确性
"""

import requests
import json
import re
import pandas as pd

def get_eastmoney_data(limit=20):
    """从天天基金网获取数据"""
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
        'pn': str(limit),
        'dx': '1'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'http://fund.eastmoney.com/'
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200 and 'var rankData' in r.text:
            start = r.text.find('[')
            end = r.text.rfind(']') + 1
            data_str = r.text[start:end]
            data_list = json.loads(data_str)
            
            result = []
            for item in data_list:
                parts = item.split(',')
                if len(parts) >= 8:
                    fund = {
                        'source': '天天基金',
                        'symbol': parts[0],
                        'sname': parts[1],
                        'nav_date': parts[3],
                        'per_nav': parts[4],
                        'total_nav': parts[5],
                        'nav_rate': parts[6],
                        'week_rate': parts[7] if len(parts) > 7 else '',
                        'month_rate': parts[8] if len(parts) > 8 else '',
                        'sg_states': parts[23] if len(parts) > 23 else '',
                        'nav_a_estimate': parts[18] if len(parts) > 18 else '',  # 涨跌额估算
                    }
                    result.append(fund)
            
            return result
    except Exception as e:
        print(f"天天基金网获取失败: {e}")
        return None

def get_sina_data(limit=20):
    """从新浪财经获取数据"""
    url = 'https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen'
    
    params = {
        'page': 1,
        'num': limit,
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
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            text = response.text
            
            # 提取JSONP中的JSON数据
            match = re.search(r'\((.*)\)', text, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                
                if 'data' in data:
                    result = []
                    for fund in data['data']:
                        result.append({
                            'source': '新浪财经',
                            'symbol': str(fund.get('symbol', '')),
                            'sname': fund.get('name', ''),
                            'nav_date': fund.get('jzrq', ''),
                            'per_nav': str(fund.get('per_nav', '')),
                            'total_nav': str(fund.get('total_nav', '')),
                            'nav_rate': str(fund.get('form_year', '')),  # 今年以来
                            'three_month': str(fund.get('three_month', '')),
                            'six_month': str(fund.get('six_month', '')),
                            'fund_manager': fund.get('jjjl', ''),
                            'jjzfe': str(fund.get('zjzfe', '')),
                        })
                    return result
    except Exception as e:
        print(f"新浪财经获取失败: {e}")
        return None

def compare_data(eastmoney_data, sina_data):
    """对比两个数据源"""
    print("="*100)
    print("数据源对比分析")
    print("="*100)
    
    # 创建字典方便查找
    em_dict = {f['symbol']: f for f in eastmoney_data}
    sina_dict = {f['symbol']: f for f in sina_data}
    
    # 找出共同的基金
    common_codes = set(em_dict.keys()) & set(sina_dict.keys())
    print(f"\n天天基金数据: {len(eastmoney_data)} 条")
    print(f"新浪财经数据: {len(sina_data)} 条")
    print(f"共同基金: {len(common_codes)} 个")
    
    if not common_codes:
        print("\n⚠️ 没有共同的基金代码，可能两个接口返回的基金集合不同")
        print("\n天天基金前5个:")
        for fund in eastmoney_data[:5]:
            print(f"  {fund['symbol']} - {fund['sname']}")
        print("\n新浪财经前5个:")
        for fund in sina_data[:5]:
            print(f"  {fund['symbol']} - {fund['sname']}")
        return
    
    # 对比共同基金的数据
    print(f"\n" + "="*100)
    print(f"对比前{min(10, len(common_codes))}个共同基金的数据")
    print("="*100)
    
    for i, code in enumerate(list(common_codes)[:10], 1):
        em_fund = em_dict[code]
        sina_fund = sina_dict[code]
        
        print(f"\n【基金{i}】{code} - {em_fund['sname']}")
        print("-"*100)
        
        # 对比各字段
        comparisons = [
            ('基金代码', 'symbol', 'symbol'),
            ('基金名称', 'sname', 'sname'),
            ('单位净值', 'per_nav', 'per_nav'),
            ('累计净值', 'total_nav', 'total_nav'),
            ('净值日期', 'nav_date', 'nav_date'),
        ]
        
        all_match = True
        for field_name, em_key, sina_key in comparisons:
            em_val = em_fund.get(em_key, '')
            sina_val = sina_fund.get(sina_key, '')
            
            # 处理日期格式差异
            if field_name == '净值日期':
                em_val_clean = em_val[:10] if em_val else ''
                sina_val_clean = sina_val[:10] if sina_val else ''
                match = em_val_clean == sina_val_clean
            else:
                # 数值比较（允许小误差）
                try:
                    em_num = float(em_val) if em_val else 0
                    sina_num = float(sina_val) if sina_val else 0
                    match = abs(em_num - sina_num) < 0.0001
                except:
                    match = str(em_val) == str(sina_val)
            
            status = "✅" if match else "❌"
            if not match:
                all_match = False
            
            print(f"  {status} {field_name:12s}: 天天={em_val:20s} | 新浪={sina_val:20s}")
        
        # 显示独有字段
        print(f"\n  天天基金独有:")
        print(f"    申购状态: {em_fund.get('sg_states', '')}")
        print(f"    涨跌额估算: {em_fund.get('nav_a_estimate', '')}")
        
        print(f"\n  新浪财经独有:")
        print(f"    基金经理: {sina_fund.get('fund_manager', '')}")
        print(f"    基金总份额: {sina_fund.get('jjzfe', '')}")
        print(f"    近三月收益: {sina_fund.get('three_month', '')}%")
        print(f"    近半年收益: {sina_fund.get('six_month', '')}%")
    
    print("\n" + "="*100)
    print("总结")
    print("="*100)
    
    print("""
对比结论:

1. 基础字段（代码、名称、净值）:
   ✅ 两个数据源的基础数据应该一致
   ⚠️ 如果不一致，说明数据更新时间不同或接口有问题

2. 独有字段:
   天天基金网:
   - 申购状态 ✅
   - 涨跌额估算 ✅（但不是真实涨跌额）
   
   新浪财经:
   - 基金经理 ✅
   - 基金总份额 ✅
   - 收益率数据更全面 ✅

3. 建议:
   - 基础数据用天天基金（稳定）
   - 基金经理、份额用新浪（如果可用）
   - 或使用akshare组合多个接口
""")

if __name__ == "__main__":
    print("正在从两个数据源获取数据...\n")
    
    # 获取数据
    print("1. 获取天天基金数据...")
    em_data = get_eastmoney_data(limit=50)
    if em_data:
        print(f"   ✅ 成功获取 {len(em_data)} 条")
    else:
        print(f"   ❌ 获取失败")
    
    print("\n2. 获取新浪财经数据...")
    sina_data = get_sina_data(limit=50)
    if sina_data:
        print(f"   ✅ 成功获取 {len(sina_data)} 条")
    else:
        print(f"   ⚠️ 新浪财经可能被限制，等待30秒后重试...")
        import time
        time.sleep(5)
        sina_data = get_sina_data(limit=50)
        if sina_data:
            print(f"   ✅ 重试成功，获取 {len(sina_data)} 条")
        else:
            print(f"   ❌ 仍然失败，可能需要等待更长时间")
    
    print()
    
    # 对比数据
    if em_data and sina_data:
        compare_data(em_data, sina_data)
    else:
        print("⚠️ 数据获取不完整，无法对比")

