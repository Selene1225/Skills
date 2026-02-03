"""
测试 fetch_all_funds_info - 获取前20个基金
"""
import asyncio
import json
import sys
import os

# 设置 UTF-8 编码（Windows 控制台兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager
from scrapers.eastmoney_scraper import EastmoneyScraper


async def test_fetch_20_funds():
    """测试获取前20个基金"""

    print("=" * 60)
    print("测试 fetch_all_funds_info - 获取前20个基金")
    print("=" * 60)

    browser_manager = BrowserManager(headless=True)

    try:
        await browser_manager.start()
        scraper = EastmoneyScraper(browser_manager)

        # 获取前20个基金
        result = await scraper.fetch_all_funds_info(
            batch_size=20,
            max_funds=20,
            delay=1.0
        )

        if result['success']:
            print(f"\n✅ 成功获取 {result['total_count']} 个基金数据")
            print(f"失败: {result.get('failed_count', 0)} 个")

            # 验证字段
            required_fields = [
                'symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav',
                'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager',
                'jjlx', 'jjzfe'
            ]

            if result['data']:
                print(f"\n前5个基金的概况:")
                for i, fund in enumerate(result['data'][:5], 1):
                    print(f"{i}. {fund.get('symbol')} - {fund.get('sname')[:20]}... - "
                          f"净值: {fund.get('per_nav')} - 涨跌: {fund.get('nav_rate')}%")

                # 保存为 JSON 文件
                output_file = "test_20_funds.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 数据已保存到: {output_file}")

                # 检查所有基金是否都有完整字段
                incomplete_funds = []
                for fund in result['data']:
                    missing = [f for f in required_fields if not fund.get(f)]
                    if missing:
                        incomplete_funds.append((fund.get('symbol'), missing))

                if incomplete_funds:
                    print(f"\n⚠️ 发现 {len(incomplete_funds)} 个基金数据不完整:")
                    for symbol, missing in incomplete_funds[:5]:
                        print(f"  - {symbol}: 缺少 {missing}")
                else:
                    print(f"\n✅ 所有 {len(result['data'])} 个基金数据完整!")

        else:
            print(f"\n❌ 失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(test_fetch_20_funds())
