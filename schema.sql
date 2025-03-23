-- issuers table
CREATE TABLE IF NOT EXISTS issuers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    issuer_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- partners table
CREATE TABLE IF NOT EXISTS partners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    partner_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- points table
CREATE TABLE IF NOT EXISTS points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_name VARCHAR(255) NOT NULL,
    expires_at VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- shops table
CREATE TABLE IF NOT EXISTS shops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    is_online BOOLEAN DEFAULT FALSE,
    category VARCHAR(255),
    shop_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- cards table
CREATE TABLE IF NOT EXISTS cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kakaku_card_id VARCHAR(50) UNIQUE NOT NULL,
    card_name VARCHAR(255) NOT NULL,
    official_url TEXT,
    grade VARCHAR(50),
    issuer_id INT,
    partner_id INT,
    point_id INT,
    visa BOOLEAN DEFAULT FALSE,
    mastercard BOOLEAN DEFAULT FALSE,
    jcb BOOLEAN DEFAULT FALSE,
    amex BOOLEAN DEFAULT FALSE,
    diners BOOLEAN DEFAULT FALSE,
    unionpay BOOLEAN DEFAULT FALSE,
    eligibility TEXT,
    application_method TEXT,
    screening_period TEXT,
    annual_fee TEXT,
    shopping_limit TEXT,
    cashing_limit TEXT,
    revolving_interest_rate TEXT,
    cashing_interest_rate TEXT,
    payment_methods TEXT,
    closing_date TEXT,
    annual_bonus TEXT,
    etc_card TEXT,
    family_card TEXT,
    electronic_money TEXT,
    electronic_money_charge TEXT,
    electronic_money_point TEXT,
    digital_wallet TEXT,
    code_payment TEXT,
    target_scraping_url TEXT,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (issuer_id) REFERENCES issuers(id),
    FOREIGN KEY (partner_id) REFERENCES partners(id),
    FOREIGN KEY (point_id) REFERENCES points(id)
);

-- point_rewards table
CREATE TABLE IF NOT EXISTS point_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    shop_id INT NOT NULL,
    spending_amount INT NOT NULL,
    points INT NOT NULL,
    from_kakaku BOOLEAN DEFAULT FALSE,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id),
    UNIQUE KEY unique_point_reward (card_id, shop_id, from_kakaku)
);

-- discount_rewards table
CREATE TABLE IF NOT EXISTS discount_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    shop_id INT NOT NULL,
    discount_amount INT,
    discount_rate INT,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id),
    UNIQUE KEY unique_discount_reward (card_id, shop_id)
);

-- point_reward_conditions table
CREATE TABLE IF NOT EXISTS point_reward_conditions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    point_reward_id INT NOT NULL,
    condition_type ENUM('date', 'brand', 'amount') NOT NULL,
    condition_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (point_reward_id) REFERENCES point_rewards(id) ON DELETE CASCADE,
    UNIQUE KEY unique_condition (point_reward_id, condition_type, condition_value)
); 

-- exchangeable_rewards table
CREATE TABLE IF NOT EXISTS exchangeable_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    reward_name VARCHAR(255) NOT NULL,
    unit VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
);

-- point_exchanges table
CREATE TABLE IF NOT EXISTS point_exchanges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    exchangeable_reward_id INT NOT NULL,
    before_value INT NOT NULL,
    after_value INT NOT NULL,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (exchangeable_reward_id) REFERENCES exchangeable_rewards(id)
);

-- include_insurance table
CREATE TABLE IF NOT EXISTS include_insurances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    category VARCHAR(255) NOT NULL,
    coverage_type VARCHAR(255) NOT NULL,
    coverage_amount VARCHAR(255) NOT NULL,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    UNIQUE KEY unique_include_insurance (card_id, category, coverage_type)
);

-- include_services table
CREATE TABLE IF NOT EXISTS include_services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    service_content TEXT NOT NULL,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    UNIQUE KEY unique_include_service (card_id, service_name)
);

-- shop_domains table
CREATE TABLE IF NOT EXISTS shop_domains (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id)
);

-- annual_bonus table
CREATE TABLE IF NOT EXISTS annual_bonuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    spending_amount INT NOT NULL,
    bonus_amount INT NOT NULL,
    limit_amount INT,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    UNIQUE KEY unique_annual_bonus (card_id, spending_amount)
);
