"""
调试脚本 3 - 使用更准确的选择器
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager


async def test_better_selectors(symbol='000001'):
    """测试改进的选择器"""

    print(f"正在测试基金 {symbol} 的数据提取...")

    browser_manager = BrowserManager(headless=True)

    try:
        await browser_manager.start()
        page = await browser_manager.new_page()

        url = f"https://fund.eastmoney.com/{symbol}.html"
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)

        # 先获取完整的 dataOfFund 文本看看结构
        data_of_fund_text = await page.evaluate("""
            () => {
                const dataOfFund = document.querySelector('.dataOfFund');
                return dataOfFund ? dataOfFund.textContent : '';
            }
        """)

        print("\n=== dataOfFund 完整文本 ===")
        print(data_of_fund_text[:300])

        # 获取 infoOfFund 完整文本
        info_of_fund_text = await page.evaluate("""
            () => {
                const infoOfFund = document.querySelector('.infoOfFund');
                return infoOfFund ? infoOfFund.textContent : '';
            }
        """)

        print("\n=== infoOfFund 完整文本 ===")
        print(info_of_fund_text[:500])

        # 测试新的提取方法
        data = await page.evaluate("""
            () => {
                const getText = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? el.textContent.trim() : '';
                };

                // 基金名称
                const fundName = getText('.fundDetail-tit');

                // 从 dataOfFund 文本中提取
                const dataOfFundText = getText('.dataOfFund');

                // 提取净值日期 - 从文本中匹配
                let navDate = '';
                const dateMatch = dataOfFundText.match(/\\((\\d{4}-\\d{2}-\\d{2})\\)/);
                if (dateMatch) {
                    navDate = dateMatch[1];
                }

                // 提取净值和增长率
                let perNav = '', totalNav = '', navRate = '';
                const navMatch = dataOfFundText.match(/单位净值[^\\d]*([\\d.]+)([\\-\\+]?[\\d.]+)%/);
                if (navMatch) {
                    perNav = navMatch[1];
                    navRate = navMatch[2];
                }
                const totalNavMatch = dataOfFundText.match(/累计净值([\\d.]+)/);
                if (totalNavMatch) {
                    totalNav = totalNavMatch[1];
                }

                // 从 infoOfFund 文本中提取
                const infoOfFundText = getText('.infoOfFund');

                // 提取基金经理 - 从文本中匹配
                let fundManager = '';
                const managerMatch = infoOfFundText.match(/基金经理[：:](.*?)成 立 日/);
                if (managerMatch) {
                    fundManager = managerMatch[1].trim();
                }

                // 提取基金类型
                let fundType = '';
                const typeMatch = infoOfFundText.match(/类型[：:](.*?)\\|/);
                if (typeMatch) {
                    fundType = typeMatch[1].trim();
                }

                // 提取基金规模
                let fundScale = '';
                const scaleMatch = infoOfFundText.match(/规模[：:](.*?)\\(/);
                if (scaleMatch) {
                    fundScale = scaleMatch[1].trim();
                }

                // 提取成立日期
                let establishDate = '';
                const estMatch = infoOfFundText.match(/成 立 日[：:](\\d{4}-\\d{2}-\\d{2})/);
                if (estMatch) {
                    establishDate = estMatch[1];
                }

                // 提取管理人
                let fundCompany = '';
                const companyMatch = infoOfFundText.match(/管 理 人[：:](.*?)基金评级/);
                if (companyMatch) {
                    fundCompany = companyMatch[1].trim();
                }

                // 申购状态 - 保持原有逻辑
                let sgStates = '开放';
                const stateEl = document.querySelector('.fundInfoItem .staticCell');
                if (stateEl) {
                    sgStates = stateEl.textContent.includes('暂停') ? '暂停申购' : '开放';
                }

                return {
                    sname: fundName,
                    per_nav: perNav,
                    total_nav: totalNav,
                    nav_rate: navRate,
                    nav_date: navDate,
                    fund_manager: fundManager,
                    jjlx: fundType,
                    fund_company: fundCompany,
                    establishment_date: establishDate,
                    fund_scale: fundScale,
                    sg_states: sgStates
                };
            }
        """)

        print("\n=== 提取结果 ===")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        # 测试字段计算
        if data['per_nav'] and data['nav_rate']:
            try:
                per_nav = float(data['per_nav'])
                nav_rate = float(data['nav_rate'])
                yesterday_nav = per_nav / (1 + nav_rate / 100)
                nav_a = per_nav - yesterday_nav

                print(f"\n=== 计算字段 ===")
                print(f"yesterday_nav: {round(yesterday_nav, 4)}")
                print(f"nav_a: {round(nav_a, 4)}")
            except Exception as e:
                print(f"计算失败: {e}")

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "000001"
    asyncio.run(test_better_selectors(symbol))
