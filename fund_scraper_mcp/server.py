"""
Fund Scraper MCP Server
基金数据爬取 MCP 服务

提供的 Tools:
- scrape_all_fund_codes: 获取全量基金代码列表（约20000+只）
- scrape_fund_list: 获取基金排行榜数据（包含净值）
- scrape_fund_detail: 获取单个基金详情
- scrape_fund_nav_history: 获取基金净值历史
- scrape_funds_batch: 批量获取多个基金详情
- fetch_all_funds_info: 一键获取所有基金的完整信息（推荐）
- check_browser_status: 检查浏览器状态
"""
import os
import sys
import asyncio
import json
from typing import Optional, Any

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from browser_manager import BrowserManager
from scrapers.eastmoney_scraper import EastmoneyScraper


# 创建 MCP Server
server = Server("fund-scraper")

# 全局浏览器管理器
browser_manager: Optional[BrowserManager] = None


async def get_browser_manager() -> BrowserManager:
    """获取或创建浏览器管理器"""
    global browser_manager
    if browser_manager is None:
        headless = os.environ.get("HEADLESS", "true").lower() == "true"
        browser_manager = BrowserManager(headless=headless)
        await browser_manager.start()
    return browser_manager


def format_result(result: dict) -> str:
    """格式化返回结果为 JSON 字符串"""
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============== Tools 定义 ==============

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="scrape_all_fund_codes",
            description="获取全量基金代码列表（约20000+只基金），包含代码、名称、类型等基础信息。适合用于获取完整的基金代码清单。",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="scrape_fund_list",
            description="从天天基金排行榜获取基金列表，包含净值、增长率等数据。注意：排行榜可能不包含最新发行的基金。",
            inputSchema={
                "type": "object",
                "properties": {
                    "fund_type": {
                        "type": "string",
                        "description": "基金类型: all(全部), stock(股票型), hybrid(混合型), bond(债券型), index(指数型), qdii, money(货币型), fof",
                        "default": "all"
                    },
                    "page": {
                        "type": "integer",
                        "description": "页码，从1开始",
                        "default": 1
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "每页数量",
                        "default": 50
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="scrape_fund_detail",
            description="获取单个基金的详细信息，包括净值、基金经理、规模、成立日期等全部字段。",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "基金代码，如 000001"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="scrape_fund_nav_history",
            description="获取基金的净值历史数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "基金代码，如 000001"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "开始日期，格式 YYYY-MM-DD",
                        "default": None
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式 YYYY-MM-DD",
                        "default": None
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数限制",
                        "default": 30
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="scrape_funds_batch",
            description="批量获取多个基金的详情数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "基金代码列表，如 ['000001', '000002']"
                    }
                },
                "required": ["symbols"]
            }
        ),
        Tool(
            name="fetch_all_funds_info",
            description="一键获取所有基金的完整信息（推荐使用）。返回包含12个字段的完整数据，与新浪数据格式兼容。注意：此操作耗时较长（约需数小时），建议先用max_funds参数测试。",
            inputSchema={
                "type": "object",
                "properties": {
                    "batch_size": {
                        "type": "integer",
                        "description": "每批处理的基金数量",
                        "default": 100
                    },
                    "max_funds": {
                        "type": "integer",
                        "description": "最多获取的基金数量（用于测试，null表示全部）",
                        "default": None
                    },
                    "delay": {
                        "type": "number",
                        "description": "每个请求之间的延迟（秒）",
                        "default": 1.0
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="check_browser_status",
            description="检查浏览器连接状态",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    
    try:
        bm = await get_browser_manager()
        scraper = EastmoneyScraper(bm)
        
        if name == "scrape_all_fund_codes":
            result = await scraper.scrape_all_fund_codes()
            
        elif name == "scrape_fund_list":
            fund_type = arguments.get("fund_type", "all")
            page = arguments.get("page", 1)
            page_size = arguments.get("page_size", 50)
            result = await scraper.scrape_list(fund_type, page, page_size)
            
        elif name == "scrape_fund_detail":
            symbol = arguments.get("symbol")
            if not symbol:
                result = {"success": False, "error": "缺少必需参数: symbol"}
            else:
                result = await scraper.scrape_detail(symbol)
                
        elif name == "scrape_fund_nav_history":
            symbol = arguments.get("symbol")
            if not symbol:
                result = {"success": False, "error": "缺少必需参数: symbol"}
            else:
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                limit = arguments.get("limit", 30)
                result = await scraper.scrape_nav_history(symbol, start_date, end_date, limit)
                
        elif name == "scrape_funds_batch":
            symbols = arguments.get("symbols")
            if not symbols:
                result = {"success": False, "error": "缺少必需参数: symbols"}
            else:
                result = await scraper.scrape_funds_batch(symbols)

        elif name == "fetch_all_funds_info":
            batch_size = arguments.get("batch_size", 100)
            max_funds = arguments.get("max_funds")
            delay = arguments.get("delay", 1.0)
            result = await scraper.fetch_all_funds_info(batch_size, max_funds, delay)

        elif name == "check_browser_status":
            result = await bm.get_status()

        else:
            result = {"success": False, "error": f"未知工具: {name}"}
        
        return [TextContent(type="text", text=format_result(result))]
        
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        return [TextContent(type="text", text=format_result(error_result))]


async def cleanup():
    """清理资源"""
    global browser_manager
    if browser_manager:
        await browser_manager.close()
        browser_manager = None


async def main():
    """主函数"""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())


def main_sync():
    """同步入口函数，供 pip install 后命令行调用"""
    asyncio.run(main())
