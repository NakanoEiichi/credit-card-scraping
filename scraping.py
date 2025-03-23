from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import gspread
from google.oauth2.service_account import Credentials
import mysql.connector
import traceback
import re
import time
from requests.exceptions import ConnectionError

# Google Sheets API の設定
SPREADSHEET_ID = "11F5a2l0hFWhJeYphjXMOk03d5KU8e-Ms36GFckWdOVo"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 認証情報の設定
creds = Credentials.from_service_account_file("/app/credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

# スプレッドシートを開く
spreadsheet = client.open_by_key(SPREADSHEET_ID)
issuers_sheet = spreadsheet.worksheet("issuers")
partners_sheet = spreadsheet.worksheet("partners")
cards_sheet = spreadsheet.worksheet("cards")
point_rewards_sheet = spreadsheet.worksheet("point_rewards")

# **シートを初期化（データを削除）**
issuers_sheet.clear()
partners_sheet.clear()
cards_sheet.clear()
point_rewards_sheet.clear()

# シートのヘッダーを設定（初回実行時）
if not issuers_sheet.row_values(1):
    issuers_sheet.append_row(["issuer_id", "issuer_name"])
if not partners_sheet.row_values(1):
    partners_sheet.append_row(["partner_id", "partner_name"])
if not cards_sheet.row_values(1):
    cards_sheet.append_row(
        [
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
            "remarks",
            "detail_url",
        ]
    )
if not point_rewards_sheet.row_values(1):
    point_rewards_sheet.append_row(
        ["card_id", "category", "shop", "amount", "points", "remarks"]
    )

# 発行会社のリストを取得（{発行会社名: issuer_id} の辞書形式）
issuers_data = issuers_sheet.get_all_records()
issuer_dict = {row["issuer_name"]: row["issuer_id"] for row in issuers_data}
partners_data = partners_sheet.get_all_records()
partner_dict = {row["partner_name"]: row["partner_id"] for row in partners_data}

# Selenium の設定
SELENIUM_URL = os.getenv("SELENIUM_URL", "http://localhost:4444/wd/hub")
url = "https://kakaku.com/card/ranking/"

# MySQL の接続情報
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "card_db")

# MySQL に接続
conn = mysql.connector.connect(
    host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE
)
cursor = conn.cursor()

