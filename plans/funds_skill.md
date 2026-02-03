# Skills 设计文档

## 1. Chrome DevTools MCP Server Skill

### 1.1 背景与目标

**问题：**
- 新浪财经API有反爬机制，IP容易被封
- 天天基金网排行榜API不包含新发行的基金
- akshare也存在部分基金找不到的情况
- 需要一个更稳定、更全面的数据获取方案

**解决方案：**
创建一个 MCP Server Skill，通过 Chrome DevTools Protocol (CDP) 模拟真实浏览器操作，抓取基金数据。

### 1.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent (Copilot)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Server: fund-scraper                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Tools                             │   │
│  │  - scrape_all_fund_codes  获取全量基金代码列表        │   │
│  │  - scrape_fund_list       获取基金排行榜（含净值）    │   │
│  │  - scrape_fund_detail     获取单个基金详情            │   │
│  │  - scrape_fund_nav_history 获取净值历史              │   │
│  │  - scrape_funds_batch     批量获取基金详情            │   │
│  │  - check_browser_status   检查浏览器状态              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │ Playwright (基于 CDP)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Microsoft Edge Browser                   │
│  - Headless 模式运行                                        │
│  - 使用系统已安装的 Edge，无需下载额外浏览器                   │
│  - 自动处理 Cookie、Session                                 │
│  - 模拟真实用户行为                                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 MCP Server 定义

**Server 名称：** `fund-scraper-mcp`

**配置文件 (mcp.json)：**
```json
{
  "mcpServers": {
    "fund-scraper": {
      "command": "python",
      "args": ["path/to/fund_scraper_mcp/server.py"],
      "env": {
        "HEADLESS": "true"
      }
    }
  }
}
```

**说明：** 使用系统已安装的 Microsoft Edge 浏览器，无需配置 `CHROME_PATH` 或下载额外浏览器。

### 1.4 功能特性

| 功能 | 描述 | 数据量 |
|------|------|--------|
| `scrape_all_fund_codes` | 获取全量基金代码列表 | 26000+ 只 |
| `scrape_fund_list` | 获取基金排行榜（含净值） | ~19000 只 |
| `scrape_fund_detail` | 获取单个基金详情 | 12+ 字段 |
| `scrape_fund_nav_history` | 获取净值历史 | 自定义时间范围 |
| `scrape_funds_batch` | 批量获取基金详情 | 自定义数量 |
| `check_browser_status` | 检查浏览器状态 | - |

### 1.5 Tools 详细设计

#### Tool 1: `scrape_all_fund_codes`

**功能：** 获取全量基金代码列表（约 26000+ 只）

**输入参数：** 无

**输出：**
```typescript
{
  success: boolean,
  total_count: number,  // 约 26000+
  data: Array<{
    symbol: string,      // 基金代码
    sname: string,       // 基金名称
    jjlx: string        // 基金类型
  }>,
  error?: string
}
```

**实现要点：**
- 访问 `https://fund.eastmoney.com/js/fundcode_search.js`
- 解析 JavaScript 变量中的基金数据
- 这是获取全量基金的最可靠方式，无反爬限制

---

#### Tool 2: `scrape_fund_list`

**功能：** 从天天基金排行榜获取基金列表（含净值数据）

**数据源：**

天天基金网提供两种数据获取方式：

| 接口 | URL | 数据量 | 特点 |
|------|-----|--------|------|
| 全量基金代码 | `fund.eastmoney.com/js/fundcode_search.js` | **26000+** | ✅ 全量代码，无反爬，仅基础信息 |
| 基金排行榜 | `fund.eastmoney.com/data/fundranking.html` | ~19000 | ✅ 包含净值数据，但不含新发行基金 |

**推荐策略：**
1. 使用 `scrape_all_fund_codes` 获取全部基金代码
2. 使用 `scrape_fund_list` 获取排行榜中的净值数据
3. 使用 `scrape_fund_detail` 获取单个基金的详细信息

**输入参数：**
```typescript
{
  fund_type?: "all" | "stock" | "bond" | "hybrid" | "qdii" | "money",  // 基金类型（可选）
  page?: number,           // 页码，默认1
  page_size?: number,      // 每页数量，默认50
  sort_by?: string,        // 排序字段（可选）
  sort_order?: "asc" | "desc"  // 排序方向（可选）
}
```

