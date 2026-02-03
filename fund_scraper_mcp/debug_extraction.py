"""
调试脚本 2 - 在浏览器中执行JavaScript查看实际能提取的数据
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


async def debug_extraction(symbol='000001'):
    """测试 JavaScript 提取数据"""

    print(f"正在测试基金 {symbol} 的数据提取...")

    browser_manager = BrowserManager(headless=True)

    try:
        await browser_manager.start()
        page = await browser_manager.new_page()

        url = f"https://fund.eastmoney.com/{symbol}.html"
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)

        # 执行当前的提取逻辑
        data = await page.evaluate("""
            () => {
                const getText = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? el.textContent.trim() : '';
                };

                // 基本信息
                const fundName = getText('.fundDetail-tit');

                // 净值数据 - 详细调试
                const dataItems = document.querySelectorAll('.dataOfFund .dataNums');
                console.log('dataItems 数量:', dataItems.length);

                let perNav = '', totalNav = '', navRate = '', navDate = '';

                if (dataItems.length >= 2) {
                    const firstDataItem = dataItems[0];
                    const secondDataItem = dataItems[1];

                    console.log('第一个 dataNums:', firstDataItem?.innerHTML);
                    console.log('第二个 dataNums:', secondDataItem?.innerHTML);

                    perNav = firstDataItem?.querySelector('span:first-child')?.textContent?.trim() || '';
                    totalNav = secondDataItem?.querySelector('span:first-child')?.textContent?.trim() || '';
                }

                // 日增长率
                const rateEl = document.querySelector('.dataOfFund .dataNums .fund-form-rate');
                if (rateEl) {
                    navRate = rateEl.textContent.trim().replace('%', '');
                }

                // 净值日期
                const dateEl = document.querySelector('.dataOfFund .dataNums .fundInfoItem');
                if (dateEl) {
                    const match = dateEl.textContent.match(/\\d{4}-\\d{2}-\\d{2}/);
                    if (match) navDate = match[0];
                }

                // 基金经理
                const managerLinks = document.querySelectorAll('.infoOfFund td a[href*="manager"]');
                const managers = Array.from(managerLinks).map(a => a.textContent.trim()).join(' ');

                // 基金信息表
                const infoItems = document.querySelectorAll('.infoOfFund td');
                let fundType = '', fundCompany = '', establishDate = '', fundScale = '';

                console.log('infoItems 数量:', infoItems.length);

                infoItems.forEach((td, i) => {
                    const text = td.textContent;
                    if (text.includes('基金类型') || text.includes('类型')) {
                        console.log('找到基金类型 td:', text);
                        fundType = td.querySelector('a')?.textContent?.trim() || '';
                    }
                    if (text.includes('基金规模') || text.includes('规模')) {
                        console.log('找到规模 td:', text);
                        const match = text.match(/[\\d.]+亿元/);
                        if (match) fundScale = match[0];
                    }
                    if (text.includes('成立日') || text.includes('成 立 日')) {
                        console.log('找到成立日 td:', text);
                        const match = text.match(/\\d{4}-\\d{2}-\\d{2}/);
                        if (match) establishDate = match[0];
                    }
                    if (text.includes('管理人') || text.includes('管 理 人')) {
                        console.log('找到管理人 td:', text);
                        fundCompany = td.querySelector('a')?.textContent?.trim() || '';
                    }
                });

                // 申购状态
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
                    fund_manager: managers,
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

    finally:
        await browser_manager.close()


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "000001"
    asyncio.run(debug_extraction(symbol))
