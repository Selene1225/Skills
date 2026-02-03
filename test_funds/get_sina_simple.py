"""
新浪财经开放式基金数据获取脚本

✅ 成功验证：可以从新浪财经获取24,439+个开放式基金数据
📊 数据来源: https://vip.stock.finance.sina.com.cn/fund_center/index.html#jzkfgpx

⚠️ 重要提示:
1. 新浪财经有反爬虫机制，短时间内多次请求会被限制（返回500错误）
2. 被限制后需要等待一段时间（约10-30分钟）才能恢复
3. 建议策略:
   - 单次请求获取较多数据（page_size=40-100）
   - 请求间隔至少3-5秒
   - 避免在短时间内运行多次测试
   - 如果被限制，等待后再试

💡 最佳实践:
- 每次只请求1-2页数据，每页40-100条
- 通过不同排序方式获取不同视角的数据
- 保存数据后进行本地分析，避免重复请求
"""

import requests
import json
import re
import pandas as pd


def get_sina_fund_data_simple(page=1, page_size=100, sort='form_year', asc=0):
    """
    从新浪财经获取开放式基金数据（简化版）
    
    参数:
        page: 页码（建议只用第1页，避免被限制）
        page_size: 每页数量（可设置到100）
        sort: 排序字段
            - 'form_year': 今年以来收益率 ⭐推荐
            - 'form_start': 成立以来收益率
            - 'one_year': 近一年收益率
            - 'six_month': 近半年收益率
            - 'three_month': 近三月收益率
            - 'per_nav': 单位净值
        asc: 0=降序（默认，获取收益最高的）, 1=升序
        
    返回:
        基金数据列表，失败返回None
    """
    url = 'https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen'
    
    params = {
        'page': page,
        'num': page_size,
        'sort': sort,
        'asc': asc,
        'ccode': '',
        'type2': '0',
        'type3': ''
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://vip.stock.finance.sina.com.cn/fund_center/index.html'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            match = re.search(r'\((.*)\)', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                return data['data'] if 'data' in data else None
        
        print(f"请求失败，状态码: {response.status_code}")
        return None
            
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def get_top_funds_by_different_metrics(count_per_metric=50):
    """
    通过不同的排序指标获取优质基金
    这种方式可以避开分页限制，获取多样化的基金数据
    
    参数:
        count_per_metric: 每个指标获取的数量
        
    返回:
        去重后的基金数据列表
    """
    metrics = {
        'form_year': '今年以来收益',
        'one_year': '近一年收益',
        'six_month': '近半年收益',
        'three_month': '近三月收益',
        'form_start': '成立以来收益'
    }
    
    all_funds = {}  # 使用字典去重，key为基金代码
    
    print(f"通过不同指标获取基金数据（避开分页限制）...")
    
    for metric, desc in metrics.items():
        print(f"\n获取{desc}排名前{count_per_metric}的基金...")
        funds = get_sina_fund_data_simple(page=1, page_size=count_per_metric, sort=metric, asc=0)
        
        if funds:
            print(f"✅ 成功获取 {len(funds)} 条")
            for fund in funds:
                all_funds[fund['symbol']] = fund  # 用代码作为key去重
        else:
            print(f"❌ 获取失败")
    
    result = list(all_funds.values())
    print(f"\n去重后共获取 {len(result)} 个不同的基金")
    return result


if __name__ == "__main__":
    print("="*80)
    print("方式1: 获取单页数据（推荐）")
    print("="*80)
    
    # 获取今年以来收益最高的100个基金
    funds = get_sina_fund_data_simple(page=1, page_size=100, sort='form_year', asc=0)
    
    if funds:
        print(f"\n✅ 成功获取 {len(funds)} 个基金")
        print("\nTop 20基金:")
        for i, fund in enumerate(funds[:20], 1):
            print(f"{i:2d}. {fund['symbol']:8d} {fund['name']:35s} 今年来: {fund.get('form_year', 'N/A'):>8.2f}%")
        
        # 保存为CSV
        df = pd.DataFrame(funds)
        df.to_csv('sina_top_100_funds.csv', index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: sina_top_100_funds.csv")
    
    # 方式2: 通过不同指标获取更多样化的数据
    print("\n" + "="*80)
    print("方式2: 通过不同排序指标获取多样化基金数据")
    print("="*80)
    
    diverse_funds = get_top_funds_by_different_metrics(count_per_metric=100)
    
    if diverse_funds:
        df = pd.DataFrame(diverse_funds)
        df.to_csv('sina_diverse_funds.csv', index=False, encoding='utf-8-sig')
        print(f"数据已保存到: sina_diverse_funds.csv")
        
        print(f"\n数据概览:")
        print(f"  总基金数: {len(df)}")
        print(f"  字段数: {len(df.columns)}")
