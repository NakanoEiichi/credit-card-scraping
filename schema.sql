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
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (issuer_id) REFERENCES issuers(id),
    FOREIGN KEY (partner_id) REFERENCES partners(id)
);

-- point_rewards table
CREATE TABLE IF NOT EXISTS point_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL,
    shop_id INT NOT NULL,
    spending_amount INT,
    points INT,
    condition_raw VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id),
    FOREIGN KEY (shop_id) REFERENCES shops(id),
    UNIQUE KEY unique_point_reward (card_id, shop_id, condition_raw)
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