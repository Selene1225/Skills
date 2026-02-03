"""
反检测策略
"""
import random

class AntiDetection:
    """反爬虫检测工具类"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    
    @classmethod
    def get_random_user_agent(cls) -> str:
        """获取随机 User-Agent"""
        return random.choice(cls.USER_AGENTS)
    
    @classmethod
    def get_random_delay(cls, min_sec: float = 1.0, max_sec: float = 3.0) -> float:
        """获取随机延迟时间（秒）"""
        return random.uniform(min_sec, max_sec)
    
    @classmethod
    def get_stealth_scripts(cls) -> list:
        """获取反检测 JavaScript 脚本"""
        return [
            # 隐藏 webdriver 属性
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            # 模拟真实的 plugins
            """
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            """,
            # 模拟真实的语言
            """
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            """,
            # 隐藏自动化标志
            """
            window.chrome = { runtime: {} };
            """,
        ]
