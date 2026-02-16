"""
基金数据获取工具 - 图形界面版本
双击运行，输入参数后自动获取所有基金数据

功能：
- 自动获取所有26000+个基金数据
- 边爬边写，数据实时保存
- 支持断点续传
- 详细的进度日志
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import asyncio
import sys
import os
from datetime import datetime
import shutil

# 清理 Python 缓存文件（避免旧代码缓存问题）
def clear_pycache():
    """清理当前目录及子目录下的所有 __pycache__ 文件夹"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, _ in os.walk(current_dir):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_path)
            except:
                pass

# 启动时清理缓存
clear_pycache()

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager
from scrapers.eastmoney_scraper import EastmoneyScraper


class FundScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("基金数据获取工具 v1.0")
        self.root.geometry("800x600")

        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')

        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="基金数据获取工具",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 输出文件
        ttk.Label(main_frame, text="输出文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value=f"all_funds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=50)
        output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        browse_btn = ttk.Button(main_frame, text="浏览...", command=self.browse_file)
        browse_btn.grid(row=1, column=2, pady=5)

        # 断点续传
        self.resume_var = tk.BooleanVar(value=False)
        resume_check = ttk.Checkbutton(main_frame, text="断点续传（从已有文件继续）",
                                       variable=self.resume_var)
        resume_check.grid(row=2, column=1, sticky=tk.W, pady=5)

        # 高级选项
        options_frame = ttk.LabelFrame(main_frame, text="高级选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="批次大小:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_var = tk.IntVar(value=100)
        ttk.Spinbox(options_frame, from_=10, to=500, textvariable=self.batch_var,
                   width=10).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        ttk.Label(options_frame, text="延迟(秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(options_frame, from_=0.5, to=5.0, increment=0.5,
                   textvariable=self.delay_var, width=10).grid(row=1, column=1,
                                                                sticky=tk.W, pady=5, padx=5)

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(button_frame, text="开始获取",
                                    command=self.start_scraping, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="停止",
                                   command=self.stop_scraping, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                           maximum=100, length=400)
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置主框架的行列权重
        main_frame.rowconfigure(7, weight=1)

        # 停止标志
        self.stop_flag = False

    def browse_file(self):
        """浏览文件对话框"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=self.output_var.get()
        )
        if filename:
            self.output_var.set(filename)

    def log(self, message, end='\n'):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}{end}")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_scraping(self):
        """开始获取数据"""
        output_file = self.output_var.get()

        if not output_file:
            messagebox.showerror("错误", "请指定输出文件名")
            return

        # 禁用开始按钮，启用停止按钮
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.stop_flag = False

        # 清空日志
        self.log_text.delete(1.0, tk.END)

        # 在新线程中运行
        thread = threading.Thread(target=self.run_scraper)
        thread.daemon = True
        thread.start()

    def stop_scraping(self):
        """停止获取"""
        self.stop_flag = True
        self.log("正在停止...")
        self.status_var.set("正在停止，请稍候...")

    def run_scraper(self):
        """运行爬虫（在线程中）"""
        try:
            asyncio.run(self.fetch_funds())
        except Exception as e:
            self.log(f"发生错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    async def fetch_funds(self):
        """获取基金数据"""
        output_file = self.output_var.get()
        resume = self.resume_var.get()
        batch_size = self.batch_var.get()
        delay = self.delay_var.get()

        self.log("="*70)
        self.log("开始获取所有基金数据（约26000+个）")
        self.log("="*70)

        # 断点续传
        processed_symbols = set()
        if resume and os.path.exists(output_file):
            self.log(f"\n断点续传模式")
            # 读取已处理的基金代码
            try:
                with open(output_file, 'r', encoding='utf-8-sig') as f:
                    import csv
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 兼容中文和英文标题
                        symbol = row.get('symbol') or row.get('基金代码')
                        if symbol:
                            processed_symbols.add(symbol)
                if processed_symbols:
                    self.log(f"已处理 {len(processed_symbols)} 个基金，将跳过这些基金")
            except Exception as e:
                self.log(f"⚠️ 读取已有文件失败: {e}")

        self.status_var.set("正在启动浏览器...")
        self.log("\n[1/3] 正在启动浏览器...")
        browser_manager = BrowserManager(headless=True)

        try:
            await browser_manager.start()
            self.log("✅ 浏览器启动成功")

            self.status_var.set("正在初始化爬虫...")
            self.log("\n[2/3] 正在初始化爬虫...")
            scraper = EastmoneyScraper(browser_manager)
            self.log("✅ 爬虫初始化完成")

            # 获取基金代码列表
            self.status_var.set("正在获取基金列表...")
            self.log("\n[3/3] 正在获取基金数据...")
            self.log("  [步骤1] 正在获取基金代码列表...")

            codes_result = await scraper.scrape_all_fund_codes()

            if not codes_result['success']:
                self.log(f"❌ 获取基金代码列表失败")
                return

            all_codes = codes_result['data']
            self.log(f"  ✅ 成功获取 {len(all_codes)} 个基金代码")

            # 过滤已处理的基金
            todo_codes = [f for f in all_codes if f['symbol'] not in processed_symbols]
            skipped = len(all_codes) - len(todo_codes)

            if skipped > 0:
                self.log(f"  ℹ️  跳过已处理的 {skipped} 个基金")
                self.log(f"  ℹ️  还需处理 {len(todo_codes)} 个基金")

            total = len(all_codes)

            # 开始获取
            self.log(f"\n  [步骤2] 开始批量获取基金详情（每批 {batch_size} 个，延迟 {delay}秒）...")
            self.log(f"  💾 数据将实时写入文件: {os.path.abspath(output_file)}\n")

            success_count = 0
            failed_count = 0

            # 打开文件（追加模式）
            import csv
            is_new_file = not os.path.exists(output_file)
            file_handle = open(output_file, 'a' if not is_new_file else 'w',
                             newline='', encoding='utf-8-sig')

            # 英文字段名
            fieldnames = ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav',
                         'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager',
                         'jjlx', 'jjzfe']

            # 中文标题对应
            chinese_headers = ['基金代码', '基金名称', '单位净值', '累计净值', '前一日净值',
                             '增长率', '涨跌额', '申购状态', '净值日期', '基金经理',
                             '基金类型', '基金zfe']

            writer = csv.DictWriter(file_handle, fieldnames=fieldnames, extrasaction='ignore')

            if is_new_file:
                # 手动写入中文标题
                file_handle.write(','.join(chinese_headers) + '\n')
                self.log(f"📝 创建新文件: {os.path.abspath(output_file)}")
            else:
                self.log(f"📝 追加到已有文件: {os.path.abspath(output_file)}")

            # 批量处理
            for i in range(0, len(todo_codes), batch_size):
                if self.stop_flag:
                    self.log("\n用户取消操作")
                    break

                batch = todo_codes[i:i+batch_size]
                batch_symbols = [f['symbol'] for f in batch]

                batch_num = i // batch_size + 1
                total_batches = (len(todo_codes) + batch_size - 1) // batch_size
                self.log(f"  【批次 {batch_num}/{total_batches}】 正在获取第 {i+1}-{min(i+batch_size, len(todo_codes))} 个基金...")

                batch_success = 0
                for idx, symbol in enumerate(batch_symbols, 1):
                    if self.stop_flag:
                        break

                    try:
                        current = i + idx
                        overall = skipped + current

                        self.status_var.set(f"正在获取 {symbol} ({overall}/{total})...")
                        self.log(f"    [{overall}/{total}] {symbol}...", end='')

                        result = await scraper.scrape_detail(symbol)
                        if result['success']:
                            fund_data = result['data']

                            # 格式化数据
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
                                'jjzfe': fund_data.get('fund_scale', '')
                            }

                            # 立即写入文件
                            writer.writerow(formatted_data)
                            file_handle.flush()

                            success_count += 1
                            batch_success += 1
                            self.log(" ✅")
                        else:
                            failed_count += 1
                            self.log(" ❌")
                    except Exception as e:
                        self.log(f" ❌ 错误: {str(e)[:50]}")
                        failed_count += 1

                    # 延迟
                    await asyncio.sleep(delay)

                # 批次统计
                self.log(f"  批次完成: 成功 {batch_success}/{len(batch_symbols)} 个")
                self.log(f"  总进度: 成功 {success_count + skipped}/{total} (本次新增 {success_count})\n")

                # 更新进度条
                progress = ((success_count + skipped) / total) * 100
                self.progress_var.set(progress)

            # 关闭文件
            file_handle.close()

            # 完成
            self.log("\n" + "="*70)
            self.log("数据获取完成")
            self.log("="*70)
            self.log(f"✅ 文件位置: {os.path.abspath(output_file)}")
            self.log(f"✅ 总记录数: {success_count + skipped} 个")
            if skipped > 0:
                self.log(f"   - 已有记录: {skipped} 个")
                self.log(f"   - 新增记录: {success_count} 个")
            self.log(f"❌ 失败: {failed_count} 个")

            self.status_var.set(f"完成！成功: {success_count + skipped}, 失败: {failed_count}")
            self.progress_var.set(100)

            messagebox.showinfo("完成", f"数据获取完成！\n\n成功: {success_count + skipped} 个\n失败: {failed_count} 个\n\n文件位置:\n{os.path.abspath(output_file)}")

        except Exception as e:
            self.log(f"\n❌ 发生错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("错误", f"发生错误：{str(e)}")

        finally:
            await browser_manager.close()


def main():
    root = tk.Tk()
    app = FundScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
