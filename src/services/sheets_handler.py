import os
from typing import List, Any, Dict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

class SheetsHandler:
    def __init__(self):
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        self.credentials = self._get_credentials()
        self.service = build("sheets", "v4", credentials=self.credentials)
        self._init_sheets()

    def _get_credentials(self) -> Credentials:
        """認証情報を取得"""
        try:
            credentials_path = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
            return service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        except Exception as e:
            print(f"認証情報取得エラー: {e}")
            raise

    def _init_sheets(self):
        """シートの初期化とヘッダーの設定"""
        # シートのクリア
        self._clear_sheet("issuers")
        self._clear_sheet("partners")
        self._clear_sheet("cards")
        self._clear_sheet("point_rewards")

        # ヘッダーの設定
        self._write_data("issuers", [["issuer_id", "issuer_name"]])
        self._write_data("partners", [["partner_id", "partner_name"]])
        self._write_data("cards", [[
            "card_id",
            "kakaku_com_card_id",
            "card_name",
            "official_url",
            "grade",
            "issuer_id",
            "partner_id",
            "visa",
            "mastercard",
            "jcb",
            "amex",
            "diners",
            "unionpay",
            "eligibility",
            "application_method",
            "screening_period",
            "annual_fee",
            "shopping_limit",
            "cashing_limit",
            "revolving_interest_rate",
            "cashing_interest_rate",
            "payment_methods",
            "closing_date",
            "annual_bonus",
            "remarks",
            "detail_url",
        ]])
        self._write_data("point_rewards", [[
            "card_id",
            "category",
            "shop",
            "spending_amount",
            "points",
            "remarks"
        ]])

    def _clear_sheet(self, sheet_name: str):
        """シートをクリア"""
        range_name = f"{sheet_name}!A:Z"
        self.service.spreadsheets().values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()

    def _write_data(self, sheet_name: str, data: List[List[Any]]):
        """データを書き込む"""
        if not data:
            return

        range_name = f"{sheet_name}!A1"
        body = {
            "values": data
        }
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()

    def batch_update(self, db_handler):
        """DBからデータを取得してスプレッドシートを一括更新"""
        # 発行会社の更新
        issuers_data = db_handler.get_all_issuers()
        self._write_data(
            "issuers",
            [["issuer_id", "issuer_name"]]  # ヘッダー
            + [[issuer["issuer_id"], issuer["issuer_name"]] for issuer in issuers_data]
        )

        # 提携会社の更新
        partners_data = db_handler.get_all_partners()
        self._write_data(
            "partners",
            [["partner_id", "partner_name"]]  # ヘッダー
            + [[partner["partner_id"], partner["partner_name"]] for partner in partners_data]
        )

        # カード情報の更新
        cards_data = db_handler.get_all_cards()
        self._write_data(
            "cards",
            [[
                "card_id",
                "kakaku_com_card_id",
                "card_name",
                "official_url",
                "grade",
                "issuer_id",
                "partner_id",
                "visa",
                "mastercard",
                "jcb",
                "amex",
                "diners",
                "unionpay",
                "eligibility",
                "application_method",
                "screening_period",
                "annual_fee",
                "shopping_limit",
                "cashing_limit",
                "revolving_interest_rate",
                "cashing_interest_rate",
                "payment_methods",
                "closing_date",
                "annual_bonus",
                "remarks",
                "detail_url",
            ]]  # ヘッダー
            + [[
                card["id"],
                card["card_id"],
                card["card_name"],
                card["official_url"],
                "",
                card["issuer_id"],
                card["partner_id"],
                card["visa"],
                card["mastercard"],
                card["jcb"],
                card["amex"],
                card["diners"],
                card["unionpay"],
                card["eligibility"],
                card["application_method"],
                card["screening_period"],
                card["annual_fee"],
                card["shopping_limit"],
                card["cashing_limit"],
                card["revolving_interest_rate"],
                card["cashing_interest_rate"],
                card["payment_methods"],
                card["closing_date"],
                card["annual_bonus"],
                card["remarks"],
                "",
            ] for card in cards_data]
        )

        # ポイント還元情報の更新
        rewards_data = db_handler.get_all_point_rewards()
        self._write_data(
            "point_rewards",
            [["card_id", "category", "shop", "spending_amount", "points", "remarks"]]  # ヘッダー
            + [[
                reward["card_id"],
                reward["category"],
                reward["shop"],
                reward["spending_amount"],
                reward["points"],
                reward["remarks"],
            ] for reward in rewards_data]
        )
