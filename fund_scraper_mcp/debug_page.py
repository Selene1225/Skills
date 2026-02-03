"""
调试脚本 - 查看基金详情页面的实际 HTML 结构
"""
import asyncio
import sys
import os

# 设置 UTF-8 编码（Windows 控制台兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager


async def debug_fund_page(symbol='000001'):
    """查看基金页面的HTML结构"""

    print(f"正在访问基金 {symbol} 的详情页...")

    browser_manager = BrowserManager(headless=False)  # 显示浏览器以便查看

    try:
        await browser_manager.start()
        page = await browser_manager.new_page()

        url = f"https://fund.eastmoney.com/{symbol}.html"
        print(f"URL: {url}")

        await page.goto(url, wait_until="networkidle", timeout=60000)

        # 等待页面加载
        await asyncio.sleep(3)

        # 截屏
        await page.screenshot(path=f"debug_{symbol}.png")
        print(f"截图保存为 debug_{symbol}.png")

        # 获取页面内容
        html = await page.content()
        with open(f"debug_{symbol}.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML保存为 debug_{symbol}.html")

        # 尝试提取关键信息
        print("\n=== 尝试提取数据 ===")

        # 测试不同的选择器
        selectors_to_test = [
            (".fundDetail-tit", "基金名称"),
            (".dataOfFund", "数据区域"),
            (".dataNums", "净值数字"),
            (".infoOfFund", "基金信息表"),
            ("table.info", "信息表格"),
            ("#gz_gsz", "估算值"),
        ]

        for selector, name in selectors_to_test:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    print(f"✅ {name} ({selector}): {text[:100] if text else '(空)'}")
                else:
                    print(f"❌ {name} ({selector}): 未找到")
            except Exception as e:
                print(f"❌ {name} ({selector}): 错误 - {e}")

        # 等待一下以便查看
        print("\n浏览器将在10秒后关闭...")
        await asyncio.sleep(10)

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "000001"
    asyncio.run(debug_fund_page(symbol))
