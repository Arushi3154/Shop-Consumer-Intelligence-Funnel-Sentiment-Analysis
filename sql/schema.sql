-- Star schema for consumer intelligence funnel
-- Run against DuckDB (or adapt for Postgres — syntax is ~95% compatible)

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id         VARCHAR PRIMARY KEY,
    customer_unique_id  VARCHAR,
    customer_city       VARCHAR,
    customer_state      VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id          VARCHAR PRIMARY KEY,
    product_category    VARCHAR,
    product_weight_g     DOUBLE,
    product_photos_qty  INTEGER
);

CREATE TABLE IF NOT EXISTS dim_seller (
    seller_id       VARCHAR PRIMARY KEY,
    seller_city     VARCHAR,
    seller_state    VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key    DATE PRIMARY KEY,
    year        INTEGER,
    month       INTEGER,
    day         INTEGER,
    weekday     VARCHAR
);

-- One row per order = core funnel fact table
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id                        VARCHAR PRIMARY KEY,
    customer_id                     VARCHAR REFERENCES dim_customer(customer_id),
    order_status                    VARCHAR,
    order_purchase_timestamp        TIMESTAMP,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP,
    payment_value                   DOUBLE,
    review_score                    INTEGER,
    review_comment_message          VARCHAR
);

-- Marketing funnel: MQL -> SQL (sales qualified lead) -> closed deal
CREATE TABLE IF NOT EXISTS fact_marketing_funnel (
    mql_id                  VARCHAR PRIMARY KEY,
    first_contact_date      DATE,
    landing_page_id         VARCHAR,
    origin                  VARCHAR,       -- traffic source: organic, paid, social, etc.
    seller_id               VARCHAR,
    won_date                DATE,          -- null if never converted to a deal
    business_segment        VARCHAR,
    lead_type                VARCHAR
);

-- Handy view: funnel stage per order, for drop-off analysis
CREATE OR REPLACE VIEW v_order_funnel_stages AS
SELECT
    order_id,
    customer_id,
    order_purchase_timestamp                                       AS stage_1_purchased,
    order_approved_at                                              AS stage_2_approved,
    order_delivered_carrier_date                                   AS stage_3_shipped,
    order_delivered_customer_date                                  AS stage_4_delivered,
    CASE WHEN review_score IS NOT NULL THEN 1 ELSE 0 END           AS stage_5_reviewed,
    review_score,
    review_comment_message
FROM fact_orders;
