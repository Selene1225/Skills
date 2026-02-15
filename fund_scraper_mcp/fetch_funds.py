"""
命令行工具 - 获取基金数据并保存为 CSV/JSON（支持断点续传）
用法：
  python fetch_funds.py --max 100                    # 获取前100个基金
  python fetch_funds.py --all                        # 获取所有基金（约26000+个，耗时较长）
  python fetch_funds.py --max 100 --format csv       # 保存为 CSV 格式
  python fetch_funds.py --max 100 --output my.csv    # 指定输出文件名
  python fetch_funds.py --all --resume               # 断点续传，从上次中断处继续
"""
import asyncio
import json
import csv
import sys
import os
import argparse
from datetime import datetime

# 设置 UTF-8 编码（Windows 控制台兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager
from scrapers.eastmoney_scraper import EastmoneyScraper


class IncrementalCSVWriter:
    """增量写入 CSV 的工具类"""

    def __init__(self, filename):
        self.filename = filename
        self.abs_path = os.path.abspath(filename)
        self.fieldnames = [
            'symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav',
            'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager',
            'jjlx', 'jjzfe'
        ]
        self.count = 0
        self.file = None
        self.writer = None
        self.is_new_file = not os.path.exists(filename)

    def __enter__(self):
        # 如果是新文件，创建并写入表头
        if self.is_new_file:
            self.file = open(self.filename, 'w', newline='', encoding='utf-8-sig')
            self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames, extrasaction='ignore')
            self.writer.writeheader()
            print(f"📝 创建新文件: {self.abs_path}")
        else:
            # 如果是已存在的文件，追加模式打开
            self.file = open(self.filename, 'a', newline='', encoding='utf-8-sig')
            self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames, extrasaction='ignore')
            # 读取已有记录数
            with open(self.filename, 'r', encoding='utf-8-sig') as f:
                self.count = sum(1 for _ in f) - 1  # 减去表头
            print(f"📝 追加到已有文件: {self.abs_path}")
            print(f"   已有 {self.count} 条记录")

        return self

    def write(self, data):
        """写入一条记录"""
        self.writer.writerow(data)
        self.file.flush()  # 立即刷新到磁盘
        self.count += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()


def load_processed_symbols(filename):
    """从已有的CSV文件中读取已处理的基金代码"""
    if not os.path.exists(filename):
        return set()

    processed = set()
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('symbol'):
                    processed.add(row['symbol'])
    except Exception as e:
        print(f"⚠️ 读取已有文件失败: {e}")
        return set()

    return processed


async def fetch_funds_incremental(output_file, max_funds=None, batch_size=100, delay=1.0, resume=False):
    """增量获取基金数据（边爬边写）"""

    print("=" * 70)
    if max_funds:
        print(f"开始获取前 {max_funds} 个基金数据...")
    else:
        print("开始获取所有基金数据（约26000+个，预计需要数小时）...")
    print("=" * 70)

    # 如果是续传模式，读取已处理的基金代码
    processed_symbols = set()
    if resume:
        print("\n🔄 断点续传模式")
        processed_symbols = load_processed_symbols(output_file)
        if processed_symbols:
            print(f"   已处理 {len(processed_symbols)} 个基金，将跳过这些基金")
        else:
            print("   未找到已处理记录，从头开始")

    print("\n[1/3] 正在启动浏览器...")
    browser_manager = BrowserManager(headless=True)

    try:
        await browser_manager.start()
        print("✅ 浏览器启动成功")

        print("\n[2/3] 正在初始化爬虫...")
        scraper = EastmoneyScraper(browser_manager)
        print("✅ 爬虫初始化完成")

        print("\n[3/3] 正在获取基金数据...")

        # 获取基金代码列表
        print("  [步骤1] 正在获取基金代码列表...")
        print("    正在访问基金代码数据页面...")
        codes_result = await scraper.scrape_all_fund_codes()

        if not codes_result['success']:
            print(f"❌ 获取基金代码列表失败")
            return None

        all_codes = codes_result['data']
        print(f"  ✅ 成功获取 {len(all_codes)} 个基金代码")

        # 限制数量（如果指定）
        if max_funds:
            all_codes = all_codes[:max_funds]
            print(f"  ℹ️  限制为前 {max_funds} 个基金")

        total = len(all_codes)

        # 过滤已处理的基金
        todo_codes = [f for f in all_codes if f['symbol'] not in processed_symbols]
        skipped = len(all_codes) - len(todo_codes)

        if skipped > 0:
            print(f"  ℹ️  跳过已处理的 {skipped} 个基金")
            print(f"  ℹ️  还需处理 {len(todo_codes)} 个基金")

        # 开始增量写入
        print(f"\n  [步骤2] 开始批量获取基金详情（每批 {batch_size} 个，延迟 {delay}秒）...")
        print(f"  💾 数据将实时写入文件: {os.path.abspath(output_file)}\n")

        success_count = 0
        failed_count = 0
        failed_symbols = []

        with IncrementalCSVWriter(output_file) as csv_writer:
            for i in range(0, len(todo_codes), batch_size):
                batch = todo_codes[i:i+batch_size]
                batch_symbols = [f['symbol'] for f in batch]

                batch_num = i // batch_size + 1
                total_batches = (len(todo_codes) + batch_size - 1) // batch_size
                print(f"  【批次 {batch_num}/{total_batches}】 正在获取第 {i+1}-{min(i+batch_size, len(todo_codes))} 个基金...")

                batch_success = 0
                for idx, symbol in enumerate(batch_symbols, 1):
                    try:
                        # 显示当前进度
                        current = i + idx
                        overall = skipped + current
                        print(f"    [{overall}/{total}] {symbol}...", end='', flush=True)

                        result = await scraper.scrape_detail(symbol)
                        if result['success']:
                            fund_data = result['data']

                            # 格式化为与旧代码兼容的字段名
                            formatted_data = {
                                'symbol': fund_data.get('symbol', ''),
                                'sname': fund_data.get('sname', ''),
                                'per_nav': fund_data.get('per_nav', ''),
                                'total_nav': fund_data.get('total_nav', ''),
                                'yesterday_nav': fund_data.get('yesterday_nav', ''),
                                'nav_rate': fund_data.get('nav_rate', ''),
                                'nav_a': fund_data.get('nav_a', ''),
                                'sg_states': fund_data.get('sg_states', ''),
                                'nav_date': fund_data.get('nav_date', ''),
                                'fund_manager': fund_data.get('fund_manager', ''),
                                'jjlx': fund_data.get('jjlx', ''),
                                'jjzfe': fund_data.get('fund_scale', '')  # fund_scale -> jjzfe
                            }

                            # 立即写入文件
                            csv_writer.write(formatted_data)
                            success_count += 1
                            batch_success += 1
                            print(" ✅")
                        else:
                            failed_count += 1
                            failed_symbols.append(symbol)
                            print(" ❌")
                    except Exception as e:
                        print(f" ❌ 错误: {str(e)[:50]}")
                        failed_count += 1
                        failed_symbols.append(symbol)

                    # 延迟
                    await scraper.random_delay(delay * 0.8, delay * 1.2)

                # 批次完成统计
                print(f"  批次完成: 成功 {batch_success}/{len(batch_symbols)} 个")
                print(f"  总进度: 成功 {success_count + skipped}/{total} (本次新增 {success_count})\n")

        # 返回统计信息
        return {
            'success': True,
            'total_count': success_count + skipped,
            'new_count': success_count,
            'skipped_count': skipped,
            'failed_count': failed_count,
            'failed_symbols': failed_symbols[:100] if len(failed_symbols) > 100 else failed_symbols
        }

    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        await browser_manager.close()


