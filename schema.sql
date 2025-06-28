-- 基本テーブル（外部キー制約なし）
-- issuers table
CREATE TABLE IF NOT EXISTS issuers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    issuer_name VARCHAR(255) NOT NULL UNIQUE COMMENT '発行会社名',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- points table
CREATE TABLE IF NOT EXISTS points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_name VARCHAR(255) NOT NULL UNIQUE COMMENT 'ポイント名',
    expiration VARCHAR(255) COMMENT '有効期限',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- shops table
CREATE TABLE IF NOT EXISTS shops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    is_online BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'オンラインショップフラグ',
    category VARCHAR(255) NOT NULL COMMENT 'ショップカテゴリ',
    shop_name VARCHAR(255) NOT NULL UNIQUE COMMENT 'ショップ名',
    created_by VARCHAR(255) NOT NULL COMMENT '作成者',
    checked_by VARCHAR(255) COMMENT '確認者',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- exchangeable_rewards table
CREATE TABLE IF NOT EXISTS exchangeable_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(255) NOT NULL COMMENT 'リワードカテゴリ',
    reward_name VARCHAR(255) NOT NULL UNIQUE COMMENT 'リワード名',
    unit VARCHAR(255) NOT NULL COMMENT '単位',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- レコメンドタグマスタテーブル
-- recommend_tags table
CREATE TABLE IF NOT EXISTS recommend_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL UNIQUE COMMENT 'タグ名',
    tag_category VARCHAR(50) NOT NULL COMMENT 'タグカテゴリ',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- カード関連テーブル（issuers, partners, pointsを参照）
-- cards table
CREATE TABLE IF NOT EXISTS cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kakaku_card_id VARCHAR(50) UNIQUE NOT NULL COMMENT '価格.comのカードID',
    card_name VARCHAR(255) NOT NULL COMMENT 'カード名',
    official_url TEXT COMMENT '公式URL',
    grade VARCHAR(50) NOT NULL COMMENT 'グレード',
    issuer_id INT NOT NULL,
    point_id INT NOT NULL,
    visa BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'VISA対応フラグ',
    mastercard BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'Mastercard対応フラグ',
    jcb BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'JCB対応フラグ',
    amex BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'American Express対応フラグ',
    diners BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'Diners Club対応フラグ',
    unionpay BOOLEAN DEFAULT FALSE NOT NULL COMMENT 'UnionPay対応フラグ',
    eligibility TEXT NOT NULL COMMENT '入会資格',
    application_method TEXT COMMENT '申込方法',
    screening_period TEXT COMMENT '審査・発行期間',
    annual_fee_raw TEXT NOT NULL COMMENT '年会費（価格.com原文）',
    annual_fee INT COMMENT '年会費',
    annual_fee_condition TEXT COMMENT '年会費条件',
    shopping_limit TEXT COMMENT 'ショッピング利用可能枠',
    cashing_limit TEXT COMMENT 'キャッシング利用可能枠',
    revolving_interest_rate TEXT COMMENT 'リボ払い金利',
    cashing_interest_rate TEXT COMMENT 'キャッシング金利',
    payment_methods TEXT COMMENT '支払方法',
    closing_date TEXT COMMENT '締め日・支払日',
    annual_bonus_raw TEXT COMMENT '年間利用ボーナス（価格.com原文）',
    etc_card TEXT COMMENT 'ETCカード',
    family_card TEXT COMMENT '家族カード',
    electronic_money TEXT COMMENT '電子マネー機能',
    electronic_money_charge TEXT COMMENT '電子マネーチャージ',
    electronic_money_point TEXT COMMENT '電子マネーチャージでポイント対象',
    digital_wallet TEXT COMMENT '対応する電子ウォレット',
    code_payment TEXT COMMENT '利用可能なコード決済',
    remarks TEXT COMMENT '備考',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (issuer_id) REFERENCES issuers(id),
    FOREIGN KEY (point_id) REFERENCES points(id)
);

-- カードとレコメンドタグの関連テーブル
-- card_recommend_tags table(cards, recommend_tagsを参照)
CREATE TABLE IF NOT EXISTS card_recommend_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    recommend_tag_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (recommend_tag_id) REFERENCES recommend_tags(id)
);

