"""
验证和修复 data_from_sina.json 中的数据
对比新浪、天天基金和akshare三个数据源
"""

import json
import requests
import akshare as ak
import random

def load_sina_data():
    """加载新浪数据文件"""
    with open('../data_from_sina.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['data']

def get_eastmoney_fund(code):
    """从天天基金网获取单个基金数据"""
    url = "http://fund.eastmoney.com/data/rankhandler.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'http://fund.eastmoney.com/'
    }
    
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
    
    try:
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
                    }
    except:
        pass
    return None

def get_akshare_fund(code):
    """从akshare获取单个基金数据"""
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
            }
    except:
        pass
    return None

def compare_values(val1, val2, tolerance=0.01):
    """比较两个值"""
    try:
        num1 = float(val1) if val1 else 0
        num2 = float(val2) if val2 else 0
        return abs(num1 - num2) < tolerance
    except:
        return str(val1) == str(val2)

def main():
    print("="*120)
    print("验证 data_from_sina.json 数据准确性")
    print("="*120)
    print()
    
    # 加载新浪数据
    print("正在加载 data_from_sina.json...")
    sina_funds = load_sina_data()
    print(f"✅ 加载完成，共 {len(sina_funds)} 只基金")
    print()
    
    # 随机抽样验证
    sample_size = min(50, len(sina_funds))
    samples = random.sample(sina_funds, sample_size)
    
    print(f"随机抽取 {sample_size} 个样本进行验证")
    print()
    
    results = {
        'total': 0,
        'em_match': 0,
        'em_diff': 0,
        'em_notfound': 0,
        'ak_match': 0,
        'ak_diff': 0,
        'ak_notfound': 0,
        'errors': []
    }
    
    for i, sina_fund in enumerate(samples, 1):
        code = sina_fund['symbol']
        print(f"[{i}/{sample_size}] 验证 {code} {sina_fund['sname'][:20]}")
        
        results['total'] += 1
        
        # 与天天基金对比
        em_fund = get_eastmoney_fund(code)
        if em_fund:
            fields_match = (
                compare_values(sina_fund['per_nav'], em_fund['per_nav']) and
                compare_values(sina_fund['total_nav'], em_fund['total_nav']) and
                compare_values(sina_fund['nav_rate'], em_fund['nav_rate'])
            )
            
            if fields_match:
                results['em_match'] += 1
                print(f"  ✅ 天天基金: 数据一致")
            else:
                results['em_diff'] += 1
                print(f"  ❌ 天天基金: 数据不一致")
                print(f"      单位净值: 新浪={sina_fund['per_nav']:10s} | 天天={em_fund['per_nav']:10s}")
                print(f"      累计净值: 新浪={sina_fund['total_nav']:10s} | 天天={em_fund['total_nav']:10s}")
                print(f"      日增长率: 新浪={str(sina_fund['nav_rate']):10s} | 天天={em_fund['nav_rate']:10s}")
                
                results['errors'].append({
                    'code': code,
                    'name': sina_fund['sname'],
                    'issue': '与天天基金数据不一致',
                    'sina_nav': sina_fund['per_nav'],
                    'em_nav': em_fund['per_nav'],
                    'sina_rate': sina_fund['nav_rate'],
                    'em_rate': em_fund['nav_rate']
                })
        else:
            results['em_notfound'] += 1
            print(f"  ⚠️ 天天基金: 未找到数据")
        
        # 与akshare对比
        ak_fund = get_akshare_fund(code)
        if ak_fund:
            fields_match = (
                compare_values(sina_fund['per_nav'], ak_fund['per_nav']) and
                compare_values(sina_fund['total_nav'], ak_fund['total_nav']) and
                compare_values(sina_fund['nav_rate'], ak_fund['nav_rate'])
            )
            
            if fields_match:
                results['ak_match'] += 1
                print(f"  ✅ akshare: 数据一致")
            else:
                results['ak_diff'] += 1
                print(f"  ❌ akshare: 数据不一致")
                print(f"      单位净值: 新浪={sina_fund['per_nav']:10s} | akshare={ak_fund['per_nav']:10s}")
                print(f"      累计净值: 新浪={sina_fund['total_nav']:10s} | akshare={ak_fund['total_nav']:10s}")
                print(f"      日增长率: 新浪={str(sina_fund['nav_rate']):10s} | akshare={ak_fund['nav_rate']:10s}")
        else:
            results['ak_notfound'] += 1
            print(f"  ⚠️ akshare: 未找到数据")
        
        print()
    
    # 统计报告
    print("="*120)
    print("验证统计报告")
    print("="*120)
    print(f"验证样本: {results['total']} 只基金")
    print()
    print("与天天基金对比:")
    print(f"  ✅ 数据一致: {results['em_match']} 只 ({results['em_match']/results['total']*100:.1f}%)")
    print(f"  ❌ 数据不一致: {results['em_diff']} 只 ({results['em_diff']/results['total']*100:.1f}%)")
    print(f"  ⚠️ 未找到: {results['em_notfound']} 只 ({results['em_notfound']/results['total']*100:.1f}%)")
    print()
    print("与akshare对比:")
    print(f"  ✅ 数据一致: {results['ak_match']} 只 ({results['ak_match']/results['total']*100:.1f}%)")
    print(f"  ❌ 数据不一致: {results['ak_diff']} 只 ({results['ak_diff']/results['total']*100:.1f}%)")
    print(f"  ⚠️ 未找到: {results['ak_notfound']} 只 ({results['ak_notfound']/results['total']*100:.1f}%)")
    print()
    
    # 数据质量评估
    if results['em_match'] + results['ak_match'] >= results['total'] * 1.5:
        print("✅ 结论: data_from_sina.json 数据质量良好，与其他数据源高度一致")
    elif results['em_diff'] > 0 or results['ak_diff'] > 0:
        print("⚠️ 结论: 发现数据不一致问题")
        print()
        print("问题基金列表:")
        for err in results['errors']:
            print(f"  - {err['code']} {err['name']}: {err['issue']}")
        print()
        print("建议: 可能需要更新 data_from_sina.json 中的数据")
    else:
        print("⚠️ 结论: 部分基金在其他数据源中未找到，可能是新基金或数据源覆盖范围不同")

if __name__ == "__main__":
    main()