**输出：**
```typescript
{
  success: boolean,
  total_count: number,
  page: number,
  data: Array<{
    symbol: string,        // 基金代码
    sname: string,         // 基金名称
    per_nav: string,       // 单位净值
    total_nav: string,     // 累计净值
    nav_rate: number,      // 日增长率
    nav_date: string,      // 净值日期
    fund_manager?: string, // 基金经理
    jjlx?: string,         // 基金类型
    fund_scale?: string    // 基金规模（带单位，如 "29.37亿"）
  }>,
  error?: string
}
```

**实现要点：**
- 访问 `https://fund.eastmoney.com/data/fundranking.html`
- 使用 Playwright 等待页面加载完成
- 提取表格数据
- 处理分页

---

#### Tool 3: `scrape_fund_detail`

**功能：** 获取单个基金的详细信息

**输入参数：**
```typescript
{
  symbol: string          // 基金代码
}
```

**输出：**
```typescript
{
  success: boolean,
  data: {
    symbol: string,
    sname: string,
    per_nav: string,
    total_nav: string,
    yesterday_nav: number,
    nav_rate: number,
    nav_a: number,
    nav_date: string,
    fund_manager: string,
    jjlx: string,
    fund_scale: string,    // 基金规模（带单位，如 "29.37亿"）
    sg_states: string,
    // 额外详情
    establishment_date?: string,  // 成立日期
    fund_company?: string,        // 基金公司
    benchmark?: string,           // 业绩比较基准
    investment_scope?: string     // 投资范围
  },
  error?: string
}
```

**实现要点：**
- 访问基金详情页
- 提取页面中的各项数据
- 处理动态加载内容

---

#### Tool 4: `scrape_fund_nav_history`

**功能：** 获取基金净值历史数据

**输入参数：**
```typescript
{
  symbol: string,          // 基金代码
  start_date?: string,     // 开始日期 YYYY-MM-DD
  end_date?: string,       // 结束日期 YYYY-MM-DD
  limit?: number           // 返回条数限制
}
```

**输出：**
```typescript
{
  success: boolean,
  data: Array<{
    date: string,          // 日期
    nav: number,           // 单位净值
    total_nav: number,     // 累计净值
    rate: number           // 日增长率
  }>,
  error?: string
}
```

---

#### Tool 5: `scrape_funds_batch`

**功能：** 批量获取多个基金的详细信息

**输入参数：**
```typescript
{
  symbols: string[],       // 基金代码数组，如 ["000001", "110022", "161005"]
  delay?: number           // 请求间隔（毫秒），默认 1000，避免请求过快
}
```

**输出：**
```typescript
{
  success: boolean,
  data: Array<FundDetail>,  // 成功获取的基金详情数组
  failed?: string[],        // 失败的基金代码列表
  error?: string
}
```

**实现要点：**
- 遍历基金代码列表，逐个调用详情接口
- 添加延迟避免请求过快
- 记录失败的基金代码
- 返回所有成功和失败的结果

---

#### Tool 6: `check_browser_status`

**功能：** 检查浏览器连接状态

**输入参数：** 无

**输出：**
```typescript
{
  connected: boolean,
  browser_version?: string,
  pages_open?: number,
  error?: string
}
```

### 1.6 核心实现

#### 文件结构
```
fund_scraper_mcp/
├── server.py              # MCP Server 主入口
├── browser_manager.py     # 浏览器管理（Playwright）
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py    # 抽象基类
│   └── eastmoney_scraper.py  # 天天基金爬虫实现（唯一数据源）
├── utils/
│   ├── __init__.py
│   └── anti_detection.py  # 反检测策略（UA轮换、延迟等）
├── test_scraper.py        # 功能测试脚本
├── requirements.txt       # Python 依赖
└── README.md
```

#### 核心代码示例

