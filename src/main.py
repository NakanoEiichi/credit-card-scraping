from models.database import DatabaseHandler
from services.sheets_handler import SheetsHandler
from services.card_scraper import CardScraper
from dotenv import load_dotenv

load_dotenv()


def main():
    db_handler = DatabaseHandler()
    sheets_handler = SheetsHandler()
    scraper = CardScraper(db_handler, sheets_handler)

    try:
        # カード一覧ページからURLを取得
        base_url = "https://kakaku.com/card/ranking/"
        card_urls = scraper.get_card_urls(base_url)

        # 各カードの詳細情報を取得
        for url in card_urls:
            try:
                # カード情報の取得
                card_data = scraper.scrape_card_detail(url)
                # カード情報のupsert
                card_id = db_handler.upsert_card(card_data)

                # # ポイント還元情報の取得と保存
                # rewards = scraper.scrape_point_rewards(card_id)
                # for reward in rewards:
                #     db_handler.upsert_point_reward(reward)

                # ポイント交換情報の取得と保存
                exchanges = scraper.scrape_point_exchange(card_id)
                for exchange in exchanges:
                    db_handler.upsert_point_exchange(exchange)

                # 付帯保険情報の取得と保存
                scraper.scrape_include_insurance(card_id)

                # 付帯サービス情報の取得と保存
                scraper.scrape_include_services(card_id)

            except Exception as e:
                print(f"[ERROR] カード情報の取得に失敗: {url}")
                print(e)
                continue

        # スプレッドシートの更新
        # print("スプレッドシートの更新を開始します...")
        # sheets_handler.batch_update(db_handler)
        # print("スプレッドシートの更新が完了しました。")

    finally:
        scraper.close()
        db_handler.close()


if __name__ == "__main__":
    main()
