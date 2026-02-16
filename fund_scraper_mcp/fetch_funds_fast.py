"""
快速获取基金数据 - 使用天天基金排行榜API
无需浏览器，直接HTTP请求，速度快
"""
import requests
import csv
import time
from datetime import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_all_funds_data(output_file="all_funds_fast.csv"):
    """
    从天天基金排行榜API批量获取所有基金数据
    一次性获取26000+基金，比逐个爬取快100倍
    """
    print("=" * 70)
    print("快速获取所有基金数据（约26000+个）")
    print("使用天天基金排行榜API，无需浏览器")
    print("=" * 70)

    # API endpoint
    base_url = "http://fund.eastmoney.com/data/rankhandler.aspx"

    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://fund.eastmoney.com/data/fundranking.html'
    }

    # 第一次请求，获取总数
    params = {
        'op': 'ph',      # 排行榜
        'dt': 'kf',      # 开放式基金
        'ft': 'all',     # 所有类型
        'rs': '',
        'gs': '0',
        'sc': 'zzf',     # 按规模排序
        'st': 'desc',    # 降序
        'sd': '2020-01-01',
        'ed': '2099-12-31',
        'qdii': '',
        'tabSubtype': ',,,,,',
        'pi': '1',      # 第1页
        'pn': '50',     # 每页50条
        'dx': '1'
    }

    print("\n[步骤1] 正在获取基金总数...")
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'

        # 解析响应 var rankData = {...}
        content = response.text
        if 'ErrCode:-999' in content or '无访问权限' in content:
            print("❌ API访问被拒绝，使用备用方案...")
            return get_funds_from_js()

        # 使用正则提取allRecords
        import re
        m = re.search(r'allRecords:(\d+)', content)
        if not m:
            print("❌ 无法获取基金总数，使用备用方案...")
            return get_funds_from_js()

        total_count = int(m.group(1))
        print(f"✅ 共有 {total_count} 个基金")

    except Exception as e:
        print(f"❌ 第一次请求失败: {e}")
        print("使用备用方案...")
        return get_funds_from_js()

    # 计算需要请求多少页
    page_size = 500  # 每页获取500条
    total_pages = (total_count + page_size - 1) // page_size

    print(f"\n[步骤2] 开始分页获取数据（每页{page_size}条，共{total_pages}页）...\n")

    all_funds = []

    for page in range(1, total_pages + 1):
        print(f"  获取第 {page}/{total_pages} 页...", end='', flush=True)

        params['pi'] = str(page)
        params['pn'] = str(page_size)

        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'

            # 解析数据 - 使用正则表达式提取datas数组
            import re
            content = response.text

            # 提取 datas:["...","...",...] 中的内容
            m = re.search(r'datas:\[(.*?)\]', content, re.DOTALL)
            if not m:
                print(f" ❌ 无法解析数据")
                continue

            datas_str = m.group(1)
            # 分割成单个基金数据（用","分隔，但要注意字符串内的引号）
            data_list = [s.strip().strip('"') for s in datas_str.split('","')]

            for item in data_list:
                if not item or not item.strip():
                    continue

                # 数据格式: "基金代码,基金名称,拼音缩写,净值日期,单位净值,累计净值,日增长率,..."
                # 示例: "009317,金信核心竞争力混合A,JXHXJZLHHA,2026-02-13,1.1921,2.5879,-1.45,..."
                fields = item.split(',')
                if len(fields) < 10:
                    continue

                try:
                    nav_rate_str = fields[6] if len(fields) > 6 else '0'
                    nav_rate = nav_rate_str.replace('%', '').strip()

                    fund = {
                        'symbol': fields[0],              # [0] 基金代码
                        'sname': fields[1],               # [1] 基金名称
                        'nav_date': fields[3],            # [3] 净值日期
                        'per_nav': fields[4],             # [4] 单位净值
                        'total_nav': fields[5],           # [5] 累计净值
                        'nav_rate': nav_rate,             # [6] 日增长率
                        'nav_a': '',                      # 涨跌额（需计算）
                        'yesterday_nav': '',              # 前一日净值（需计算）
                        'sg_states': '开放',              # 申购状态（默认开放）
                        'fund_manager': '',               # 基金经理（API不提供）
                        'jjlx': '',                       # 基金类型（API不提供）
                        'jjzfe': fields[14] if len(fields) > 14 else ''  # [14] 基金规模
                    }

                    # 计算前一日净值和涨跌额
                    if fund['per_nav'] and fund['nav_rate']:
                        try:
                            per_nav = float(fund['per_nav'])
                            rate = float(fund['nav_rate'])
                            yesterday_nav = per_nav / (1 + rate / 100)
                            nav_a = per_nav - yesterday_nav

                            fund['yesterday_nav'] = str(round(yesterday_nav, 4))
                            fund['nav_a'] = str(round(nav_a, 4))
                        except:
                            pass

                    all_funds.append(fund)

                except Exception as e:
                    print(f"  解析基金数据失败: {str(e)[:100]}")
                    continue

            print(f" ✅ 成功获取 {len(data_list)} 个")
            time.sleep(0.5)  # 短暂延迟，避免请求过快

        except Exception as e:
            print(f" ❌ {str(e)[:50]}")

    # 写入CSV
    print(f"\n[步骤3] 正在写入CSV文件...")

    # 中文标题
    chinese_headers = ['基金代码', '基金名称', '单位净值', '累计净值', '前一日净值',
                      '增长率', '涨跌额', '申购状态', '净值日期', '基金经理',
                      '基金类型', '基金zfe']

    fieldnames = ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav',
                 'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager',
                 'jjlx', 'jjzfe']

    # 获取根目录
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(root_dir, output_file)

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        # 写入中文标题
        f.write(','.join(chinese_headers) + '\n')

        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        for fund in all_funds:
            writer.writerow(fund)

    print(f"\n{'='*70}")
    print(f"✅ 数据获取完成！")
    print(f"{'='*70}")
    print(f"文件位置: {output_path}")
    print(f"总记录数: {len(all_funds)} 个")
    print(f"{'='*70}")

    return output_path


