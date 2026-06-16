CREATE TABLE IF NOT EXISTS market_ticks (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    main_type VARCHAR(100),
    sub_type VARCHAR(100),
    short_name VARCHAR(255),
    trading_date VARCHAR(50),
    price_high FLOAT,
    price_low FLOAT,
    close_price FLOAT,
    open_price FLOAT,
    trade_volume BIGINT,
    share_volume BIGINT,
    turnover FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);