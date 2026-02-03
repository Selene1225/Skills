"""
Fund Scraper MCP Server 功能测试
直接测试爬虫功能，不通过 MCP 协议
"""
import asyncio
import sys
import os

# 添加项目目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager
from scrapers.eastmoney_scraper import EastmoneyScraper


async def test_all_fund_codes(scraper):
    """测试获取全量基金代码"""
    print("=" * 60)
    print("测试 1: 获取全量基金代码列表")
    print("=" * 60)
    
    result = await scraper.scrape_all_fund_codes()
    
    if result['success']:
        print(f"✅ 成功! 共获取 {result['total_count']} 只基金")
        print(f"\n前5个基金:")
        for fund in result['data'][:5]:
            print(f"  {fund['symbol']} - {fund['sname']} ({fund['jjlx']})")
    else:
        print(f"❌ 失败: {result['error']}")
    
    return result['success']


async def test_fund_detail(scraper):
    """测试获取单个基金详情"""
    print("\n" + "=" * 60)
    print("测试 2: 获取单个基金详情 (000001)")
    print("=" * 60)
    
    result = await scraper.scrape_detail("000001")
    
    if result['success']:
        data = result['data']
        print(f"✅ 成功!")
        print(f"\n基金详情:")
        print(f"  代码: {data.get('symbol')}")
        print(f"  名称: {data.get('sname')}")
        print(f"  单位净值: {data.get('per_nav')}")
        print(f"  累计净值: {data.get('total_nav')}")
        print(f"  前一日净值: {data.get('yesterday_nav')}")
        print(f"  日增长率: {data.get('nav_rate')}%")
        print(f"  涨跌额: {data.get('nav_a')}")
        print(f"  净值日期: {data.get('nav_date')}")
        print(f"  基金经理: {data.get('fund_manager')}")
        print(f"  基金类型: {data.get('jjlx')}")
        print(f"  基金规模: {data.get('fund_scale')}")
        print(f"  申购状态: {data.get('sg_states')}")
    else:
        print(f"❌ 失败: {result['error']}")
    
    return result['success']


async def test_fund_list(scraper):
    """测试获取基金排行榜"""
    print("\n" + "=" * 60)
    print("测试 3: 获取基金排行榜 (前10个)")
    print("=" * 60)
    
    result = await scraper.scrape_list(fund_type="all", page=1, page_size=10)
    
    if result['success']:
        print(f"✅ 成功! 共 {result['total_count']} 只基金")
        print(f"\n前10个基金:")
        for fund in result['data']:
            print(f"  {fund['symbol']} - {fund['sname'][:15]:15s} 净值:{fund['per_nav']:8s} 日增长:{fund['nav_rate']:8s}%")
    else:
        print(f"❌ 失败: {result['error']}")
    
    return result['success']


async def test_nav_history(scraper):
    """测试获取净值历史"""
    print("\n" + "=" * 60)
    print("测试 4: 获取净值历史 (000001, 最近10条)")
    print("=" * 60)
    
    result = await scraper.scrape_nav_history("000001", limit=10)
    
    if result['success']:
        print(f"✅ 成功! 共 {result['total_count']} 条记录")
        print(f"\n净值历史:")
        for item in result['data']:
            print(f"  {item['date']} - 净值:{item['nav']:8s} 累计:{item['total_nav']:8s} 增长率:{item['rate']:8s}%")
    else:
        print(f"❌ 失败: {result['error']}")
    
    return result['success']


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Fund Scraper MCP Server 功能测试")
    print("=" * 60)
    
    results = {}
    
    # 创建共享的浏览器管理器和爬虫
    bm = BrowserManager(headless=True)
    await bm.start()
    scraper = EastmoneyScraper(bm)
    
    try:
        # 测试 1: 全量基金代码
        results['all_codes'] = await test_all_fund_codes(scraper)
        
        # 测试 2: 基金详情
        results['detail'] = await test_fund_detail(scraper)
        
        # 测试 3: 基金排行榜
        results['list'] = await test_fund_list(scraper)
        
        # 测试 4: 净值历史
        results['nav_history'] = await test_nav_history(scraper)
    finally:
        await bm.close()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
