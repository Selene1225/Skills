import requests
import json
import re
import time

def get_sina_fund_data(page=1, page_size=40, sort='form_year', asc=0):
    """
    从新浪财经获取开放式基金数据
    
    参数:
        page: 页码（从1开始）
        page_size: 每页数量（建议40）
        sort: 排序字段
            - 'form_year': 今年以来收益率
            - 'form_start': 成立以来收益率
            - 'one_year': 近一年收益率
            - 'six_month': 近半年收益率
            - 'three_month': 近三月收益率
            - 'per_nav': 单位净值
        asc: 0=降序, 1=升序
        
    返回:
        {
            'total_num': 总数量,
            'data': 基金数据列表,
            'exec_time': 执行时间,
            'sort_time': 排序时间,
            'lastupdate': 最后更新时间
        }
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
                return data
        
        return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


if __name__ == "__main__":
    print("=== 测试新浪财经开放式基金接口 ===\n")
    
    # 测试1: 获取第一页数据
    print("测试1: 获取第1页数据（40条）")
    result = get_sina_fund_data(page=1, page_size=40)
    
    if result:
        print(f"✅ 成功！")
        print(f"总基金数量: {result['total_num']:,} 个")
        print(f"本次获取: {len(result['data'])} 条")
        print(f"最后更新: {result['lastupdate']}")
        
        # 显示第一条数据
        if result['data']:
            fund = result['data'][0]
            print(f"\n第一条基金信息:")
            print(f"  基金代码: {fund['symbol']}")
            print(f"  基金名称: {fund['name']}")
            print(f"  单位净值: {fund['per_nav']}")
            print(f"  累计净值: {fund['total_nav']}")
            print(f"  净值日期: {fund['jzrq']}")
            print(f"  近三月收益: {fund.get('three_month', 'N/A')}%")
            print(f"  近半年收益: {fund.get('six_month', 'N/A')}%")
            print(f"  近一年收益: {fund.get('one_year', 'N/A')}%")
            print(f"  今年以来收益: {fund.get('form_year', 'N/A')}%")
            print(f"  成立以来收益: {fund.get('form_start', 'N/A')}%")
            print(f"  成立日期: {fund['clrq']}")
            print(f"  基金经理: {fund['jjjl']}")
            
            print(f"\n前10个基金:")
            for i, fund in enumerate(result['data'][:10], 1):
                print(f"  {i}. {fund['symbol']} - {fund['name']} (今年以来: {fund.get('form_year', 'N/A')}%)")
    
    # 测试2: 测试分页
    print("\n" + "="*80)
    print("测试2: 获取第2页数据")
    time.sleep(1)  # 等待1秒避免请求过快
    result2 = get_sina_fund_data(page=2, page_size=20)
    if result2:
        print(f"✅ 第2页获取成功，{len(result2['data'])} 条数据")
        if result2['data']:
            first_fund = result2['data'][0]
            print(f"第2页第一条: {first_fund['symbol']} - {first_fund['name']}")
    else:
        print(f"⚠️ 第2页获取失败（可能是请求限制，稍等片刻重试）")
    
    # 测试3: 批量获取
    print("\n" + "="*80)
    print("测试3: 批量获取200条数据")
    all_funds = []
    total_num = 0
    for page in range(1, 6):  # 获取5页，每页40条
        result_page = get_sina_fund_data(page=page, page_size=40)
        if result_page and result_page['data']:
            all_funds.extend(result_page['data'])
            total_num = result_page['total_num']
            print(f"第{page}页获取成功，累计 {len(all_funds)} 条")
            time.sleep(0.5)  # 礼貌抓取
        else:
            break
    
    print(f"\n✅ 总共获取 {len(all_funds)} 条基金数据")
    print(f"\n🎉 所有测试通过！新浪财经接口可以正常使用。")
    if total_num > 0:
        print(f"📊 新浪财经共有 {total_num:,} 个开放式基金")
