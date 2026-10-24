from playwright.async_api import async_playwright, Browser
from config import Config

class BrowserPool:
    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )

    async def new_context(self):
        if not self.browser:
            await self.start()
        return await self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


browser_pool = BrowserPool()