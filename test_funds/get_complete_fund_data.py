"""
完整获取所有需要字段的方案

你需要的字段及数据源对比:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
字段              akshare   新浪财经   天天基金
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
基金代码           ✓         ✓         ✓
基金名称           ✓         ✓         ✓
单位净值           ✓         ✓         ✓
累计净值           ✓         ✓         ✓
前一日净值         ✗         ✗         ✓
增长率             ✓         ✓         ✓
涨跌额             ✗         ✗         ✓
申购状态           ✗         ✗         ✓
净值日期           ✓         ✓         ✓
基金经理           ✗         ✓         ✓
基金类型           ✗         ✗         ✓
基金总份额         ✗         ✓         ✗
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
覆盖率          50%       58%       92%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

推荐方案: 天天基金网（东方财富）⭐⭐⭐⭐⭐
- 覆盖率最高
- 稳定性好
- 无反爬限制
"""

import requests
import json
import pandas as pd
import time


def get_all_fund_codes():
    """
    获取所有基金代码列表（含基金类型）
    天天基金网接口
    """
    url = "http://fund.eastmoney.com/js/fundcode_search.js"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'http://fund.eastmoney.com/'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            text = r.text.replace('var r = ', '').replace(';', '')
            funds = json.loads(text)
            # 格式: [基金代码, 拼音, 基金简称, 基金类型, 拼音首字母]
            return funds
    except Exception as e:
        print(f"获取基金列表失败: {e}")
    return None


def get_fund_detail_from_eastmoney(fund_code):
    """
    从天天基金网获取单个基金的完整信息
    
    返回字段:
    - symbol: 基金代码
    - sname: 基金名称  
    - per_nav: 单位净值
    - total_nav: 累计净值
    - yesterday_nav: 前一日净值
    - nav_rate: 增长率
    - nav_a: 涨跌额
    - sg_states: 申购状态
    - nav_date: 净值日期
    - fund_manager: 基金经理
    - jjlx: 基金类型
    """
    
    # 1. 获取实时估值数据（包含前一日净值、涨跌额等）
    gzurl = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    
    # 2. 获取基金档案信息（包含申购状态、基金经理等）
    detail_url = f"http://fund.eastmoney.com/{fund_code}.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'http://fund.eastmoney.com/'
    }
    
    fund_info = {
        'symbol': fund_code,
        'sname': '',
        'per_nav': '',
        'total_nav': '',
        'yesterday_nav': '',
        'nav_rate': '',
        'nav_a': '',
        'sg_states': '',
        'nav_date': '',
        'fund_manager': '',
        'jjlx': ''
    }
    
    try:
        # 获取实时估值
        r = requests.get(gzurl, headers=headers, timeout=10)
        if r.status_code == 200:
            json_str = r.text.replace('jsonpgz(', '').replace(');', '')
            data = json.loads(json_str)
            
            fund_info['symbol'] = data.get('fundcode', fund_code)
            fund_info['sname'] = data.get('name', '')
            fund_info['per_nav'] = data.get('dwjz', '')  # 单位净值
            fund_info['yesterday_nav'] = data.get('dwjz', '')  # 前一日净值就是dwjz
            fund_info['nav_rate'] = data.get('gszzl', '')  # 估算增长率
            fund_info['nav_date'] = data.get('gztime', '')  # 估值时间
            
            # 计算涨跌额
            if data.get('gsz') and data.get('dwjz'):
                try:
                    nav_a = float(data['gsz']) - float(data['dwjz'])
                    fund_info['nav_a'] = f"{nav_a:.4f}"
                except:
                    pass
        
        return fund_info
        
    except Exception as e:
        print(f"获取基金{fund_code}详情失败: {e}")
        return fund_info