**server.py:**
```python
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
from browser_manager import BrowserManager
from scrapers import EastmoneyScraper

server = Server("fund-scraper")
browser_manager = BrowserManager()

@server.tool()
async def scrape_all_fund_codes() -> dict:
    """获取全量基金代码列表"""
    browser = await browser_manager.get_browser()
    scraper = EastmoneyScraper(browser)
    result = await scraper.scrape_all_fund_codes()
    return result

@server.tool()
async def scrape_fund_list(
    fund_type: str = "all",
    page: int = 1,
    page_size: int = 50
) -> dict:
    """获取基金列表（排行榜）"""
    browser = await browser_manager.get_browser()
    scraper = EastmoneyScraper(browser)
    result = await scraper.scrape_list(
        fund_type=fund_type,
        page=page,
        page_size=page_size
    )
    return result

@server.tool()
async def scrape_fund_detail(symbol: str) -> dict:
    """获取基金详情"""
    browser = await browser_manager.get_browser()
    scraper = EastmoneyScraper(browser)
    result = await scraper.scrape_detail(symbol)
    return result

@server.tool()
async def scrape_fund_nav_history(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = None
) -> dict:
    """获取基金净值历史"""
    browser = await browser_manager.get_browser()
    scraper = EastmoneyScraper(browser)
    result = await scraper.scrape_nav_history(symbol, start_date, end_date, limit)
    return result

@server.tool()
async def scrape_funds_batch(symbols: list, delay: int = 1000) -> dict:
    """批量获取基金详情"""
    browser = await browser_manager.get_browser()
    scraper = EastmoneyScraper(browser)
    result = await scraper.scrape_batch(symbols, delay)
    return result

@server.tool()
async def check_browser_status() -> dict:
    """检查浏览器状态"""
    return await browser_manager.get_status()

if __name__ == "__main__":
    asyncio.run(server.run())
```

**browser_manager.py:**
```python
import asyncio
from playwright.async_api import async_playwright, Browser, Page

class BrowserManager:
    def __init__(self):
        self.browser: Browser = None
        self.playwright = None

    async def get_browser(self) -> Browser:
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                channel='msedge',  # 使用系统 Microsoft Edge
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
        return self.browser

    async def new_page(self) -> Page:
        browser = await self.get_browser()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # 反检测
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        return page

    async def get_status(self) -> dict:
        if self.browser is None:
            return {"connected": False}

        return {
            "connected": self.browser.is_connected(),
            "pages_open": len(self.browser.contexts)
        }

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

**scrapers/eastmoney_scraper.py:**
```python
from .base_scraper import BaseScraper
import re
import json

