"""
使用akshare和天天基金网对比数据
验证计算的准确性
"""

import requests
import json
import akshare as ak
import pandas as pd

def get_eastmoney_fund(code):
    """从天天基金网获取单个基金数据（直接访问基金详情页）"""
    try:
        # 方法1: 通过基金详情页API获取实时数据
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'http://fund.eastmoney.com/'
        }
        
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            # 返回格式: jsonpgz({"fundcode":"000001","name":"...","jzrq":"...","dwjz":"...",...});
            text = r.text.strip()
            if text.startswith('jsonpgz(') and text.endswith(');'):
                json_str = text[8:-2]
                data = json.loads(json_str)
                return {
                    'symbol': data.get('fundcode', ''),
                    'sname': data.get('name', ''),
                    'nav_date': data.get('jzrq', ''),
                    'per_nav': data.get('dwjz', ''),
                    'total_nav': data.get('ljjz', ''),
                    'nav_rate': data.get('gszzl', ''),  # 估算增长率
                    'gsz': data.get('gsz', ''),  # 估算净值
                }
    except Exception as e:
        print(f"    详情页获取失败: {e}")
    
    # 方法2: 从排行榜接口搜索
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
            'pn': '5000',  # 增加数量以便查找
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
                        'quarter_rate': parts[9],
                        'half_year_rate': parts[10],
                        'year_rate': parts[11],
                        'sg_states': parts[23] if len(parts) > 23 else '',
                        'fund_manager': parts[27] if len(parts) > 27 else '',
                        'fund_type': parts[28] if len(parts) > 28 else '',
                    }
    except Exception as e:
        print(f"    排行榜获取失败: {e}")
    
    return None

def get_akshare_fund_rank(code):
    """从akshare获取基金排行数据"""
    try:
        df = ak.fund_open_fund_rank_em(symbol="全部")
        fund_row = df[df['基金代码'] == code]
        if not fund_row.empty:
            row = fund_row.iloc[0]
            return {
                'symbol': row['基金代码'],
                'sname': row['基金简称'],
                'nav_date': row['日期'],
                'per_nav': str(row['单位净值']),
                'total_nav': str(row['累计净值']),
                'nav_rate': str(row['日增长率']),
                'week_rate': str(row['近1周']),
                'month_rate': str(row['近1月']),
                'quarter_rate': str(row['近3月']),
                'half_year_rate': str(row['近6月']),
                'year_rate': str(row['近1年']),
            }
    except:
        pass
    return None

def get_akshare_fund_detail(code):
    """从akshare获取基金详细信息"""
    try:
        df = ak.fund_individual_basic_info_xq(symbol=code)
        
        result = {}
        for _, row in df.iterrows():
            if row['item'] == '基金经理':
                result['fund_manager'] = row['value']
            elif row['item'] == '最新规模':
                result['scale'] = row['value']
            elif row['item'] == '基金类型':
                result['fund_type'] = row['value']
        
        return result
    except:
        return {}

def get_akshare_yesterday_nav(code):
    """从akshare获取前一日净值"""
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势", period="1月")
        if len(df) >= 2:
            today_nav = df.iloc[-1]['单位净值']
            yesterday_nav = df.iloc[-2]['单位净值']
            nav_a = today_nav - yesterday_nav
            
            return {
                'yesterday_nav': yesterday_nav,
                'nav_a_calc': nav_a,
                'today_nav': today_nav
            }
    except:
        pass
    return {}

print("="*100)
print("数据验证：天天基金网 vs akshare")
print("="*100)

# 测试几个基金
test_codes = ["000001", "000002", "000003", "110022", "161005"]

print("\n正在获取数据...")