def main():
    parser = argparse.ArgumentParser(
        description='获取基金数据（支持断点续传）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fetch_funds.py --max 100                    # 获取前100个基金
  python fetch_funds.py --all                        # 获取所有基金
  python fetch_funds.py --max 500 --output my.csv    # 指定文件名
  python fetch_funds.py --all --resume               # 断点续传
  python fetch_funds.py --all --batch 200 --delay 0.5  # 自定义批次大小和延迟
        """
    )

    parser.add_argument('--max', type=int, help='获取的最大基金数量')
    parser.add_argument('--all', action='store_true', help='获取所有基金（约26000+个）')
    parser.add_argument('--output', '-o', help='输出文件名（默认自动生成）')
    parser.add_argument('--resume', action='store_true', help='断点续传模式（从已有文件继续）')
    parser.add_argument('--batch', type=int, default=100,
                        help='每批获取的基金数量 (默认: 100)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='每批之间的延迟秒数 (默认: 1.0)')

    args = parser.parse_args()

    # 确定获取数量
    if args.all:
        max_funds = None
    elif args.max:
        max_funds = args.max
    else:
        # 默认获取100个
        max_funds = 100
        print(f"未指定数量，默认获取前 {max_funds} 个基金")
        print("提示: 使用 --max N 指定数量，或 --all 获取全部\n")

    # 确定输出文件名
    if args.output:
        output_file = args.output
    else:
        if args.resume:
            # 续传模式需要指定文件
            print("❌ 错误: 断点续传模式必须使用 --output 指定文件名")
            sys.exit(1)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'funds_data_{timestamp}.csv'

    # 获取数据（增量模式）
    result = asyncio.run(fetch_funds_incremental(
        output_file=output_file,
        max_funds=max_funds,
        batch_size=args.batch,
        delay=args.delay,
        resume=args.resume
    ))

    if not result:
        sys.exit(1)

    # 显示统计
    abs_path = os.path.abspath(output_file)
    print(f"\n" + "=" * 70)
    print(f"数据获取完成")
    print(f"=" * 70)
    print(f"✅ 文件位置: {abs_path}")
    print(f"✅ 总记录数: {result.get('total_count', 0)} 个")
    if result.get('skipped_count', 0) > 0:
        print(f"   - 已有记录: {result.get('skipped_count', 0)} 个")
        print(f"   - 新增记录: {result.get('new_count', 0)} 个")
    print(f"❌ 失败: {result.get('failed_count', 0)} 个")
    if result.get('failed_symbols'):
        print(f"   失败的基金代码: {', '.join(result['failed_symbols'][:10])}")
        if len(result['failed_symbols']) > 10:
            print(f"   ... 还有 {len(result['failed_symbols']) - 10} 个")


if __name__ == "__main__":
    main()
