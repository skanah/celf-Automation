from playwright.async_api import Page
from config import Config


class AccountSession:
    """One logged-in CELF account with its own browser context."""

    def __init__(self, account_id: str, username: str, password: str):
        self.account_id = account_id
        self.username = username
        self.password = password
        self.context = None
        self.page: Page | None = None
        self.logged_in = False

    async def login(self, browser_pool, log=print) -> bool:
        self.context = await browser_pool.new_context()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(Config.ACTION_TIMEOUT)
        self.page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)

        log(f"[{self.account_id}] → login page")
        await self.page.goto(Config.LOGIN_URL, wait_until="networkidle")

        # ---- Adjust selectors to real CELF login form ----
        await self.page.fill('input[name="LoginForm[username]"]', self.username)
        await self.page.fill('input[name="LoginForm[password]"]', self.password)
        await self.page.click('button[type="submit"], input[type="submit"]')

        try:
            await self.page.wait_for_load_state("networkidle")
            # Detect success (presence of logout link or dashboard marker)
            if await self.page.locator('a:has-text("Logout"), a[href*="logout"]').count() > 0 \
               or "site/login" not in self.page.url:
                self.logged_in = True
                log(f"[{self.account_id}] ✅ Logged in as {self.username}")
                return True
        except Exception as e:
            log(f"[{self.account_id}] login check failed: {e}")

        log(f"[{self.account_id}] ❌ Login failed")
        self.logged_in = False
        return False

    async def close(self):
        if self.context:
            await self.context.close()
        self.logged_in = False