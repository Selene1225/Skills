"""
随机抽样对比天天基金和akshare数据
验证两个可用数据源的一致性
"""

import requests
import json
import random
import time
import akshare as ak
import pandas as pd

def get_eastmoney_funds_batch(page_num=1, page_size=500):
    """从天天基金网获取一批基金数据"""
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
        'pi': str(page_num),
        'pn': str(page_size),
        'dx': '1'
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200 or 'var rankData' not in r.text:
            return []
        
        start = r.text.find('[')
        end = r.text.rfind(']') + 1
        data_str = r.text[start:end]
        data_list = json.loads(data_str)
        
        result = []
        for item in data_list:
            parts = item.split(',')
            if len(parts) >= 8:
                fund = {
                    'symbol': parts[0],
                    'sname': parts[1],
                    'nav_date': parts[3],
                    'per_nav': parts[4],
                    'total_nav': parts[5],
                    'nav_rate': parts[6],
                    'week_rate': parts[7],
                    'month_rate': parts[8],
                }
                result.append(fund)
        
        return result
    except Exception as e:
        print(f"获取天天基金数据失败: {e}")
        return []

def get_akshare_fund(code):
    """从akshare获取单个基金数据"""
    try:
        # 从排行榜数据中查找
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
            }
    except Exception as e:
        print(f"  akshare获取{code}失败: {e}")
    
    return None

def compare_values(val1, val2, tolerance=0.01):
    """比较两个值是否一致"""
    try:
        num1 = float(val1) if val1 else 0
        num2 = float(val2) if val2 else 0
        return abs(num1 - num2) < tolerance
    except:
        return str(val1) == str(val2)

def main():
    print("="*120)
    print("随机抽样对比：天天基金网 vs akshare")
    print("="*120)
    print()
    
    # 策略：随机选择10页，每页抽20个基金
    num_pages = 10
    samples_per_page = 20
    
    print(f"抽样策略: 随机选择{num_pages}页，每页抽取{samples_per_page}个基金")
    print()
    
    # 天天基金约有38页（每页500个）
    total_pages = 38
    random_pages = random.sample(range(1, total_pages + 1), num_pages)
    random_pages.sort()
    
    print(f"随机页码: {random_pages}")
    print()
    
    all_match = 0
    all_diff = 0
    all_samples = 0
    
    for page_idx, page_num in enumerate(random_pages, 1):
        print("="*120)
        print(f"【页面 {page_idx}/{num_pages}】第{page_num}页")
        print("="*120)
        
        # 从天天基金获取这一页
        print(f"正在从天天基金获取第{page_num}页数据...")
        em_funds = get_eastmoney_funds_batch(page_num)
        
        if not em_funds:
            print("  ❌ 获取失败，跳过此页")
            print()
            continue
        
        print(f"  ✅ 获取到{len(em_funds)}只基金")
        
        # 随机抽取样本
        sample_size = min(samples_per_page, len(em_funds))
        samples = random.sample(em_funds, sample_size)
        
        print(f"  随机抽取{sample_size}个样本")
        print()
        
        # 对比每个样本
        batch_match = 0
        batch_diff = 0
        
        for fund in samples:
            code = fund['symbol']
            
            # 从akshare获取数据
            ak_fund = get_akshare_fund(code)
            
            if not ak_fund:
                print(f"  ⚠️ {code} {fund['sname'][:15]:15s} - akshare无数据")
                continue
            
            all_samples += 1
            
            # 对比关键字段
            fields_match = (
                compare_values(fund['per_nav'], ak_fund['per_nav']) and
                compare_values(fund['total_nav'], ak_fund['total_nav']) and
                compare_values(fund['nav_rate'], ak_fund['nav_rate'])
            )
            
            if fields_match:
                batch_match += 1
                all_match += 1
                print(f"  ✅ {code} {fund['sname'][:15]:15s} - 数据一致 (净值={fund['per_nav']}, 增长率={fund['nav_rate']}%)")
            else:
                batch_diff += 1
                all_diff += 1
                print(f"  ❌ {code} {fund['sname'][:15]:15s} - 数据差异:")
                print(f"      单位净值: 天天={fund['per_nav']:10s} | akshare={ak_fund['per_nav']:10s}")
                print(f"      累计净值: 天天={fund['total_nav']:10s} | akshare={ak_fund['total_nav']:10s}")
                print(f"      日增长率: 天天={fund['nav_rate']:10s} | akshare={ak_fund['nav_rate']:10s}")
        
        print()
        print(f"本页统计: ✅ 一致{batch_match}个, ❌ 差异{batch_diff}个")
        print()
        
        # 避免akshare请求过快
        if page_idx < num_pages:
            wait_time = random.uniform(2, 4)
            print(f"等待{wait_time:.1f}秒后继续...\n")
            time.sleep(wait_time)
    
    # 最终统计
    print("="*120)
    print("最终统计结果")
    print("="*120)
    print(f"抽样总数: {all_samples} 只基金")
    print(f"数据一致: {all_match} 只 ({all_match/all_samples*100:.1f}%)" if all_samples > 0 else "无有效样本")
    print(f"数据差异: {all_diff} 只 ({all_diff/all_samples*100:.1f}%)" if all_samples > 0 else "")
    print()
    
    if all_samples > 0:
        if all_match / all_samples >= 0.95:
            print("✅ 结论: 天天基金网和akshare数据高度一致，两个数据源都可信赖")
            print("   推荐使用天天基金网（速度快）+ akshare补充字段（基金经理等）")
        elif all_match / all_samples >= 0.80:
            print("⚠️ 结论: 两个数据源大部分一致，存在少量差异")
            print("   建议优先使用天天基金网，必要时用akshare交叉验证")
        else:
            print("❌ 结论: 数据源存在较大差异，需要进一步分析")
            print("   可能原因：数据更新时间不同、统计口径差异等")
    else:
        print("❌ 无有效样本进行对比")

if __name__ == "__main__":
    main()