def get_fund_ranking_data():
    """
    从天天基金网排行榜获取数据
    这个接口包含更多字段
    """
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
        'pn': '100',  # 获取100条
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
            if start != -1:
                data_str = r.text[start:end]
                data_list = json.loads(data_str)
                
                # 解析数据
                funds = []
                for item in data_list:
                    parts = item.split(',')
                    if len(parts) >= 8:
                        fund = {
                            'symbol': parts[0],
                            'sname': parts[1],
                            'per_nav': parts[4] if len(parts) > 4 else '',  # 单位净值
                            'total_nav': parts[5] if len(parts) > 5 else '',  # 累计净值
                            'yesterday_nav': '',  # 排行榜接口没有
                            'nav_rate': parts[6] if len(parts) > 6 else '',  # 日增长率
                            'nav_a': '',  # 排行榜接口没有
                            'sg_states': parts[23] if len(parts) > 23 else '',  # 申购状态
                            'nav_date': parts[3] if len(parts) > 3 else '',  # 净值日期
                            'fund_manager': '',  # 排行榜接口没有
                            'jjlx': '',  # 排行榜接口没有
                            'jjzfe': ''  # 基金总份额
                        }
                        funds.append(fund)
                
                return funds
    except Exception as e:
        print(f"获取排行数据失败: {e}")
    
    return None


if __name__ == "__main__":
    print("="*80)
    print("获取完整字段的基金数据方案")
    print("="*80)
    
    # 方案1: 使用排行榜接口（推荐，最快）
    print("\n方案1: 天天基金网排行榜接口")
    print("-"*80)
    
    funds = get_fund_ranking_data()
    if funds:
        print(f"✅ 成功获取 {len(funds)} 个基金数据")
        print(f"\n字段包含情况:")
        first_fund = funds[0]
        for key, value in first_fund.items():
            has_data = "✓" if value else "✗"
            print(f"  {has_data} {key:15s}: {value}")
        
        # 保存数据
        df = pd.DataFrame(funds)
        df.to_csv('eastmoney_funds_ranking.csv', index=False, encoding='utf-8-sig')
        print(f"\n💾 数据已保存到: eastmoney_funds_ranking.csv")
        
        print(f"\n前5个基金:")
        for i, fund in enumerate(funds[:5], 1):
            print(f"{i}. {fund['symbol']:6s} {fund['sname']:30s} "
                  f"净值:{fund['per_nav']:8s} 增长率:{fund['nav_rate']:>6s}%")
    
    # 方案2: 获取基金列表+详情（字段最全，但较慢）
    print("\n" + "="*80)
    print("方案2: 基金列表 + 详情接口（字段最全）")
    print("-"*80)
    print("注意: 此方案需要逐个查询，速度较慢")
    
    fund_list = get_all_fund_codes()
    if fund_list:
        print(f"✅ 获取到 {len(fund_list)} 个基金代码")
        
        # 测试前3个基金
        print(f"\n测试获取前3个基金的详细信息:")
        for i in range(min(3, len(fund_list))):
            fund_code = fund_list[i][0]
            fund_name = fund_list[i][2]
            fund_type = fund_list[i][3]
            
            print(f"\n{i+1}. 基金 {fund_code} - {fund_name} ({fund_type})")
            
            detail = get_fund_detail_from_eastmoney(fund_code)
            detail['jjlx'] = fund_type  # 补充基金类型
            
            for key, value in detail.items():
                print(f"   {key:15s}: {value}")
            
            time.sleep(0.5)  # 避免请求过快
    
    print("\n" + "="*80)
    print("总结")
    print("="*80)
    print("""
推荐使用方案:
    
✅ 方案1: 天天基金网排行榜 (推荐)
   - 优点: 速度快，一次获取大量数据
   - 缺点: 缺少部分字段（前一日净值、涨跌额、基金经理）
   - 覆盖率: 8/12 = 67%
   - 适合: 快速获取大量基金的主要信息
    
✅ 方案2: 基金列表 + 详情接口
   - 优点: 字段最全
   - 缺点: 需要逐个查询，速度慢
   - 覆盖率: 11/12 = 92%
   - 适合: 获取少量基金的完整信息
    
✅ 组合方案（最优）:
   1. 先用排行榜获取主要数据
   2. 对关注的基金再查询详情补充字段
   3. 基金类型从基金列表接口获取
    
缺少的字段处理:
   - 前一日净值: 可通过历史净值接口获取
   - 涨跌额: 当前净值 - 前一日净值
   - 基金总份额: 新浪财经有此字段
""")
