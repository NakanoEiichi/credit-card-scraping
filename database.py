import os
import mysql.connector
import traceback


class DatabaseHandler:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "user"),
            password=os.getenv("MYSQL_PASSWORD", "password"),
            database=os.getenv("MYSQL_DATABASE", "card_db"),
        )
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=None, commit=False):
        """SQLクエリを実行"""
        try:
            self.cursor.execute(query, params)
            if commit:
                self.conn.commit()
        except mysql.connector.Error as e:
            print(f"[ERROR] MySQL クエリ実行エラー: {e}")
            print(traceback.format_exc())

    def fetch_or_insert_id(self, table, column, value):
        """発行会社や提携会社のIDを取得、なければ追加"""
        query_select = f"SELECT id FROM {table} WHERE {column} = %s"
        self.execute_query(query_select, (value,))
        row = self.cursor.fetchone()

        if row is None:
            query_insert = f"INSERT INTO {table} ({column}) VALUES (%s)"
            self.execute_query(query_insert, (value,), commit=True)
            return self.cursor.lastrowid
        return row[0]

    def insert_or_update_card(self, card_data):
        """カード情報をUPSERT"""
        query = """
        INSERT INTO cards (
            card_id, card_name, official_url, issuer_id, partner_id,
            visa, mastercard, jcb, amex, diners, unionpay,
            eligibility, application_method, screening_period, annual_fee, shopping_limit, cashing_limit,
            revolving_interest_rate, cashing_interest_rate, payment_methods, closing_date, remarks
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            card_name=VALUES(card_name), official_url=VALUES(official_url),
            issuer_id=VALUES(issuer_id), partner_id=VALUES(partner_id),
            visa=VALUES(visa), mastercard=VALUES(mastercard), jcb=VALUES(jcb),
            amex=VALUES(amex), diners=VALUES(diners), unionpay=VALUES(unionpay),
            eligibility=VALUES(eligibility), application_method=VALUES(application_method),
            screening_period=VALUES(screening_period), annual_fee=VALUES(annual_fee), 
            shopping_limit=VALUES(shopping_limit), cashing_limit=VALUES(cashing_limit), 
            revolving_interest_rate=VALUES(revolving_interest_rate), 
            cashing_interest_rate=VALUES(cashing_interest_rate), payment_methods=VALUES(payment_methods),
            closing_date=VALUES(closing_date), remarks=VALUES(remarks);
        """
        self.execute_query(query, card_data, commit=True)

    def close(self):
        """データベース接続を閉じる"""
        self.cursor.close()
        self.conn.close()
