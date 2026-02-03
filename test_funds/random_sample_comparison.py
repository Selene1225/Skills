"""
随机抽样对比天天基金和新浪财经数据
策略：
1. 从天天基金网获取所有基金数据
2. 随机抽取10页，每页20个基金
3. 从新浪获取这些基金的数据
4. 对比验证数据一致性
"""

import requests
import json
import re
import random
import time

def get_all_eastmoney_funds():
    """从天天基金网获取所有基金数据"""
    print("正在从天天基金网获取所有基金数据...")
    
    url = "http://fund.eastmoney.com/data/rankhandler.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'http://fund.eastmoney.com/'
    }
    
    all_funds = []
    page = 1
    
    while True:
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
            'pi': str(page),
            'pn': '500',
            'dx': '1'
        }
        
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code != 200 or 'var rankData' not in r.text:
                break
            
            start = r.text.find('[')
            end = r.text.rfind(']') + 1
            data_str = r.text[start:end]
            data_list = json.loads(data_str)
            
            if not data_list:
                break
            
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
                        'sg_states': parts[23] if len(parts) > 23 else '',
                    }
                    all_funds.append(fund)
            
            print(f"  第{page}页: 获取{len(data_list)}个基金，累计{len(all_funds)}个")
            
            if len(data_list) < 500:
                break
            
            page += 1
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            print(f"  获取第{page}页失败: {e}")
            break
    
    print(f"✅ 天天基金网数据获取完成，共{len(all_funds)}只基金\n")
    return all_funds

