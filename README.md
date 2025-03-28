## 機能

- クレジットカード情報の自動スクレイピング
- データベースへの情報保存
- Googleスプレッドシートへのデータ書き込み

## 必要条件

- Docker
- Docker Compose
- Google Cloud Platform アカウント（Google Sheets API用）

## セットアップ

1. リポジトリをクローン
```bash
git clone [repository-url]
cd credit-card-scraping
```

2. 環境変数の設定
```bash
cp .env.example .env
```
`.env`ファイルを編集し、必要な設定を行ってください。

3. Google Cloud Platformの設定
- Google Cloud Platformでプロジェクトを作成
- Google Sheets APIを有効化
- サービスアカウントを作成し、認証情報（JSON）をダウンロード
- ダウンロードしたJSONファイルを`credentials.json`としてプロジェクトルートに配置

4. アプリケーションの起動
```bash
docker-compose up -d
```

## スクレイピングの実行

アプリケーションコンテナに入り、`main.py`を実行することでスクレイピング処理が開始されます：

```bash
# アプリケーションコンテナに入る
docker-compose exec app bash

# スクレイピング処理を実行
python main.py
```

## 環境変数

- `MYSQL_HOST`: MySQLホスト名
- `MYSQL_USER`: MySQLユーザー名
- `MYSQL_PASSWORD`: MySQLパスワード
- `MYSQL_DATABASE`: MySQLデータベース名
- `MYSQL_ROOT_PASSWORD`: MySQL rootパスワード
- `GOOGLE_SHEETS_SPREADSHEET_ID`: GoogleスプレッドシートID