for i, code in enumerate(test_codes, 1):
    print(f"\n" + "="*100)
    print(f"【基金{i}】代码: {code}")
    print("="*100)
    
    # 1. 天天基金网数据
    print("\n1️⃣  天天基金网数据:")
    em_data = get_eastmoney_fund(code)
    if em_data:
        print(f"  基金名称: {em_data['sname']}")
        print(f"  净值日期: {em_data['nav_date']}")
        print(f"  单位净值: {em_data['per_nav']}")
        print(f"  累计净值: {em_data.get('total_nav', '')}")
        print(f"  日增长率: {em_data.get('nav_rate', '')}%")
        if 'week_rate' in em_data:
            print(f"  近1周: {em_data['week_rate']}%")
            print(f"  近1月: {em_data['month_rate']}%")
        if 'sg_states' in em_data:
            print(f"  申购状态: {em_data['sg_states']}")
        if 'gsz' in em_data:
            print(f"  估算净值: {em_data['gsz']}")
    else:
        print("  ❌ 获取失败")
        continue
    
    # 2. akshare排行数据
    print("\n2️⃣  akshare排行数据:")
    ak_rank = get_akshare_fund_rank(code)
    if ak_rank:
        print(f"  基金名称: {ak_rank['sname']}")
        print(f"  净值日期: {ak_rank['nav_date']}")
        print(f"  单位净值: {ak_rank['per_nav']}")
        print(f"  累计净值: {ak_rank['total_nav']}")
        print(f"  日增长率: {ak_rank['nav_rate']}%")
        print(f"  近1周: {ak_rank['week_rate']}%")
        print(f"  近1月: {ak_rank['month_rate']}%")
    else:
        print("  ❌ 获取失败")
    
    # 3. 对比基础数据
    if em_data and ak_rank:
        print("\n3️⃣  数据对比:")
        
        fields = [
            ('基金名称', 'sname'),
            ('单位净值', 'per_nav'),
            ('累计净值', 'total_nav'),
            ('日增长率', 'nav_rate'),
        ]
        
        # 如果天天基金有更多数据，加入对比
        if 'week_rate' in em_data and 'week_rate' in ak_rank:
            fields.extend([
                ('近1周', 'week_rate'),
                ('近1月', 'month_rate'),
            ])
        
        for field_name, key in fields:
            em_val = em_data.get(key, '')
            ak_val = ak_rank.get(key, '')
            
            try:
                em_num = float(em_val) if em_val else 0
                ak_num = float(ak_val) if ak_val else 0
                match = abs(em_num - ak_num) < 0.01
            except:
                match = str(em_val) == str(ak_val)
            
            status = "✅" if match else "❌"
            print(f"  {status} {field_name:10s}: 天天={em_val:15s} | akshare={ak_val:15s}")
    
    # 4. akshare详细信息
    print("\n4️⃣  akshare详细信息（基金经理等）:")
    ak_detail = get_akshare_fund_detail(code)
    if ak_detail:
        print(f"  基金经理: {ak_detail.get('fund_manager', '无')}")
        print(f"  最新规模: {ak_detail.get('scale', '无')}")
        print(f"  基金类型: {ak_detail.get('fund_type', '无')}")
    else:
        print("  ⚠️ 详细信息获取失败")
    
    # 5. 前一日净值（计算涨跌额）
    print("\n5️⃣  前一日净值计算:")
    yesterday_data = get_akshare_yesterday_nav(code)
    if yesterday_data:
        print(f"  当日净值: {yesterday_data['today_nav']}")
        print(f"  前一日净值: {yesterday_data['yesterday_nav']}")
        print(f"  涨跌额(计算): {yesterday_data['nav_a_calc']:.4f}")
        
        # 与天天基金的估算对比（如果有）
        if em_data and em_data.get('nav_a_estimate'):
            try:
                em_estimate = float(em_data['nav_a_estimate'])
                ak_calc = float(yesterday_data['nav_a_calc'])
                diff = abs(em_estimate - ak_calc)
                print(f"  涨跌额(天天估算): {em_estimate:.4f}")
                print(f"  差异: {diff:.4f}")
            except:
                pass
    else:
        print("  ⚠️ 历史净值获取失败")
    
    print("\n")
    import time
    if i < len(test_codes):
        time.sleep(0.5)  # 避免请求过快

print("="*100)
print("总结")
print("="*100)

print("""
验证结论:

1. 基础数据一致性:
   ✅ 天天基金网和akshare的基础数据（净值、增长率等）应该一致
   ✅ 如果一致，说明两个数据源都可靠

2. 补充字段验证:
   ✅ akshare可以提供基金经理（fund_individual_basic_info_xq）
   ✅ akshare可以计算前一日净值和涨跌额（fund_open_fund_info_em）
   ⚠️ 涨跌额的计算值 vs 天天基金的估算值可能有差异

3. 最终方案建议:
   - 主数据：天天基金网（稳定、快速）
   - 补充字段：akshare（基金经理、前一日净值）
   - 或者全用akshare（简单但可能较慢）
""")
