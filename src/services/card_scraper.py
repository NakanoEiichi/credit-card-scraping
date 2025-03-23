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
        print(f"カードURL一覧の取得中: {base_url}")
        self._ensure_driver()
        detail_urls = []

        try:
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

                    for element in card_list_elements:
                        try:
                            link = element.find_element(
                                By.CSS_SELECTOR, ".p-planSearchList_name_link"
                            )
                            url = link.get_attribute("href")
                            if url:
                                detail_urls.append(url)
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
                        time.sleep(3)  # ページ遷移後の待機
                        self.wait.until(EC.staleness_of(card_list_elements[0]))
                    except (NoSuchElementException, TimeoutException):
                        print("次のページボタンが見つからないか、クリックできません")
                        break

                except Exception as e:
                    print(f"ページ処理中にエラーが発生: {str(e)}")
                    break

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
            self.driver.get(url)
            
            # ページの読み込みを待機
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "def-tbl1")))

            kakaku_card_id = url.split("id=")[-1]

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
            point_name = rows[0].find_element(By.TAG_NAME, "td").text
            expires_at = rows[2].find_element(By.TAG_NAME, "td").text
            point_data = {
                "point_name": point_name,
                "expires_at": expires_at,
            }
            point_id = self.db_handler.get_point_id(point_data)
            card_data["point_id"] = point_id
            annual_bonus = rows[11].find_element(By.TAG_NAME, "td").text
            card_data["annual_bonus"] = annual_bonus

            # 追加機能
            tables = self.driver.find_elements(By.CLASS_NAME, "def-tbl1")
            if len(tables) > 1:
                additional_info = tables[1]
                rows = additional_info.find_elements(By.TAG_NAME, "tr")
                first_row_th = rows[0].find_element(By.TAG_NAME, "th")
                if first_row_th.text == "ETCカード":
                    card_data["etc_card"] = rows[1].find_element(By.TAG_NAME, "td").text
                    card_data["family_card"] = rows[2].find_element(By.TAG_NAME, "td").text
                    card_data["electronic_money"] = rows[3].find_element(By.TAG_NAME, "td").text
                    card_data["electronic_money_charge"] = rows[4].find_element(By.TAG_NAME, "td").text
                    card_data["electronic_money_point"] = rows[5].find_element(By.TAG_NAME, "td").text
                    card_data["digital_wallet"] = rows[6].find_element(By.TAG_NAME, "td").text
                    card_data["code_payment"] = rows[7].find_element(By.TAG_NAME, "td").text
                    return card_data
                    
            card_data["etc_card"] = ""
            card_data["family_card"] = ""
            card_data["electronic_money"] = ""
            card_data["electronic_money_charge"] = ""
            card_data["electronic_money_point"] = ""
            card_data["digital_wallet"] = ""
            card_data["code_payment"] = ""
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
        print(f"ポイント還元情報の取得中: {card_id}")
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

                    remarks = ""
                    if len(shop_text) > 1:
                        remarks_number = shop_text[-1].strip()
                        remarks = self.driver.execute_script(
                            "return arguments[0].nextSibling.textContent;",
                            notes[int(remarks_number) - 1],
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
                            "remarks": remarks,
                            "from_kakaku": True,
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

    @retry(
        retry=retry_if_exception_type((WebDriverException, TimeoutException, StaleElementReferenceException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def scrape_point_exchange(self, card_id: int) -> List[Dict[str, Any]]:
        """ポイント交換情報を取得"""
        print(f"ポイント交換情報の取得中: {card_id}")
        exchanges = []
        try:
            point_tables = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".p-rateTbl.p-rateTbl-type2.p-rateTbl01.s-highlightTbl")
                )
            )

            if not point_tables:
                return exchanges

            table = point_tables[0]
            first_header = table.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "tr")[0]
            second_header = table.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "tr")[1]
            third_header = table.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "tr")[2]
            notes = self.driver.find_elements(By.CLASS_NAME, "p-rateNotes_label")

            category_elements = first_header.find_elements(By.CSS_SELECTOR, "th:not(.fixCol)")
            max_th_index = 0
            th_index = 0
            for category_element in category_elements:
                category = category_element.text
                max_th_index += int(category_element.get_attribute("colspan"))
                
                while th_index < max_th_index:
                    reward_name_text = second_header.find_elements(By.TAG_NAME, "th")[th_index].text.split("※")
                    reward_name = reward_name_text[0]
                    remarks = ""
                    if len(reward_name_text) > 1:
                        remarks_number = reward_name_text[-1].strip()
                        remarks = self.driver.execute_script(
                            "return arguments[0].nextSibling.textContent;",
                            notes[int(remarks_number) - 1],
                        ).strip()
                    exchange_rate_str = third_header.find_elements(By.TAG_NAME, "th")[th_index].text.replace(',', '')
                    pattern = r'(\d+)([a-zA-Z\u4e00-\u9fff]+)→(\d+)([a-zA-Z\u4e00-\u9fff]+)'
                    match = re.match(pattern, exchange_rate_str)
                    th_index += 1
                    if match:
                        before_value = int(match.group(1))
                        after_value = int(match.group(3))
                        after_unit = match.group(4)
                        reward = {
                            "category": category,
                            "reward_name": reward_name,
                            "unit": after_unit,
                        }
                        reward_id = self.db_handler.get_reward_id(reward)

                        exchanges.append({
                            "card_id": card_id,
                            "exchangeable_reward_id": reward_id,
                            "before_value": before_value,
                            "after_value": after_value,
                            "remarks": remarks,
                        })
                    else:
                        raise ValueError(f"Invalid exchange rate format: {exchange_rate_str}")
                    
            return exchanges
        except Exception as e:
            print(f"ポイント交換情報の取得中にエラーが発生: {str(e)}")
            self._init_driver()
            self._init_wait()
            raise e
    
    def scrape_include_insurance(self, card_id: int):
        """付帯保険情報を取得"""
        print(f"付帯保険情報の取得中: {card_id}")
        try:
            tables = self.driver.find_elements(By.CLASS_NAME, "def-tbl2")
            if len(tables) < 2:
                print(f"カードID {card_id} の付帯保険情報テーブルが見つかりません")
                return
            insurance_table = tables[-1]
            
            rows = insurance_table.find_elements(By.TAG_NAME, "tr")
            category = ""
            for row in rows:
                # th要素で、かつbd-cell2クラスを持つものを探す
                try:
                    category_th = row.find_element(By.CSS_SELECTOR, "th.bd-cell2")
                    category = category_th.text
                except NoSuchElementException:
                    pass
                
                # th要素で、かつbd-cell2クラスを持っていないものを探す
                coverage_type_th = row.find_element(By.CSS_SELECTOR, "th:not(.bd-cell2)")
                coverage_type = coverage_type_th.text
                if coverage_type == "備考":
                    continue

                coverage_amount = row.find_element(By.TAG_NAME, "td").text
                if coverage_amount == "-":
                    continue
                
                include_insurance_data = {
                    "card_id": card_id,
                    "category": category,
                    "coverage_type": coverage_type,
                    "coverage_amount": coverage_amount,
                    "remarks": "",
                }
                self.db_handler.upsert_include_insurance(include_insurance_data)

        except Exception as e:
            print(f"付帯保険情報の取得中にエラーが発生: {str(e)}")
            self._init_driver()
            self._init_wait()
            raise e

    def scrape_include_services(self, card_id: int):
        """付帯サービス情報を取得"""
        print(f"付帯サービス情報の取得中: {card_id}")
        try:
            tables = self.driver.find_elements(By.CLASS_NAME, "def-tbl1")
            if len(tables) < 3:
                print(f"カードID {card_id} の付帯サービス情報テーブルが見つかりません")
                return
            
            service_table = tables[2]
            rows = service_table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                service_name = row.find_element(By.TAG_NAME, "th").text
                service_content = row.find_element(By.TAG_NAME, "td").text
                
                include_service_data = {
                    "card_id": card_id,
                    "service_name": service_name,
                    "service_content": service_content,
                    "remarks": "",
                }
                self.db_handler.upsert_include_service(include_service_data)

        except Exception as e:
            print(f"付帯サービス情報の取得中にエラーが発生: {str(e)}")
            self._init_driver()
            self._init_wait()
            raise e
        
    def scrape_point_info(self, card_id: int):
        """ポイント情報を取得"""
        print(f"ポイント情報の取得中: {card_id}")
        try:
            point_table = self.driver.find_element(By.CLASS_NAME, "def-tbl2")
            rows = point_table.find_elements(By.TAG_NAME, "tr")
            point_name = rows[0].find_element(By.TAG_NAME, "td").text
            expires_at = rows[2].find_element(By.TAG_NAME, "td").text
            point_info = {
                "point_name": point_name,
                "expires_at": expires_at,
            }
            self.db_handler.upsert_point(point_info)

        except Exception as e:
            print(f"ポイント情報の取得中にエラーが発生: {str(e)}")

    def close(self):
        """ドライバーを終了"""
        if self.driver:
            self.driver.quit()
