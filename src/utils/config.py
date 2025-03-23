import os
from typing import Any
from dotenv import load_dotenv


class Config:
    """環境変数の管理クラス"""

    def __init__(self):
        # .envファイルの読み込み
        load_dotenv()

        # Database settings
        self.MYSQL_HOST = self._get_env("MYSQL_HOST", "localhost")
        self.MYSQL_USER = self._get_env("MYSQL_USER", "user")
        self.MYSQL_PASSWORD = self._get_env("MYSQL_PASSWORD", "password")
        self.MYSQL_DATABASE = self._get_env("MYSQL_DATABASE", "card_db")

        # Google Sheets settings
        self.GOOGLE_SHEETS_SPREADSHEET_ID = self._get_env(
            "GOOGLE_SHEETS_SPREADSHEET_ID"
        )
        self.GOOGLE_APPLICATION_CREDENTIALS = self._get_env(
            "GOOGLE_APPLICATION_CREDENTIALS", "/app/credentials.json"
        )

        # Selenium settings
        self.SELENIUM_URL = self._get_env(
            "SELENIUM_URL", "http://localhost:4444/wd/hub"
        )

        # Scraping settings
        self.SCRAPING_DELAY_MIN = float(self._get_env("SCRAPING_DELAY_MIN", "30"))
        self.SCRAPING_DELAY_MAX = float(self._get_env("SCRAPING_DELAY_MAX", "90"))

    @staticmethod
    def _get_env(key: str, default: Any = None) -> str:
        """環境変数を取得"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Environment variable {key} is not set")
        return value


# シングルトンインスタンスの作成
config = Config()
