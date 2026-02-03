"""
浏览器管理器
使用 Playwright 控制 Microsoft Edge 浏览器
"""
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from utils.anti_detection import AntiDetection


class BrowserManager:
    """浏览器管理器 - 管理 Microsoft Edge 浏览器实例"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def start(self) -> None:
        """启动浏览器"""
        if self._browser is not None:
            return
        
        self._playwright = await async_playwright().start()
        
        # 启动 Edge 浏览器（使用系统已安装的 Edge，无需下载 Chromium）
        self._browser = await self._playwright.chromium.launch(
            channel='msedge',  # 使用系统 Microsoft Edge
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-gpu',
                '--window-size=1920,1080',
            ]
        )
        
        # 创建浏览器上下文
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=AntiDetection.get_random_user_agent(),
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        
        # 添加反检测脚本
        for script in AntiDetection.get_stealth_scripts():
            await self._context.add_init_script(script)
    
    async def get_browser(self) -> Browser:
        """获取浏览器实例"""
        if self._browser is None:
            await self.start()
        return self._browser
    
    async def new_page(self) -> Page:
        """创建新页面"""
        if self._context is None:
            await self.start()
        
        page = await self._context.new_page()
        return page
    
    async def get_status(self) -> dict:
        """获取浏览器状态"""
        if self._browser is None:
            return {
                "connected": False,
                "message": "浏览器未启动"
            }
        
        try:
            is_connected = self._browser.is_connected()
            pages_count = len(self._context.pages) if self._context else 0
            
            return {
                "connected": is_connected,
                "pages_open": pages_count,
                "headless": self.headless,
                "message": "浏览器运行正常" if is_connected else "浏览器连接断开"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def close(self) -> None:
        """关闭浏览器"""
        try:
            if self._context:
                try:
                    await self._context.close()
                except Exception:
                    pass
                self._context = None
            
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None
            
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
        except Exception:
            pass
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
