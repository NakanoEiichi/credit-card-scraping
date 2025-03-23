import os
import time
import re
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, StaleElementReferenceException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from models.database import DatabaseHandler
from services.sheets_handler import SheetsHandler


class CardScraper:
    def __init__(self, db_handler: DatabaseHandler, sheets_handler: SheetsHandler):
        self.db_handler = db_handler
        self.sheets_handler = sheets_handler
        self.driver = None
        self.wait = None
        self._init_driver()
        self._init_wait()

    def _init_driver(self):
        """Selenium WebDriverを初期化"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Remote(
                command_executor=os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub"),
                options=chrome_options
            )
        except Exception as e:
            print(f"WebDriver初期化エラー: {e}")
            self.driver = None
            self.wait = None
            raise

    def _init_wait(self) -> None:
        """WebDriverWaitの初期化"""
        self.wait = WebDriverWait(self.driver, 20)

    def _ensure_driver(self) -> None:
        """ドライバーの状態を確認し、必要に応じて再初期化"""
        try:
            self.driver.current_url
        except (WebDriverException, AttributeError):
            self._init_driver()
            self._init_wait()

    @retry(
        retry=retry_if_exception_type((WebDriverException, TimeoutException, StaleElementReferenceException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def get_card_urls(self, base_url: str, max_pages: int = 5) -> List[str]:
        """カード詳細ページのURL一覧を取得"""
        self._ensure_driver()
        detail_urls = []

        try:
            print(f"ページにアクセス: {base_url}")
            self.driver.get(base_url)
            
            # ページの読み込みを待機
            time.sleep(5)
            
            # 検索結果の表示を待機
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "p-planSearchList"))
                )
            except TimeoutException:
                print("検索結果が見つかりません。ページを再読み込みします。")
                self.driver.refresh()
                time.sleep(5)
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "p-planSearchList"))
                )

            for _ in range(max_pages):
                try:
                    # カードリストの要素を待機
                    card_list_elements = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, ".p-planSearchList_item")
                        )
                    )
                    print(f"カードリスト要素を取得: {len(card_list_elements)}件")

                    for element in card_list_elements:
                        try:
                            link = element.find_element(
                                By.CSS_SELECTOR, ".p-planSearchList_name_link"
                            )
                            url = link.get_attribute("href")
                            if url:
                                detail_urls.append(url)
                                print(f"URLを追加: {url}")
                        except NoSuchElementException:
                            print("リンク要素が見つかりません")
                            continue

                    # 次のページボタンを探す
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, ".next")
                        if not next_button.is_displayed():
                            print("次のページボタンが表示されていません")
                            break
                        next_button.click()
                        print("次のページに移動")
                        time.sleep(3)  # ページ遷移後の待機
                        self.wait.until(EC.staleness_of(card_list_elements[0]))
                    except (NoSuchElementException, TimeoutException):
                        print("次のページボタンが見つからないか、クリックできません")
                        break

                except Exception as e:
                    print(f"ページ処理中にエラーが発生: {str(e)}")
                    break

            print(f"合計URL数: {len(detail_urls)}")
            return detail_urls

        except Exception as e:
            print(f"URL取得中にエラーが発生: {str(e)}")
            self._init_driver()
            self._init_wait()
            raise e

    @retry(
        retry=retry_if_exception_type((WebDriverException, TimeoutException, StaleElementReferenceException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def scrape_card_detail(self, url: str) -> Dict[str, Any]:
        """カード詳細ページから情報を取得"""
        self._ensure_driver()

        try:
            print(f"カード詳細ページにアクセス: {url}")
            self.driver.get(url)
            
            # ページの読み込みを待機
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "def-tbl1")))
            print("基本情報テーブルを検出")

            kakaku_card_id = url.split("id=")[-1]
            print(f"カードID: {kakaku_card_id}")

            # グレード情報の取得
            grade_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".menu-list3 .icon2"))
            )
            grade = grade_element.text.replace("カードランキング", "")

            # 基本情報テーブルの取得
            base_info = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "def-tbl1"))
            )
            rows = base_info.find_elements(By.TAG_NAME, "tr")

            # 基本情報の取得
            card_data = {
                "kakaku_card_id": kakaku_card_id,
                "card_name": rows[0].find_element(By.TAG_NAME, "td").text,
                "official_url": rows[1]
                .find_element(By.TAG_NAME, "td")
                .find_element(By.TAG_NAME, "a")
                .get_attribute("href"),
                "grade": grade,
            }
            print(f"カード名: {card_data['card_name']}")

            # 発行会社と提携会社の処理
            issuer_name = rows[2].find_element(By.TAG_NAME, "td").text
            partner_name = rows[3].find_element(By.TAG_NAME, "td").text

            # データベース接続を確認し、必要に応じて再接続
            try:
                card_data["issuer_id"] = self.db_handler.get_issuer_id(issuer_name)
                card_data["partner_id"] = self.db_handler.get_partner_id(partner_name)
                print(f"発行会社ID: {card_data['issuer_id']}, 提携会社ID: {card_data['partner_id']}")
            except Exception as e:
                print(f"データベース接続エラー: {str(e)}")
                self.db_handler.reconnect()  # データベース接続を再確立
                card_data["issuer_id"] = self.db_handler.get_issuer_id(issuer_name)
                card_data["partner_id"] = self.db_handler.get_partner_id(partner_name)

            # ブランド情報の処理
            brands = rows[4].find_element(By.TAG_NAME, "td").text.split("、")
            card_data.update(
                {
                    "visa": "Visa" in brands,
                    "mastercard": "Mastercard" in brands,
                    "jcb": "JCB" in brands,
                    "amex": "AMEX（アメックス）" in brands,
                    "diners": "Diners" in brands,
                    "unionpay": "銀聯（UnionPay）" in brands,
                }
            )
            print(f"対応ブランド: {', '.join(brands)}")

            # その他の情報
            card_data.update(
                {
                    "eligibility": rows[5].find_element(By.TAG_NAME, "td").text,
                    "application_method": rows[6].find_element(By.TAG_NAME, "td").text,
                    "screening_period": rows[7].find_element(By.TAG_NAME, "td").text,
                    "annual_fee": rows[8].find_element(By.TAG_NAME, "td").text,
                    "shopping_limit": rows[9].find_element(By.TAG_NAME, "td").text,
                    "cashing_limit": rows[10].find_element(By.TAG_NAME, "td").text,
                    "revolving_interest_rate": rows[11]
                    .find_element(By.TAG_NAME, "td")
                    .text,
                    "cashing_interest_rate": rows[12].find_element(By.TAG_NAME, "td").text,
                    "payment_methods": rows[13].find_element(By.TAG_NAME, "td").text,
                    "closing_date": rows[14].find_element(By.TAG_NAME, "td").text,
                    "remarks": rows[15].find_element(By.TAG_NAME, "td").text,
                }
            )

            # ポイント還元情報の取得
            point_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "def-tbl2"))
            )
            rows = point_table.find_elements(By.TAG_NAME, "tr")
            annual_bonus = rows[11].find_element(By.TAG_NAME, "td").text
            card_data["annual_bonus"] = annual_bonus
            print(f"年間ボーナス: {annual_bonus}")

            return card_data

        except Exception as e:
            print(f"カード詳細の取得中にエラーが発生: {str(e)}")
            self._init_driver()
            self._init_wait()
            raise e

    @retry(
        retry=retry_if_exception_type((WebDriverException, TimeoutException, StaleElementReferenceException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def scrape_point_rewards(self, card_id: int) -> List[Dict[str, Any]]:
        """ポイント還元情報を取得"""
        rewards = []
        try:
            point_tables = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".p-rateTbl.p-rateTbl-type2.p-rateTbl01.s-highlightTbl")
                )
            )

            if not point_tables:
                return rewards

            table = point_tables[0]
            rows = table.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
            notes = self.driver.find_elements(By.CLASS_NAME, "p-rateNotes_label")

            category = ""
            for row in rows:
                try:
                    th = row.find_element(By.TAG_NAME, "th")
                    classes = set(th.get_attribute("class").split())

                    if {"p-rateTbl_label", "p-rateTbl_labelParent", "fixCol"}.issubset(classes):
                        category = th.get_attribute("textContent").strip()
                        continue

                    shop_text = th.get_attribute("title").split("※")
                    shop = shop_text[0]
                    shop_data = {
                        "shop_name": shop,
                        "is_online": category == "ECサイト",
                        "category": category,
                    }
                    shop_id = self.db_handler.get_shop_id(shop_data)

                    condition_raw = ""
                    if len(shop_text) > 1:
                        condition_number = shop_text[-1].strip()
                        condition_raw = self.driver.execute_script(
                            "return arguments[0].nextSibling.textContent;",
                            notes[int(condition_number) - 1],
                        ).strip()

                    td = row.find_element(By.XPATH, ".//td")
                    rewards_text = td.get_attribute("textContent").strip()
                    numbers = re.findall(r"\d+,?\d*", rewards_text)

                    amount = int(numbers[0].replace(",", ""))
                    points = int(numbers[1])

                    rewards.append(
                        {
                            "card_id": card_id,
                            "shop_id": shop_id,
                            "spending_amount": amount,
                            "points": points,
                            "condition_raw": condition_raw,
                        }
                    )
                except Exception as e:
                    print(f"ポイント還元情報の行処理中にエラーが発生: {str(e)}")
                    continue

            return rewards

        except Exception as e:
            print(f"ポイント還元情報の取得中にエラーが発生: {str(e)}")
            self._init_driver()
            self._init_wait()
            raise e

    def close(self):
        """ドライバーを終了"""
        if self.driver:
            self.driver.quit()
