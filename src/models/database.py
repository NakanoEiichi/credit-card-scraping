import os
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self) -> None:
        """データベースに接続"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "mysql"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "root"),
                database=os.getenv("MYSQL_DATABASE", "card_db"),
                port=int(os.getenv("MYSQL_PORT", "3306")),
                connect_timeout=60,
                pool_size=5,
                pool_reset_session=True
            )
            print("データベース接続成功")
        except Error as e:
            print(f"データベース接続エラー: {e}")
            raise

    def reconnect(self) -> None:
        """データベース接続を再確立"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
            self.connect()
            print("データベース再接続成功")
        except Error as e:
            print(f"データベース再接続エラー: {e}")
            raise

    def _ensure_connection(self) -> None:
        """接続が有効か確認し、必要に応じて再接続"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.reconnect()
        except Error as e:
            print(f"接続確認エラー: {e}")
            raise

    def get_issuer_id(self, name: str) -> int:
        """発行会社IDを取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM issuers WHERE issuer_name = %s", (name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute("INSERT INTO issuers (issuer_name) VALUES (%s)", (name,))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"発行会社ID取得エラー: {e}")
            self.reconnect()
            return self.get_issuer_id(name)

    def get_partner_id(self, name: str) -> int:
        """提携会社IDを取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM partners WHERE partner_name = %s", (name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute("INSERT INTO partners (partner_name) VALUES (%s)", (name,))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"提携会社ID取得エラー: {e}")
            self.reconnect()
            return self.get_partner_id(name)

    def get_card_id(self, kakaku_card_id: str) -> Optional[int]:
        """カードIDを取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id FROM cards WHERE kakaku_card_id = %s", (kakaku_card_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            print(f"カードID取得エラー: {e}")
            self.reconnect()
            return self.get_card_id(kakaku_card_id)
    
    def get_shop_id(self, shop_data: Dict[str, Any]) -> int:
        """ショップIDを取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM shops WHERE shop_name = %s AND is_online = %s AND category = %s", (shop_data["shop_name"], shop_data["is_online"], shop_data["category"]))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                cursor.execute("INSERT INTO shops (shop_name, is_online, category) VALUES (%s, %s, %s)", (shop_data["shop_name"], shop_data["is_online"], shop_data["category"]))
                self.connection.commit()
                return cursor.lastrowid
        except Error as e:
            print(f"ショップID取得エラー: {e}")
            self.reconnect()
            return self.get_shop_id(shop_data)

    def upsert_card(self, card_data: Dict[str, Any]) -> int:
        """カード情報を更新または挿入"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO cards (
                    kakaku_card_id, card_name, official_url, grade, issuer_id, partner_id,
                    visa, mastercard, jcb, amex, diners, unionpay,
                    eligibility, application_method, screening_period,
                    annual_fee, shopping_limit, cashing_limit,
                    revolving_interest_rate, cashing_interest_rate,
                    payment_methods, closing_date, remarks, annual_bonus
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    card_name = VALUES(card_name),
                    official_url = VALUES(official_url),
                    grade = VALUES(grade),
                    issuer_id = VALUES(issuer_id),
                    partner_id = VALUES(partner_id),
                    visa = VALUES(visa),
                    mastercard = VALUES(mastercard),
                    jcb = VALUES(jcb),
                    amex = VALUES(amex),
                    diners = VALUES(diners),
                    unionpay = VALUES(unionpay),
                    eligibility = VALUES(eligibility),
                    application_method = VALUES(application_method),
                    screening_period = VALUES(screening_period),
                    annual_fee = VALUES(annual_fee),
                    shopping_limit = VALUES(shopping_limit),
                    cashing_limit = VALUES(cashing_limit),
                    revolving_interest_rate = VALUES(revolving_interest_rate),
                    cashing_interest_rate = VALUES(cashing_interest_rate),
                    payment_methods = VALUES(payment_methods),
                    closing_date = VALUES(closing_date),
                    remarks = VALUES(remarks),
                    annual_bonus = VALUES(annual_bonus)
                """,
                (
                    card_data["kakaku_card_id"],
                    card_data["card_name"],
                    card_data["official_url"],
                    card_data["grade"],
                    card_data["issuer_id"],
                    card_data["partner_id"],
                    card_data["visa"],
                    card_data["mastercard"],
                    card_data["jcb"],
                    card_data["amex"],
                    card_data["diners"],
                    card_data["unionpay"],
                    card_data["eligibility"],
                    card_data["application_method"],
                    card_data["screening_period"],
                    card_data["annual_fee"],
                    card_data["shopping_limit"],
                    card_data["cashing_limit"],
                    card_data["revolving_interest_rate"],
                    card_data["cashing_interest_rate"],
                    card_data["payment_methods"],
                    card_data["closing_date"],
                    card_data["remarks"],
                    card_data["annual_bonus"],
                ),
            )
            self.connection.commit()
            
            # 挿入または更新されたカードのIDを取得
            cursor.execute("SELECT id FROM cards WHERE kakaku_card_id = %s", (card_data["kakaku_card_id"],))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            print(f"カード情報更新エラー: {e}")
            self.reconnect()
            return self.upsert_card(card_data)
        
    def upsert_point_reward(self, point_reward_data: Dict[str, Any]) -> None:
        """ポイント還元情報を更新または挿入"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO point_rewards (
                    card_id, shop_id, spending_amount, points, condition_raw
                ) VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    spending_amount = VALUES(spending_amount),
                    points = VALUES(points),
                    condition_raw = VALUES(condition_raw)
                """,
                (
                    point_reward_data["card_id"],
                    point_reward_data["shop_id"],
                    point_reward_data["spending_amount"],
                    point_reward_data["points"],
                    point_reward_data["condition_raw"],
                ),
            )
            self.connection.commit()
        except Error as e:
            print(f"ポイント還元情報更新エラー: {e}")
            self.reconnect()
            return self.upsert_point_reward(point_reward_data)

    def get_all_issuers(self) -> List[Dict[str, Any]]:
        """全ての発行会社情報を取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM issuers")
            return cursor.fetchall()
        except Error as e:
            print(f"発行会社情報取得エラー: {e}")
            self.reconnect()
            return self.get_all_issuers()

    def get_all_partners(self) -> List[Dict[str, Any]]:
        """全ての提携会社情報を取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM partners")
            return cursor.fetchall()
        except Error as e:
            print(f"提携会社情報取得エラー: {e}")
            self.reconnect()
            return self.get_all_partners()

    def get_all_cards(self) -> List[Dict[str, Any]]:
        """全てのカード情報を取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM cards")
            return cursor.fetchall()
        except Error as e:
            print(f"カード情報取得エラー: {e}")
            self.reconnect()
            return self.get_all_cards()

    def get_all_point_rewards(self) -> List[Dict[str, Any]]:
        """全てのポイント還元情報を取得"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM point_rewards")
            return cursor.fetchall()
        except Error as e:
            print(f"ポイント還元情報取得エラー: {e}")
            self.reconnect()
            return self.get_all_point_rewards()

    def insert_point_reward(self, reward_data: Dict[str, Any]) -> None:
        """ポイント還元情報を挿入"""
        self._ensure_connection()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO point_rewards (
                    card_id, category, shop, spending_amount, points, remarks
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    reward_data["card_id"],
                    reward_data["category"],
                    reward_data["shop"],
                    reward_data["spending_amount"],
                    reward_data["points"],
                    reward_data["remarks"],
                ),
            )
            self.connection.commit()
        except Error as e:
            print(f"ポイント還元情報挿入エラー: {e}")
            self.reconnect()
            self.insert_point_reward(reward_data)

    def close(self) -> None:
        """データベース接続を閉じる"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("データベース接続を閉じました")
