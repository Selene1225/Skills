"""
爬虫基类
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import asyncio

from browser_manager import BrowserManager
from utils.anti_detection import AntiDetection


class BaseScraper(ABC):
    """爬虫抽象基类"""
    
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
    
    @abstractmethod
    async def scrape_all_fund_codes(self) -> Dict[str, Any]:
        """获取全量基金代码列表"""
        pass
    
    @abstractmethod
    async def scrape_list(
        self,
        fund_type: str = "all",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """获取基金列表（带净值数据）"""
        pass
    
    @abstractmethod
    async def scrape_detail(self, symbol: str) -> Dict[str, Any]:
        """获取单个基金详情"""
        pass
    
    @abstractmethod
    async def scrape_nav_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 30
    ) -> Dict[str, Any]:
        """获取基金净值历史"""
        pass
    
    async def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """随机延迟，模拟人类行为"""
        delay = AntiDetection.get_random_delay(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    def _success_response(self, data: Any, **kwargs) -> Dict[str, Any]:
        """构造成功响应"""
        response = {
            "success": True,
            "data": data
        }
        response.update(kwargs)
        return response
    
    def _error_response(self, error: str) -> Dict[str, Any]:
        """构造错误响应"""
        return {
            "success": False,
            "error": error
        }
