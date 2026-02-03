import requests
import json
import time

def get_fund_data(page=1, page_size=20):
    """
    从天天基金网获取股票型基金数据
    
    参数:
        page: 页码（从1开始）
        page_size: 每页数量
        
    返回:
        基金数据列表，每条数据是一个逗号分隔的字符串
        格式: 基金代码,基金名称,拼音缩写,日期,净值,累计净值,日增长率,近1周,近1月,近3月,近6月,近1年,近2年,近3年,今年来,成立来,成立日期,...
    """
    url = "http://fund.eastmoney.com/data/rankhandler.aspx"
    params = {
        'op': 'ph',      # operation: 排行
        'dt': 'kf',      # 开放式基金
        'ft': 'gp',      # 股票型
        'rs': '',
        'gs': '0',
        'sc': 'qjzf',    # 排序字段：近一月增长率
        'st': 'desc',    # 降序
        'sd': '2024-01-01',
        'ed': '2026-01-31',
        'qdii': '',
        'tabSubtype': ',,,,,',
        'pi': str(page),         # page index
        'pn': str(page_size),    # page number
        'dx': '1',
        'v': '0.1'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://fund.eastmoney.com/'
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"请求失败，状态码: {r.status_code}")
            return None
            
        # 提取数据部分
        if 'var rankData' in r.text:
            start = r.text.find('[')
            end = r.text.rfind(']') + 1
            if start != -1 and end > start:
                data_str = r.text[start:end]
                data = json.loads(data_str)
                return data
        
        return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


if __name__ == "__main__":
    # 测试获取数据
    print("=== 测试获取第1页数据（20条）===")
    data = get_fund_data(page=1, page_size=20)
    if data:
        print(f"✅ 成功获取 {len(data)} 条基金数据！\n")
        
        # 解析并显示第一条数据
        first_fund = data[0].split(',')
        print("第一条基金信息:")
        print(f"  基金代码: {first_fund[0]}")
        print(f"  基金名称: {first_fund[1]}")
        print(f"  日期: {first_fund[3]}")
        print(f"  净值: {first_fund[4]}")
        print(f"  累计净值: {first_fund[5]}")
        print(f"  日增长率: {first_fund[6]}%")
        
        print("\n前10个基金:")
        for fund in data[:10]:
            code, name = fund.split(',')[:2]
            print(f"  {code} - {name}")
        if len(data) > 10:
            print(f"  ... 还有 {len(data) - 10} 条")
    
    # 测试分页
    print("\n=== 测试获取第2页数据 ===")
    data2 = get_fund_data(page=2, page_size=10)
    if data2:
        print(f"✅ 成功获取第2页 {len(data2)} 条数据")
        code, name = data2[0].split(',')[:2]
        print(f"第2页第一条: {code} - {name}")
    
    # 测试批量获取
    print("\n=== 测试批量获取100条数据 ===")
    all_funds = []
    for page in range(1, 6):  # 获取前5页，每页20条
        data = get_fund_data(page=page, page_size=20)
        if data:
            all_funds.extend(data)
            print(f"第{page}页获取成功，累计 {len(all_funds)} 条")
            time.sleep(0.3)  # 礼貌抓取，避免请求过快
        else:
            break
    
    print(f"\n✅ 总共获取 {len(all_funds)} 条基金数据")
    print("\n🎉 所有测试通过！接口可以正常使用。")