class EastmoneyScraper(BaseScraper):
    BASE_URL = "https://fund.eastmoney.com"
    
    async def scrape_all_fund_codes(self):
        """获取全量基金代码列表（约20000+只）"""
        page_obj = await self.browser_manager.new_page()
        
        try:
            # 访问全量基金代码JS文件
            response = await page_obj.goto(
                f"{self.BASE_URL}/js/fundcode_search.js",
                wait_until="load"
            )
            
            content = await response.text()
            
            # 解析 var r = [[...], [...], ...];
            match = re.search(r'var r = (\[.*\]);', content, re.DOTALL)
            if match:
                funds_data = json.loads(match.group(1))
                
                # 转换为标准格式
                # 格式: ["000001","HXCZHH","华夏成长混合","混合型-偏股","HUAXIACHENGZHANGHUNHE"]
                funds = []
                for item in funds_data:
                    funds.append({
                        'symbol': item[0],
                        'abbr': item[1],
                        'sname': item[2],
                        'jjlx': item[3],  # 基金类型
                        'pinyin': item[4]
                    })
                
                return {
                    "success": True,
                    "total_count": len(funds),
                    "data": funds
                }
            
            return {"success": False, "error": "无法解析数据"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page_obj.close()
    
    async def scrape_list(self, fund_type="all", page=1, page_size=50):
        page_obj = await self.browser_manager.new_page()
        
        try:
            # 访问基金排行页
            await page_obj.goto(
                f"{self.BASE_URL}/data/fundranking.html",
                wait_until="networkidle"
            )
            
            # 等待表格加载
            await page_obj.wait_for_selector("#dbtable tbody tr")
            
            # 提取数据
            funds = await page_obj.evaluate("""
                () => {
                    const rows = document.querySelectorAll('#dbtable tbody tr');
                    return Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('td');
                        return {
                            symbol: cells[2]?.textContent?.trim() || '',
                            sname: cells[3]?.textContent?.trim() || '',
                            nav_date: cells[4]?.textContent?.trim() || '',
                            per_nav: cells[5]?.textContent?.trim() || '',
                            total_nav: cells[6]?.textContent?.trim() || '',
                            nav_rate: cells[7]?.textContent?.trim() || ''
                        };
                    });
                }
            """)
            
            return {
                "success": True,
                "data": funds,
                "total_count": len(funds)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page_obj.close()
    
    async def scrape_detail(self, symbol):
        page_obj = await self.browser_manager.new_page()
        
        try:
            # 访问基金详情页
            await page_obj.goto(
                f"{self.BASE_URL}/{symbol}.html",
                wait_until="networkidle"
            )
            
            # 提取详情数据
            data = await page_obj.evaluate("""
                () => {
                    const getText = (sel) => document.querySelector(sel)?.textContent?.trim() || '';
                    return {
                        sname: getText('.fundDetail-tit'),
                        per_nav: getText('#gz_gsz') || getText('.dataItem02 .dataNums span:first-child'),
                        total_nav: getText('.dataItem03 .dataNums span:first-child'),
                        nav_rate: getText('#gz_gszzl'),
                        fund_manager: getText('.infoOfFund td:nth-child(1) a'),
                        establishment_date: getText('.infoOfFund td:nth-child(3)'),
                        fund_company: getText('.infoOfFund td:nth-child(4) a')
                    };
                }
            """)
            
            data['symbol'] = symbol
            return {"success": True, "data": data}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page_obj.close()
```

### 1.7 反检测策略

1. **User-Agent 轮换**
   - 维护多个真实浏览器 UA
   - 每次请求随机选择

2. **请求间隔控制**
   - 随机延迟 1-3 秒
   - 批量请求时使用可配置延迟
   - 模拟人类浏览行为

3. **指纹伪装**
   - 隐藏 webdriver 属性
   - 禁用自动化控制标志
   - 模拟真实浏览器环境

4. **Headless 模式**
   - 默认无头模式运行
   - 可通过环境变量切换为有头模式调试

### 1.8 依赖

```txt
# requirements.txt
mcp>=1.0.0
playwright>=1.40.0
```

### 1.9 使用示例

```python
# 获取全量基金代码
all_funds = await mcp_client.call_tool(
    "fund-scraper",
    "scrape_all_fund_codes"
)

# 获取基金排行榜
ranking = await mcp_client.call_tool(
    "fund-scraper",
    "scrape_fund_list",
    {
        "fund_type": "all",
        "page": 1,
        "page_size": 100
    }
)

# 获取单个基金详情
detail = await mcp_client.call_tool(
    "fund-scraper",
    "scrape_fund_detail",
    {"symbol": "000001"}
)

# 获取基金净值历史
nav_history = await mcp_client.call_tool(
    "fund-scraper",
    "scrape_fund_nav_history",
    {
        "symbol": "110022",
        "limit": 30
    }
)

# 批量获取基金详情
batch_details = await mcp_client.call_tool(
    "fund-scraper",
    "scrape_funds_batch",
    {
        "symbols": ["000001", "110022", "161005"],
        "delay": 1000
    }
)
```

### 1.10 实现计划

| 阶段 | 任务 |
|------|------|
| Phase 1 | 基础框架搭建 (MCP Server + Browser Manager) |
| Phase 2 | 实现全量基金代码获取 |
| Phase 3 | 实现基金列表和详情爬虫 |
| Phase 4 | 实现净值历史和批量获取 |
| Phase 5 | 反检测策略优化 |
| Phase 6 | 测试与调试 |

### 1.11 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 网站结构变更 | 爬虫失效 | 模块化设计，易于更新选择器；定期测试 |
| IP被封 | 无法访问 | 降低请求频率，添加延迟，使用代理（可选） |
| 验证码 | 阻断访问 | 检测验证码页面，通知用户；天天基金网通常无验证码 |
| 性能瓶颈 | 速度慢 | 批量获取时控制并发，合理设置延迟 |
| Edge 未安装 | 无法启动 | Windows 通常预装 Edge；其他系统提示安装 |

### 1.12 优势总结

**相比原计划的改进：**
1. ✅ **无需下载浏览器** - 使用系统 Edge，节省 200MB 空间
2. ✅ **更好的兼容性** - Windows 预装 Edge，开箱即用
3. ✅ **维护成本低** - Edge 随系统自动更新
4. ✅ **反检测能力强** - Playwright 原生支持，比 Selenium 更稳定
5. ✅ **代码简洁** - 自动等待机制，减少 99% timing 问题

---

## 2. 后续扩展 Skills

### 2.1 数据缓存 Skill
- 本地缓存已获取的基金数据
- 设置过期时间
- 增量更新机制

### 2.2 数据对比 Skill
- 多源数据交叉验证
- 自动发现数据差异
- 生成数据质量报告

### 2.3 定时任务 Skill
- 每日自动更新基金数据
- 邮件/通知报告
- 异常告警
