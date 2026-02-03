"""
天天基金网（东方财富）爬虫
支持：
1. 全量基金代码列表
2. 基金排行榜数据
3. 单个基金详情
4. 净值历史数据
"""
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base_scraper import BaseScraper
from browser_manager import BrowserManager


class EastmoneyScraper(BaseScraper):
    """天天基金网爬虫"""
    
    BASE_URL = "https://fund.eastmoney.com"
    
    # 基金类型映射
    FUND_TYPE_MAP = {
        "all": "",
        "stock": "gp",      # 股票型
        "hybrid": "hh",     # 混合型
        "bond": "zq",       # 债券型
        "index": "zs",      # 指数型
        "qdii": "qdii",     # QDII
        "money": "hb",      # 货币型
        "fof": "fof",       # FOF
    }
    
    async def scrape_all_fund_codes(self) -> Dict[str, Any]:
        """
        获取全量基金代码列表（约20000+只）
        数据源：fund.eastmoney.com/js/fundcode_search.js
        """
        page = await self.browser_manager.new_page()
        
        try:
            # 访问全量基金代码JS文件
            url = f"{self.BASE_URL}/js/fundcode_search.js"
            response = await page.goto(url, wait_until="load", timeout=30000)
            
            if response.status != 200:
                return self._error_response(f"请求失败，状态码: {response.status}")
            
            content = await response.text()
            
            # 解析 var r = [[...], [...], ...];
            # 格式: ["000001","HXCZHH","华夏成长混合","混合型-偏股","HUAXIACHENGZHANGHUNHE"]
            match = re.search(r'var r = (\[.*\]);', content, re.DOTALL)
            if not match:
                return self._error_response("无法解析基金代码数据")
            
            funds_data = json.loads(match.group(1))
            
            # 转换为标准格式
            funds = []
            for item in funds_data:
                if len(item) >= 4:
                    funds.append({
                        'symbol': item[0],           # 基金代码
                        'abbr': item[1],             # 拼音缩写
                        'sname': item[2],            # 基金名称
                        'jjlx': item[3],             # 基金类型
                        'pinyin': item[4] if len(item) > 4 else ''  # 全拼
                    })
            
            return self._success_response(
                funds,
                total_count=len(funds),
                source="fundcode_search.js"
            )
            
        except Exception as e:
            return self._error_response(f"获取全量基金代码失败: {str(e)}")
        finally:
            await page.close()
    
    async def scrape_list(
        self,
        fund_type: str = "all",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        从排行榜获取基金列表（包含净值数据）
        注意：排行榜可能不包含最新发行的基金
        """
        page_obj = await self.browser_manager.new_page()
        
        try:
            # 构造排行榜URL
            ft = self.FUND_TYPE_MAP.get(fund_type, "")
            url = f"{self.BASE_URL}/data/fundranking.html"
            if ft:
                url += f"#t={ft}"
            
            await page_obj.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待表格加载
            await page_obj.wait_for_selector("#dbtable tbody tr", timeout=30000)
            
            # 添加延迟，确保数据加载完成
            await self.random_delay(1, 2)
            
            # 提取表格数据
            funds = await page_obj.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#dbtable tbody tr');
                    return Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length < 8) return null;
                        
                        return {
                            symbol: cells[2]?.querySelector('a')?.textContent?.trim() || '',
                            sname: cells[3]?.querySelector('a')?.textContent?.trim() || '',
                            nav_date: cells[4]?.textContent?.trim() || '',
                            per_nav: cells[5]?.textContent?.trim() || '',
                            total_nav: cells[6]?.textContent?.trim() || '',
                            nav_rate: cells[7]?.querySelector('span')?.textContent?.trim()?.replace('%', '') || '',
                            week_rate: cells[8]?.querySelector('span')?.textContent?.trim()?.replace('%', '') || '',
                            month_rate: cells[9]?.querySelector('span')?.textContent?.trim()?.replace('%', '') || '',
                            quarter_rate: cells[10]?.querySelector('span')?.textContent?.trim()?.replace('%', '') || '',
                            half_year_rate: cells[11]?.querySelector('span')?.textContent?.trim()?.replace('%', '') || '',
                            year_rate: cells[12]?.querySelector('span')?.textContent?.trim()?.replace('%', '') || ''
                        };
                    }).filter(item => item !== null && item.symbol !== '');
                }
            """)
            
            # 分页处理
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paged_funds = funds[start_idx:end_idx]
            
            return self._success_response(
                paged_funds,
                total_count=len(funds),
                page=page,
                page_size=page_size,
                source="ranking"
            )
            
        except Exception as e:
            return self._error_response(f"获取基金排行榜失败: {str(e)}")
        finally:
            await page_obj.close()
    
    async def scrape_detail(self, symbol: str) -> Dict[str, Any]:
        """
        获取单个基金的详细信息
        数据源：基金详情页
        """
        page = await self.browser_manager.new_page()
        
        try:
            # 访问基金详情页
            url = f"{self.BASE_URL}/{symbol}.html"
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待关键元素加载
            await page.wait_for_selector(".fundDetail-tit", timeout=30000)
            
            await self.random_delay(0.5, 1.5)
            
            # 提取详情数据
            data = await page.evaluate("""
                () => {
                    const getText = (sel) => {
                        const el = document.querySelector(sel);
                        return el ? el.textContent.trim() : '';
                    };

                    // 基金名称
                    const fundName = getText('.fundDetail-tit');

                    // 从 dataOfFund 文本中提取净值信息
                    const dataOfFundText = getText('.dataOfFund');

                    // 提取净值日期 - 格式: (2026-01-30)
                    let navDate = '';
                    const dateMatch = dataOfFundText.match(/\\((\\d{4}-\\d{2}-\\d{2})\\)/);
                    if (dateMatch) {
                        navDate = dateMatch[1];
                    }

                    // 提取单位净值和增长率 - 格式: 1.1670-0.51%
                    let perNav = '', navRate = '';
                    const navMatch = dataOfFundText.match(/(\\d+\\.\\d+)([\\-\\+]?\\d+\\.\\d+)%/);
                    if (navMatch) {
                        perNav = navMatch[1];
                        navRate = navMatch[2];
                    }

                    // 提取累计净值
                    let totalNav = '';
                    const totalNavMatch = dataOfFundText.match(/累计净值(\\d+\\.\\d+)/);
                    if (totalNavMatch) {
                        totalNav = totalNavMatch[1];
                    }

                    // 从 infoOfFund 文本中提取基金信息
                    const infoOfFundText = getText('.infoOfFund');

                    // 提取基金经理 - 格式: 基金经理：郑晓辉等成 立 日
                    let fundManager = '';
                    const managerMatch = infoOfFundText.match(/基金经理[：:](.*?)成 立 日/);
                    if (managerMatch) {
                        fundManager = managerMatch[1].trim();
                    }

                    // 提取基金类型 - 格式: 类型：混合型-灵活  |
                    let fundType = '';
                    const typeMatch = infoOfFundText.match(/类型[：:](.*?)\\|/);
                    if (typeMatch) {
                        fundType = typeMatch[1].trim();
                    }

                    // 提取基金规模 - 格式: 规模：29.37亿元
                    let fundScale = '';
                    const scaleMatch = infoOfFundText.match(/规模[：:](\\d+\\.\\d+亿元)/);
                    if (scaleMatch) {
                        fundScale = scaleMatch[1];
                    }

                    // 提取成立日期 - 格式: 成 立 日：2001-12-18
                    let establishDate = '';
                    const estMatch = infoOfFundText.match(/成 立 日[：:](\\d{4}-\\d{2}-\\d{2})/);
                    if (estMatch) {
                        establishDate = estMatch[1];
                    }

                    // 提取管理人 - 格式: 管 理 人：华夏基金基金评级
                    let fundCompany = '';
                    const companyMatch = infoOfFundText.match(/管 理 人[：:](.*?)基金评级/);
                    if (companyMatch) {
                        fundCompany = companyMatch[1].trim();
                    }

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
                        fund_manager: fundManager,
                        jjlx: fundType,
                        fund_company: fundCompany,
                        establishment_date: establishDate,
                        fund_scale: fundScale,
                        sg_states: sgStates
                    };
                }
            """)
            
            # 补充基金代码
            data['symbol'] = symbol
            
            # 计算前一日净值和涨跌额
            if data['per_nav'] and data['nav_rate']:
                try:
                    per_nav = float(data['per_nav'])
                    nav_rate = float(data['nav_rate'])
                    yesterday_nav = per_nav / (1 + nav_rate / 100)
                    nav_a = per_nav - yesterday_nav
                    
                    data['yesterday_nav'] = round(yesterday_nav, 4)
                    data['nav_a'] = round(nav_a, 4)
                except:
                    data['yesterday_nav'] = ''
                    data['nav_a'] = ''
            
            return self._success_response(data, source="detail_page")
            
        except Exception as e:
            return self._error_response(f"获取基金详情失败: {str(e)}")
        finally:
            await page.close()
    
    async def scrape_nav_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        获取基金净值历史数据
        """
        page = await self.browser_manager.new_page()
        
        try:
            # 访问净值历史页面
            url = f"{self.BASE_URL}/f10/jjjz_{symbol}.html"
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待表格加载
            await page.wait_for_selector("#jztable tbody tr", timeout=30000)
            
            await self.random_delay(0.5, 1)
            
            # 提取净值历史
            nav_list = await page.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#jztable tbody tr');
                    return Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length < 4) return null;
                        
                        return {
                            date: cells[0]?.textContent?.trim() || '',
                            nav: cells[1]?.textContent?.trim() || '',
                            total_nav: cells[2]?.textContent?.trim() || '',
                            rate: cells[3]?.textContent?.trim()?.replace('%', '') || ''
                        };
                    }).filter(item => item !== null && item.date !== '');
                }
            """)
            
            # 日期过滤
            if start_date or end_date:
                filtered_list = []
                for item in nav_list:
                    if start_date and item['date'] < start_date:
                        continue
                    if end_date and item['date'] > end_date:
                        continue
                    filtered_list.append(item)
                nav_list = filtered_list
            
            # 限制数量
            nav_list = nav_list[:limit]
            
            return self._success_response(
                nav_list,
                symbol=symbol,
                total_count=len(nav_list),
                source="nav_history_page"
            )
            
        except Exception as e:
            return self._error_response(f"获取净值历史失败: {str(e)}")
        finally:
            await page.close()
    
    async def scrape_funds_batch(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批量获取多个基金的详情
        """
        results = []
        errors = []
        
        for symbol in symbols:
            try:
                result = await self.scrape_detail(symbol)
                if result['success']:
                    results.append(result['data'])
                else:
                    errors.append({'symbol': symbol, 'error': result['error']})
                
                # 每个请求之间添加延迟
                await self.random_delay(1, 2)
                
            except Exception as e:
                errors.append({'symbol': symbol, 'error': str(e)})
        
        return self._success_response(
            results,
            total_requested=len(symbols),
            success_count=len(results),
            error_count=len(errors),
            errors=errors if errors else None
        )

    async def fetch_all_funds_info(
        self,
        batch_size: int = 100,
        max_funds: Optional[int] = None,
        delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        获取所有基金的完整信息

        Args:
            batch_size: 每批处理的基金数量
            max_funds: 最多获取的基金数量（None表示全部）
            delay: 每个请求之间的延迟（秒）

        Returns:
            包含所有基金信息的字典，字段与新浪数据格式兼容：
            ['symbol', 'sname', 'per_nav', 'total_nav', 'yesterday_nav',
             'nav_rate', 'nav_a', 'sg_states', 'nav_date', 'fund_manager', 'jjlx', 'jjzfe']
        """
        try:
            # 1. 获取全量基金代码
            codes_result = await self.scrape_all_fund_codes()
            if not codes_result['success']:
                return self._error_response("获取基金代码列表失败")

            all_codes = codes_result['data']

            # 限制数量（如果指定）
            if max_funds:
                all_codes = all_codes[:max_funds]

            total = len(all_codes)

            # 2. 批量获取详情
            all_results = []
            failed = []

            for i in range(0, total, batch_size):
                batch = all_codes[i:i+batch_size]
                batch_symbols = [f['symbol'] for f in batch]

                print(f"正在获取第 {i+1}-{min(i+batch_size, total)} 个基金（共 {total} 个）...")

                for symbol in batch_symbols:
                    try:
                        result = await self.scrape_detail(symbol)
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
                            all_results.append(formatted_data)
                        else:
                            failed.append(symbol)
                    except Exception as e:
                        print(f"获取基金 {symbol} 失败: {str(e)}")
                        failed.append(symbol)

                    # 延迟
                    await self.random_delay(delay * 0.8, delay * 1.2)

            return self._success_response(
                all_results,
                total_count=len(all_results),
                failed_count=len(failed),
                failed_symbols=failed[:100] if len(failed) > 100 else failed,  # 最多返回100个失败的
                source="fetch_all_funds_info"
            )

        except Exception as e:
            return self._error_response(f"获取所有基金信息失败: {str(e)}")