-- ポイント報酬関連テーブル（cards, shopsを参照）
-- point_rewards table
CREATE TABLE IF NOT EXISTS point_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    shop_id INT NOT NULL,
    spending_amount INT NOT NULL COMMENT '利用金額',
    given_points INT NOT NULL COMMENT '付与ポイント',
    remarks TEXT COMMENT '備考',
    evidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);

-- point_reward_conditions table
CREATE TABLE IF NOT EXISTS point_reward_conditions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_reward_id INT NOT NULL,
    condition_type VARCHAR(255) NOT NULL COMMENT '条件タイプ',
    condition_value VARCHAR(255) NOT NULL COMMENT '条件値',
    limit_amount INT COMMENT '限度額',
    remarks TEXT COMMENT '備考',
    evidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (point_reward_id) REFERENCES point_rewards(id),
    UNIQUE KEY unique_condition (point_reward_id, condition_type, condition_value)
);

-- 割引報酬関連テーブル（cards, shopsを参照）
-- discount_rewards table
CREATE TABLE IF NOT EXISTS discount_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    shop_id INT NOT NULL,
    discount_condition_type_1 VARCHAR(255) COMMENT '割引条件タイプ1',
    discount_condition_type_2 VARCHAR(255) COMMENT '割引条件タイプ2',
    discount_condition_type_3 VARCHAR(255) COMMENT '割引条件タイプ3',
    discount_condition_value_1 VARCHAR(255) COMMENT '割引条件値1',
    discount_condition_value_2 VARCHAR(255) COMMENT '割引条件値2',
    discount_condition_value_3 VARCHAR(255) COMMENT '割引条件値3',
    discount_amount INT COMMENT '割引額',
    discount_rate INT COMMENT '割引率',
    evidence TEXT,
    remarks TEXT COMMENT '備考',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id),
    UNIQUE KEY unique_discount_reward (card_id, shop_id)
);

-- ポイント交換関連テーブル（cards, exchangeable_rewardsを参照）
-- point_exchanges table
CREATE TABLE IF NOT EXISTS point_exchanges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    exchangeable_reward_id INT NOT NULL,
    before_value INT NOT NULL COMMENT '交換前のポイント数',
    after_value INT NOT NULL COMMENT '交換後のポイント数',
    remarks TEXT COMMENT '備考',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (exchangeable_reward_id) REFERENCES exchangeable_rewards(id),
    UNIQUE KEY unique_point_exchange (card_id, exchangeable_reward_id)
);

-- 付帯保険関連テーブル（cardsを参照）
-- include_insurance table
CREATE TABLE IF NOT EXISTS include_insurances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    category VARCHAR(255) NOT NULL COMMENT 'カテゴリ',
    coverage_type VARCHAR(255) NOT NULL COMMENT '保険タイプ',
    coverage_amount VARCHAR(255) NOT NULL COMMENT '保険金額',
    remarks TEXT COMMENT '備考',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    UNIQUE KEY unique_include_insurance (card_id, category, coverage_type)
);

-- 付帯サービス関連テーブル（cardsを参照）
-- include_services table
CREATE TABLE IF NOT EXISTS include_services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    service_name VARCHAR(255) NOT NULL COMMENT 'サービス名',
    service_content TEXT NOT NULL COMMENT 'サービス内容',
    remarks TEXT COMMENT '備考',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    UNIQUE KEY unique_include_service (card_id, service_name)
);

-- ショップドメイン関連テーブル（shopsを参照）
-- shop_domains table
CREATE TABLE IF NOT EXISTS shop_domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    url TEXT NOT NULL COMMENT 'ショップURL',
    domain VARCHAR(255) NOT NULL COMMENT 'ドメイン',
    remarks TEXT COMMENT '備考',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);

-- 年間ボーナス関連テーブル（cardsを参照）
-- annual_bonus table
CREATE TABLE IF NOT EXISTS annual_bonuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    spending_amount INT NOT NULL COMMENT '利用金額',
    bonus_amount INT NOT NULL COMMENT 'ボーナス金額',
    limit_amount INT COMMENT '限度額',
    remarks TEXT COMMENT '備考',
    evidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);
