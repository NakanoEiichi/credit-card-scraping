## 機能

- クレジットカード情報の自動スクレイピング
- クレジットカード画像の取得とS3/MinIOへの保存
- データベースへの情報保存
- ~~Googleスプレッドシートへのデータ書き込み~~

## 必要条件

- Docker
- Docker Compose
- ~~Google Cloud Platform アカウント（Google Sheets API用）~~

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

3. ~~Google Cloud Platformの設定~~
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

### データベース設定
- `MYSQL_HOST`: MySQLホスト名
- `MYSQL_USER`: MySQLユーザー名
- `MYSQL_PASSWORD`: MySQLパスワード
- `MYSQL_DATABASE`: MySQLデータベース名
- `MYSQL_ROOT_PASSWORD`: MySQL rootパスワード
- `DB_PORT`: MySQLポート

### Selenium設定
- `SELENIUM_URL`: SeleniumサーバーのURL

### MinIO設定（開発環境）
- `MINIO_ROOT_USER`: MinIO管理者ユーザー名
- `MINIO_ROOT_PASSWORD`: MinIO管理者パスワード
- `MINIO_PORT`: MinIO APIポート
- `MINIO_CONSOLE_PORT`: MinIO管理コンソールポート
- `MINIO_ENDPOINT`: MinIOエンドポイントURL
- `MINIO_BUCKET_NAME`: 画像保存用バケット名

### Google Sheets設定
- ~~`GOOGLE_SHEETS_SPREADSHEET_ID`: GoogleスプレッドシートID~~