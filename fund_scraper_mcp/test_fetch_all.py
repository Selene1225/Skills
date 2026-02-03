"""
测试 fetch_all_funds_info 功能
验证返回的12个字段是否符合要求
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


async def test_fetch_all_funds_info():
    """测试获取所有基金信息（只获取前5个）"""

    print("=" * 60)
    print("测试 fetch_all_funds_info - 获取前5个基金")
    print("=" * 60)

    browser_manager = BrowserManager(headless=True)

    try:
        await browser_manager.start()
        scraper = EastmoneyScraper(browser_manager)

        # 只获取前5个基金进行测试
        result = await scraper.fetch_all_funds_info(
            batch_size=5,
            max_funds=5,
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

            print(f"\n要求的12个字段: {required_fields}")

            if result['data']:
                first_fund = result['data'][0]
                print(f"\n第一个基金的数据:")
                print(json.dumps(first_fund, ensure_ascii=False, indent=2))

                # 检查字段
                missing_fields = [f for f in required_fields if f not in first_fund]
                extra_fields = [f for f in first_fund.keys() if f not in required_fields]

                if missing_fields:
                    print(f"\n❌ 缺少字段: {missing_fields}")
                else:
                    print(f"\n✅ 所有必需字段都存在")

                if extra_fields:
                    print(f"⚠️ 额外字段: {extra_fields}")

                # 验证计算字段
                print("\n验证计算字段的正确性:")
                per_nav = first_fund.get('per_nav', '')
                nav_rate = first_fund.get('nav_rate', '')
                yesterday_nav = first_fund.get('yesterday_nav', '')
                nav_a = first_fund.get('nav_a', '')

                if per_nav and nav_rate and yesterday_nav and nav_a:
                    try:
                        per_nav_f = float(per_nav)
                        nav_rate_f = float(nav_rate)
                        yesterday_nav_f = float(yesterday_nav)
                        nav_a_f = float(nav_a)

                        # 验证: per_nav = yesterday_nav * (1 + nav_rate/100)
                        expected_per_nav = yesterday_nav_f * (1 + nav_rate_f / 100)
                        # 验证: nav_a = per_nav - yesterday_nav
                        expected_nav_a = per_nav_f - yesterday_nav_f

                        print(f"  单位净值 (per_nav): {per_nav}")
                        print(f"  前一日净值 (yesterday_nav): {yesterday_nav}")
                        print(f"  增长率 (nav_rate): {nav_rate}%")
                        print(f"  涨跌额 (nav_a): {nav_a}")

                        if abs(expected_per_nav - per_nav_f) < 0.01:
                            print(f"  ✅ 前一日净值计算正确")
                        else:
                            print(f"  ❌ 前一日净值计算有误，期望: {expected_per_nav:.4f}")

                        if abs(expected_nav_a - nav_a_f) < 0.01:
                            print(f"  ✅ 涨跌额计算正确")
                        else:
                            print(f"  ❌ 涨跌额计算有误，期望: {expected_nav_a:.4f}")
                    except Exception as e:
                        print(f"  ⚠️ 无法验证计算字段: {e}")

                # 显示所有基金的概况
                print(f"\n所有 {len(result['data'])} 个基金的概况:")
                for i, fund in enumerate(result['data'], 1):
                    print(f"{i}. {fund.get('symbol')} - {fund.get('sname')} - "
                          f"净值: {fund.get('per_nav')} - 涨跌: {fund.get('nav_rate')}%")

            # 显示完整结果（供参考）
            print(f"\n完整结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n❌ 失败: {result.get('error', '未知错误')}")

    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    asyncio.run(test_fetch_all_funds_info())
