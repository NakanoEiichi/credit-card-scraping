from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import time


class CardScraper:
    def __init__(self, db_handler):
        self.db = db_handler
        self.SELENIUM_URL = os.getenv("SELENIUM_URL", "http://localhost:4444/wd/hub")
        self.driver = webdriver.Remote(
            command_executor=self.SELENIUM_URL, options=webdriver.ChromeOptions()
        )
        self.wait = WebDriverWait(self.driver, 10)

    def get_detail_urls(self, url):
        """カード詳細ページのURLを取得"""
        self.driver.get(url)
        detail_urls = []
        # while True:
        for i in range(1):
            elements = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "p-planSearchList_item")
                )
            )
            detail_urls.extend(
                [
                    el.find_element(
                        By.CLASS_NAME, "p-planSearchList_name_link"
                    ).get_attribute("href")
                    for el in elements
                ]
            )

            try:
                next_button = self.driver.find_element(By.CLASS_NAME, "next")
                next_button.click()
                self.wait.until(EC.staleness_of(elements[0]))
            except:
                break
        return detail_urls

    def extract_card_data(self, detail_url):
        """カード詳細情報を抽出"""
        self.driver.get(detail_url)
        time.sleep(5)

        card_id = detail_url.split("id=")[-1]
        base_info_table = self.driver.find_elements(By.CLASS_NAME, "def-tbl1")[0]
        rows = base_info_table.find_elements(By.TAG_NAME, "tr")

        card_name = rows[0].find_element(By.TAG_NAME, "td").text
        official_url = (
            rows[1]
            .find_element(By.TAG_NAME, "td")
            .find_element(By.TAG_NAME, "a")
            .get_attribute("href")
        )
        issuer_id = self.db.fetch_or_insert_id(
            "issuers", "issuer_name", rows[2].find_element(By.TAG_NAME, "td").text
        )
        partner_id = self.db.fetch_or_insert_id(
            "partners", "partner_name", rows[3].find_element(By.TAG_NAME, "td").text
        )

        brand_text = rows[4].find_element(By.TAG_NAME, "td").text
        brands = set(brand_text.split("、"))
        brand_flags = [
            int(brand in brands)
            for brand in [
                "Visa",
                "Mastercard",
                "JCB",
                "AMEX（アメックス）",
                "Diners",
                "銀聯（UnionPay）",
            ]
        ]

        card_data = (
            card_id,
            card_name,
            official_url,
            issuer_id,
            partner_id,
            *brand_flags,
            *[rows[i].find_element(By.TAG_NAME, "td").text for i in range(5, 16)],
        )
        return card_data

    def scrape(self, url):
        """スクレイピングを実行"""
        detail_urls = self.get_detail_urls(url)
        print("scraping")
        for detail_url in detail_urls:
            card_data = self.extract_card_data(detail_url)
            print(card_data)
        #     self.db.insert_or_update_card(card_data)

    def close(self):
        """ブラウザを閉じる"""
        self.driver.quit()