try:
    driver = webdriver.Remote(
        command_executor=SELENIUM_URL, options=webdriver.ChromeOptions()
    )

    wait = WebDriverWait(driver, 10)
    driver.get(url)

    detail_urls = []

    # while True:
    for i in range(5):
        # while True:
        card_list_elements = wait.until(
            EC.presence_of_all_elements_located(
                (By.CLASS_NAME, "p-planSearchList_item")
            )
        )

        for card_list_element in card_list_elements:
            try:
                link_element = card_list_element.find_element(
                    By.CLASS_NAME, "p-planSearchList_name_link"
                )
                detail_url = link_element.get_attribute("href")
                detail_urls.append(detail_url)
            except:
                continue

        try:
            next_button = driver.find_element(By.CLASS_NAME, "next")
            next_button.click()
            wait.until(EC.staleness_of(card_list_elements[0]))
        except:
            break

    for detail_url in detail_urls:
        time.sleep(60)
        try:
            driver.get(detail_url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            card_id = detail_url.split("id=")[-1]
            grade = (
                driver.find_element(By.CLASS_NAME, "menu-list3")
                .find_element(By.CLASS_NAME, "icon2")
                .text.replace("カードランキング", "")
            )

            base_info_table = driver.find_elements(By.CLASS_NAME, "def-tbl1")[0]
            base_info_table_trs = base_info_table.find_elements(By.TAG_NAME, "tr")
            card_name = base_info_table_trs[0].find_element(By.TAG_NAME, "td").text
            official_url = (
                base_info_table_trs[1]
                .find_element(By.TAG_NAME, "td")
                .find_element(By.TAG_NAME, "a")
                .get_attribute("href")
            )
            issuer_name = base_info_table_trs[2].find_element(By.TAG_NAME, "td").text

            # 発行会社の ID を取得、なければ追加
            # if issuer_name not in issuer_dict:
            #     new_issuer_id = len(issuer_dict) + 1  # 連番で発行
            #     issuers_sheet.append_row([new_issuer_id, issuer_name])
            #     issuer_dict[issuer_name] = new_issuer_id

            # issuer_id = issuer_dict[issuer_name]
            cursor.execute(
                "SELECT id FROM issuers WHERE issuer_name = %s", (issuer_name,)
            )
            issuer_row = cursor.fetchone()
            if issuer_row is None:
                cursor.execute(
                    "INSERT INTO issuers (issuer_name) VALUES (%s)", (issuer_name,)
                )
                conn.commit()
                issuer_id = cursor.lastrowid
                issuers_sheet.append_row([issuer_id, issuer_name])
            else:
                issuer_id = issuer_row[0]

            partner_name = base_info_table_trs[3].find_element(By.TAG_NAME, "td").text
            # 提携会社の ID を取得、なければ追加
            # if partner_name not in partner_dict:
            #     new_partner_id = len(partner_dict) + 1
            #     partners_sheet.append_row([new_partner_id, partner_name, ""])
            #     partner_dict[partner_name] = new_partner_id

            # partner_id = partner_dict[partner_name]
            cursor.execute(
                "SELECT id FROM partners WHERE partner_name = %s",
                (partner_name,),
            )
            partner_row = cursor.fetchone()
            if partner_row is None:
                cursor.execute(
                    "INSERT INTO partners (partner_name) VALUES (%s)", (partner_name,)
                )
                conn.commit()
                partner_id = cursor.lastrowid
                partners_sheet.append_row([partner_id, partner_name])
            else:
                partner_id = partner_row[0]

            brand_text = base_info_table_trs[4].find_element(By.TAG_NAME, "td").text
            brands = brand_text.split("、")
            visa = "Visa" in brands
            mastercard = "Mastercard" in brands
            jcb = "JCB" in brands
            amex = "AMEX（アメックス）" in brands
            diners = "Diners" in brands
            unionpay = "銀聯（UnionPay）" in brands

            eligibility = base_info_table_trs[5].find_element(By.TAG_NAME, "td").text
            application_method = (
                base_info_table_trs[6].find_element(By.TAG_NAME, "td").text
            )
            screening_period = (
                base_info_table_trs[7].find_element(By.TAG_NAME, "td").text
            )
            annual_fee = base_info_table_trs[8].find_element(By.TAG_NAME, "td").text
            shopping_limit = base_info_table_trs[9].find_element(By.TAG_NAME, "td").text
            cashing_limit = base_info_table_trs[10].find_element(By.TAG_NAME, "td").text
            revolving_interest_rate = (
                base_info_table_trs[11].find_element(By.TAG_NAME, "td").text
            )
            cashing_interest_rate = (
                base_info_table_trs[12].find_element(By.TAG_NAME, "td").text
            )
            payment_methods = (
                base_info_table_trs[13].find_element(By.TAG_NAME, "td").text
            )
            closing_date = base_info_table_trs[14].find_element(By.TAG_NAME, "td").text
            remarks = base_info_table_trs[15].find_element(By.TAG_NAME, "td").text

            # cards_sheet.append_row(
            #     [
            #         card_id,
            #         card_name,
            #         official_url,
            #         grade,
            #         issuer_id,
            #         partner_id,
            #         visa,
            #         mastercard,
            #         jcb,
            #         amex,
            #         diners,
            #         unionpay,
            #         eligibility,
            #         application_method,
            #         screening_period,
            #         annual_fee,
            #         shopping_limit,
            #         cashing_limit,
            #         revolving_interest_rate,
            #         cashing_interest_rate,
            #         payment_methods,
            #         closing_date,
            #         remarks,
            #         detail_url,
            #     ]
            # )

            # `cards` テーブルに UPSERT（重複時は更新）
            # cursor.execute(
            #     """
            #     INSERT INTO cards (
            #         card_id, card_name, official_url, issuer_id, partner_id,
            #         visa, mastercard, jcb, amex, diners, unionpay,
            #         eligibility, application_method, screening_period, annual_fee, shopping_limit, cashing_limit,
            #         revolving_interest_rate, cashing_interest_rate, payment_methods, closing_date, remarks
            #     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            #     ON DUPLICATE KEY UPDATE
            #         card_name=VALUES(card_name), official_url=VALUES(official_url),
            #         issuer_id=VALUES(issuer_id), partner_id=VALUES(partner_id),
            #         visa=VALUES(visa), mastercard=VALUES(mastercard), jcb=VALUES(jcb), amex=VALUES(amex), diners=VALUES(diners), unionpay=VALUES(unionpay),
            #         eligibility=VALUES(eligibility), application_method=VALUES(application_method),
            #         screening_period=VALUES(screening_period), annual_fee=VALUES(annual_fee), shopping_limit=VALUES(shopping_limit),
            #         cashing_limit=VALUES(cashing_limit), revolving_interest_rate=VALUES(revolving_interest_rate),
            #         cashing_interest_rate=VALUES(cashing_interest_rate), payment_methods=VALUES(payment_methods),
            #         closing_date=VALUES(closing_date), remarks=VALUES(remarks);
            # """,
            #     (
            #         card_id,
            #         card_name,
            #         official_url,
            #         issuer_id,
            #         partner_id,
            #         int(visa),
            #         int(mastercard),
            #         int(jcb),
            #         int(amex),
            #         int(diners),
            #         int(unionpay),
            #         eligibility,
            #         application_method,
            #         screening_period,
            #         annual_fee,
            #         shopping_limit,
            #         cashing_limit,
            #         revolving_interest_rate,
            #         cashing_interest_rate,
            #         payment_methods,
            #         closing_date,
            #         remarks,
            #     ),
            # )
            cursor.execute(
                """
    INSERT INTO cards (
        card_id, card_name, official_url, issuer_id, partner_id, 
        visa, mastercard, jcb, amex, diners, unionpay,
        eligibility, application_method, screening_period, annual_fee, shopping_limit, cashing_limit, 
        revolving_interest_rate, cashing_interest_rate, payment_methods, closing_date, remarks
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
                (
                    card_id,
                    card_name,
                    official_url,
                    issuer_id,
                    partner_id,
                    int(visa),  # boolean を int に変換
                    int(mastercard),
                    int(jcb),
                    int(amex),
                    int(diners),
                    int(unionpay),
                    eligibility,
                    application_method,
                    screening_period,
                    annual_fee,
                    shopping_limit,
                    cashing_limit,
                    revolving_interest_rate,
                    cashing_interest_rate,
                    payment_methods,
                    closing_date,
                    remarks,
                ),
            )
            conn.commit()

            cards_table_id = cursor.lastrowid
            cards_sheet.append_row(
                [
                    cards_table_id,
                    card_id,
                    card_name,
                    official_url,
                    grade,
                    issuer_id,
                    partner_id,
                    visa,
                    mastercard,
                    jcb,
                    amex,
                    diners,
                    unionpay,
                    eligibility,
                    application_method,
                    screening_period,
                    annual_fee,
                    shopping_limit,
                    cashing_limit,
                    revolving_interest_rate,
                    cashing_interest_rate,
                    payment_methods,
                    closing_date,
                    remarks,
                    detail_url,
                ]
            )
            point_rewards_tables = driver.find_elements(
                By.CSS_SELECTOR, ".p-rateTbl.p-rateTbl-type2.p-rateTbl01.s-highlightTbl"
            )
            if not point_rewards_tables:
                continue

            point_rewards_table = point_rewards_tables[0]
            trs = point_rewards_table.find_element(By.TAG_NAME, "tbody").find_elements(
                By.TAG_NAME, "tr"
            )

            category = ""
            notes = driver.find_elements(By.CLASS_NAME, "p-rateNotes_label")
            for tr in trs:
                th = tr.find_element(By.TAG_NAME, "th")
                class_list = set(th.get_attribute("class").split())
                required_classes = {
                    "p-rateTbl_label",
                    "p-rateTbl_labelParent",
                    "fixCol",
                }
                if required_classes.issubset(class_list):
                    category = th.get_attribute("textContent").strip()
                    continue

                shop_text = th.get_attribute("title").split("※")
                shop = shop_text[0]
                if len(shop_text) > 1:
                    # shop_textの中から末尾の数字を取得
                    # remarks_number = re.search(r"\d+$", shop_text)
                    remarks_number = shop_text[-1].strip()
                    # remarks = (
                    #     notes[int(remarks_number) - 1]
                    #     .find_element(By.XPATH, "./following-sibling::*[1]")
                    #     .text.strip()
                    # )
                    remarks = driver.execute_script(
                        "return arguments[0].nextSibling.textContent;",
                        notes[int(remarks_number) - 1],
                    ).strip()
                    print(f"remarks: {remarks}")
                else:
                    remarks = ""
                print(f"shop: {shop}")
                # rewards_rext = (
                #     tr.find_element(By.XPATH, ".//td")
                #     .get_attribute("innerText")
                #     .strip()
                # )
                td = tr.find_element(By.XPATH, ".//td")
                rewards_rext = td.get_attribute("textContent").strip()
                print(f"rewards_rext: {rewards_rext}")
                rewards_numbers = re.findall(r"\d+,?\d*", rewards_rext)
                print(f"rewards_numbers: {rewards_numbers}")
                # amount, points = map(int, rewards_numbers)
                amount = int(rewards_numbers[0].replace(",", ""))
                points = int(rewards_numbers[1])

                # リトライロジックを追加
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        point_rewards_sheet.append_row(
                            [cards_table_id, category, shop, amount, points, remarks]
                        )
                        break
                    except ConnectionError as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            print(
                                f"[ERROR] Google Sheets APIへの接続に失敗しました: {e}"
                            )
                            raise
                        print(
                            f"[WARN] 接続エラー、{retry_count}回目のリトライを実行します..."
                        )
                        time.sleep(5 * retry_count)  # 徐々に待ち時間を増やす

            #             cursor.execute(
            #                 """
            # INSERT INTO point_rewards (card_id, category, shop, spending_amount, points) VALUES (%s, %s, %s, %s, %s)
            # """,
            #                 (
            #                     cards_table_id,
            #                     category,
            #                     shop,
            #                     amount,
            #                     points,
            #                 ),
            #             )
            conn.commit()

        except mysql.connector.Error as e:
            print(f"[ERROR] MySQL カードデータ UPSERT エラー ({card_name}): {e}")
            print(traceback.format_exc())
            continue

finally:
    driver.quit()