def get_funds_from_js():
    """
    备用方案：从fundcode_search.js获取基金代码，然后批量获取
    """
    print("\n使用备用方案：从基金代码列表获取数据...\n")

    import asyncio
    from browser_manager import BrowserManager
    from scrapers.eastmoney_scraper import EastmoneyScraper

    async def fetch():
        browser_manager = BrowserManager(headless=True)
        await browser_manager.start()

        scraper = EastmoneyScraper(browser_manager)

        # 使用现有的批量获取方法
        result = await scraper.fetch_all_funds_info(max_funds=None, batch_size=100, delay=0.5)

        await browser_manager.close()

        if result['success']:
            # 写入CSV
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_file = os.path.join(root_dir, f"all_funds_fast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

            chinese_headers = ['基金代码', '基金名称', '单位净值', '累计净值', '前一日净值',
                              '增长率', '涨跌额', '申购状态', '净值日期', '基金经理',
                              '基金类型', '基金zfe']

            fieldnames = ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav',
                         'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager',
                         'jjlx', 'jjzfe']

            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                f.write(','.join(chinese_headers) + '\n')
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                for fund in result['data']:
                    writer.writerow(fund)

            print(f"\n✅ 成功！文件: {output_file}")
            print(f"总记录数: {len(result['data'])} 个")
            return output_file

    return asyncio.run(fetch())


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 创建隐藏的 Tkinter 窗口用于文件对话框
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 设置默认输出目录为 E:\数据
    default_dir = r"E:\数据"
    # 如果 E:\数据 不存在，则回退到与 .bat 同目录
    if not os.path.exists(default_dir):
        default_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    default_filename = f"{datetime.now().strftime('%Y%m%d')}_基金数据.csv"
    default_path = os.path.join(default_dir, default_filename)

    # 弹出文件保存对话框
    output_file = filedialog.asksaveasfilename(
        title="选择基金数据保存位置",
        initialdir=default_dir,
        initialfile=default_filename,
        defaultextension=".csv",
        filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
    )

    root.destroy()

    # 如果用户取消了选择，则退出
    if not output_file:
        print("\n用户取消操作，程序退出。")
        input("\n按回车键退出...")
        sys.exit(0)

    # 执行数据获取
    get_all_funds_data(output_file)

