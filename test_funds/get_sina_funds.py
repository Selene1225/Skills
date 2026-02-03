"""
从新浪财经获取开放式基金数据

接口说明:
- URL: https://vip.stock.finance.sina.com.cn/fund_center/index.html#jzkfgpx
- API: https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen
- 数据总量: 24,439+ 个开放式基金
- 更新频率: 每日更新
"""

import requests
import json
import re
import time
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


# 创建一个会话对象，复用连接
session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_sina_fund_data(page=1, page_size=40, sort='form_year', asc=0):
    """
    从新浪财经获取开放式基金数据
    
    参数:
        page: 页码（从1开始）
        page_size: 每页数量（建议40，最大100）
        sort: 排序字段
            - 'form_year': 今年以来收益率 (默认)
            - 'form_start': 成立以来收益率
            - 'one_year': 近一年收益率
            - 'six_month': 近半年收益率
            - 'three_month': 近三月收益率
            - 'per_nav': 单位净值
            - 'total_nav': 累计净值
        asc: 0=降序, 1=升序
        
    返回:
        字典包含:
            - total_num: 总基金数量
            - data: 基金数据列表
            - exec_time: 执行时间
            - sort_time: 排序时间
            - lastupdate: 最后更新时间
            
        每条基金数据包含字段:
            - symbol: 基金代码
            - name: 基金名称
            - per_nav: 单位净值
            - total_nav: 累计净值
            - jzrq: 净值日期
            - three_month: 近三月收益率(%)
            - six_month: 近半年收益率(%)
            - one_year: 近一年收益率(%)
            - form_year: 今年以来收益率(%)
            - form_start: 成立以来收益率(%)
            - clrq: 成立日期
            - jjjl: 基金经理
            - zmjgm: 资产规模(万元)
            - zjzfe: 资金总份额
    """
    url = 'https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen'
    
    params = {
        'page': page,
        'num': page_size,
        'sort': sort,
        'asc': asc,
        'ccode': '',
        'type2': '0',  # 0=全部开放式基金
        'type3': ''
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://vip.stock.finance.sina.com.cn/fund_center/index.html'
    }
    
    try:
        response = session.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            text = response.text
            
            # 提取JSONP中的JSON数据
            match = re.search(r'\((.*)\)', text, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data
            else:
                print(f"无法从响应中提取JSON数据")
                return None
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None
            
    except requests.Timeout:
        print(f"请求超时")
        return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def get_all_funds(max_pages=None, page_size=40, sort='form_year', delay=2.0, max_retries=3):
    """
    批量获取所有基金数据
    
    参数:
        max_pages: 最大页数，None表示获取全部
        page_size: 每页数量
        sort: 排序字段
        delay: 每次请求间隔(秒)，避免被封IP，建议>=2秒
        max_retries: 失败后最大重试次数
        
    返回:
        所有基金数据列表
    """
    all_funds = []
    page = 1
    total_num = 0
    
    print(f"开始获取新浪财经开放式基金数据...")
    print(f"注意: 新浪有反爬限制，请求间隔设为{delay}秒，请耐心等待...")
    
    while True:
        if max_pages and page > max_pages:
            break
        
        # 重试机制
        retry_count = 0
        result = None
        
        while retry_count < max_retries:
            result = get_sina_fund_data(page=page, page_size=page_size, sort=sort)
            
            if result and result.get('data'):
                break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = delay * (retry_count + 1)
                    print(f"第{page}页获取失败，{wait_time}秒后重试 ({retry_count}/{max_retries})...")
                    time.sleep(wait_time)
        
        if result and result.get('data'):
            all_funds.extend(result['data'])
            total_num = result['total_num']
            
            print(f"第{page}页获取成功，本页{len(result['data'])}条，累计{len(all_funds)}条 / 总计{total_num}条")
            
            # 如果已经获取完所有数据，退出
            if len(all_funds) >= total_num:
                break
                
            page += 1
            time.sleep(delay)  # 礼貌抓取
        else:
            print(f"第{page}页多次重试后仍失败，停止获取")
            break
    
    print(f"\n✅ 获取完成！总计 {len(all_funds)} 条基金数据")
    return all_funds


def funds_to_dataframe(funds_data):
    """
    将基金数据转换为pandas DataFrame
    
    参数:
        funds_data: 基金数据列表
        
    返回:
        pandas DataFrame
    """
    if not funds_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(funds_data)
    
    # 数据类型转换
    numeric_columns = ['per_nav', 'total_nav', 'three_month', 'six_month', 
                      'one_year', 'form_year', 'form_start', 'zmjgm', 'zjzfe']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 日期转换
    if 'jzrq' in df.columns:
        df['jzrq'] = pd.to_datetime(df['jzrq'], errors='coerce')
    if 'clrq' in df.columns:
        df['clrq'] = pd.to_datetime(df['clrq'], errors='coerce')
    
    return df


if __name__ == "__main__":
    # 示例1: 获取第一页数据
    print("=" * 80)
    print("示例1: 获取今年以来收益率最高的前40个基金")
    print("=" * 80)
    
    result = get_sina_fund_data(page=1, page_size=40, sort='form_year', asc=0)
    
    if result:
        print(f"\n总基金数量: {result['total_num']:,} 个")
        print(f"本次获取: {len(result['data'])} 条")
        print(f"最后更新: {result['lastupdate']}\n")
        
        # 显示前10个
        print("Top 10 基金:")
        for i, fund in enumerate(result['data'][:10], 1):
            symbol = str(fund['symbol'])
            name = fund['name']
            form_year = fund.get('form_year', 'N/A')
            if isinstance(form_year, (int, float)):
                print(f"{i:2d}. {symbol:8s} {name:35s} 今年来: {form_year:>8.2f}%")
            else:
                print(f"{i:2d}. {symbol:8s} {name:35s} 今年来: {form_year:>8s}")
    
    # 示例2: 批量获取数据并保存
    print("\n" + "=" * 80)
    print("示例2: 批量获取200条基金数据并保存为CSV")
    print("=" * 80)
    
    all_funds = get_all_funds(max_pages=5, page_size=40, delay=2.5)
    
    if all_funds:
        df = funds_to_dataframe(all_funds)
        
        # 保存为CSV
        output_file = 'sina_funds_data.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: {output_file}")
        
        # 显示数据摘要
        print(f"\n数据概览:")
        print(f"  基金数量: {len(df)}")
        print(f"  字段数量: {len(df.columns)}")
        print(f"\n前5行数据:")
        print(df[['symbol', 'name', 'per_nav', 'form_year', 'form_start']].head())
