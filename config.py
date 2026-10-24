import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    UPLOAD_FOLDER = "data"
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024   # 100 MB (image uploads)

    # CELF endpoints
    BASE_URL          = "https://celfonline.org"          # adjust to real domain
    LOGIN_URL         = f"{BASE_URL}/celf/index.php?r=site/login"
    CHURCH_REPORT_URL = f"{BASE_URL}/celf/index.php?r=reporting/AddReport"
    CELL_REPORT_URL   = f"{BASE_URL}/celf/index.php?r=CellReporting/index2"

    # Automation
    MAX_CONCURRENT_ACCOUNTS = 5
    NAVIGATION_TIMEOUT = 30_000
    ACTION_TIMEOUT = 15_000
    HEADLESS = True