def get_sina_fund_batch(fund_codes):
    """从新浪财经批量获取基金数据"""
    url = 'https://vip.stock.finance.sina.com.cn/fund_center/data/jsonp.php/IO.XSRV2.CallbackList/NetValueReturn_Service.NetValueReturnOpen'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://vip.stock.finance.sina.com.cn/fund_center/index.html'
    }
    
    result = {}
    
    for code in fund_codes:
        params = {
            'page': 1,
            'num': 1,
            'sort': 'form_year',
            'asc': 0,
            'ccode': code,
            'type2': '0',
            'type3': ''
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                text = response.text
                match = re.search(r'\((.*)\)', text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    
                    if 'data' in data and len(data['data']) > 0:
                        item = data['data'][0]
                        result[code] = {
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
            
            time.sleep(random.uniform(0.3, 0.8))  # 避免请求过快
            
        except Exception as e:
            print(f"    {code}: 获取失败 ({e})")
            continue
    
    return result

def compare_funds(em_fund, sina_fund):
    """对比两个数据源的基金数据"""
    differences = []
    
    # 对比字段
    fields = [
        ('基金名称', 'sname'),
        ('单位净值', 'per_nav'),
        ('累计净值', 'total_nav'),
        ('日增长率', 'nav_rate'),
    ]
    
    for field_name, key in fields:
        em_val = em_fund.get(key, '')
        sina_val = sina_fund.get(key, '')
        
        try:
            em_num = float(em_val) if em_val else 0
            sina_num = float(sina_val) if sina_val else 0
            if abs(em_num - sina_num) >= 0.01:
                differences.append({
                    'field': field_name,
                    'em_val': em_val,
                    'sina_val': sina_val,
                    'diff': abs(em_num - sina_num)
                })
        except:
            if str(em_val) != str(sina_val):
                differences.append({
                    'field': field_name,
                    'em_val': em_val,
                    'sina_val': sina_val,
                    'diff': 'N/A'
                })
    
    return differences

def main():
    print("="*120)
    print("随机抽样对比：天天基金网 vs 新浪财经")
    print("="*120)
    print()
    
    # 1. 获取天天基金所有数据
    em_funds = get_all_eastmoney_funds()
    
    if not em_funds:
        print("❌ 无法获取天天基金数据，退出")
        return
    
    # 2. 创建基金代码索引
    em_funds_dict = {f['symbol']: f for f in em_funds}
    
    # 3. 随机抽样
    samples_per_batch = 20
    num_batches = 10
    
    print(f"随机抽样策略: {num_batches}批次，每批{samples_per_batch}个基金")
    print()
    
    # 随机选择基金
    total_samples = min(samples_per_batch * num_batches, len(em_funds))
    sampled_funds = random.sample(em_funds, total_samples)
    
    # 分批处理
    all_match_count = 0
    all_diff_count = 0
    sina_success_count = 0
    sina_fail_count = 0
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * samples_per_batch
        end_idx = start_idx + samples_per_batch
        batch = sampled_funds[start_idx:end_idx]
        
        print("="*120)
        print(f"【批次 {batch_idx + 1}/{num_batches}】抽样对比")
        print("="*120)
        
        # 获取这批基金的代码
        codes = [f['symbol'] for f in batch]
        print(f"抽样基金代码: {', '.join(codes[:5])}{'...' if len(codes) > 5 else ''}")
        print()
        
        # 从新浪获取数据
        print("正在从新浪财经获取数据...")
        sina_funds = get_sina_fund_batch(codes)
        
        sina_success = len(sina_funds)
        sina_fail = len(codes) - sina_success
        sina_success_count += sina_success
        sina_fail_count += sina_fail
        
        print(f"  新浪数据: ✅ 成功{sina_success}个, ❌ 失败{sina_fail}个")
        print()
        
        if not sina_funds:
            print("  ⚠️ 新浪财经无数据返回，可能仍被限制")
            print()
            continue
        
        # 对比数据
        print("数据对比:")
        batch_match = 0
        batch_diff = 0
        
        for code in codes:
            if code not in sina_funds:
                continue
            
            em_fund = em_funds_dict[code]
            sina_fund = sina_funds[code]
            
            diffs = compare_funds(em_fund, sina_fund)
            
            if not diffs:
                batch_match += 1
                all_match_count += 1
                print(f"  ✅ {code} {em_fund['sname'][:15]:15s} - 数据完全一致")
            else:
                batch_diff += 1
                all_diff_count += 1
                print(f"  ❌ {code} {em_fund['sname'][:15]:15s} - 发现差异:")
                for diff in diffs:
                    print(f"      {diff['field']:10s}: 天天={diff['em_val']:10s} | 新浪={diff['sina_val']:10s} | 差异={diff['diff']}")
        
        print()
        print(f"批次总结: ✅ 一致{batch_match}个, ❌ 差异{batch_diff}个")
        print()
        
        # 避免请求过快
        if batch_idx < num_batches - 1:
            wait_time = random.uniform(5, 10)
            print(f"等待{wait_time:.1f}秒后继续下一批次...")
            time.sleep(wait_time)
            print()
    
    # 最终统计
    print("="*120)
    print("最终统计")
    print("="*120)
    print(f"天天基金网: 共获取 {len(em_funds)} 只基金")
    print(f"抽样数量: {total_samples} 只基金 ({num_batches}批次 × {samples_per_batch}个/批次)")
    print(f"新浪财经: ✅ 成功获取 {sina_success_count} 只, ❌ 失败 {sina_fail_count} 只")
    print()
    
    if sina_success_count > 0:
        print(f"数据对比结果:")
        print(f"  ✅ 完全一致: {all_match_count} 只 ({all_match_count/sina_success_count*100:.1f}%)")
        print(f"  ❌ 存在差异: {all_diff_count} 只 ({all_diff_count/sina_success_count*100:.1f}%)")
        print()
        
        if all_match_count / sina_success_count > 0.95:
            print("✅ 结论: 两个数据源数据高度一致，都可以使用")
        elif all_match_count / sina_success_count > 0.80:
            print("⚠️ 结论: 两个数据源大部分一致，存在少量差异")
        else:
            print("❌ 结论: 两个数据源差异较大，需要进一步分析")
    else:
        print("❌ 无法从新浪获取数据进行对比")
        print("可能原因: IP被限制，建议等待后重试")

if __name__ == "__main__":
    main()
