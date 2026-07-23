"""
Phase 1: Load raw Olist CSVs, clean, and build the star schema in DuckDB.

Before running: download these into data/raw/
  From https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
    - olist_customers_dataset.csv
    - olist_orders_dataset.csv
    - olist_order_items_dataset.csv
    - olist_order_payments_dataset.csv
    - olist_order_reviews_dataset.csv
    - olist_products_dataset.csv
    - olist_sellers_dataset.csv
    - product_category_name_translation.csv
  From https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist
    - olist_marketing_qualified_leads_dataset.csv
    - olist_closed_deals_dataset.csv
"""
import duckdb
import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "warehouse.duckdb"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_csv(name):
    path = RAW / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {name} in data/raw/. See the docstring at the top of this "
            f"script for download links."
        )
    return pd.read_csv(path)


def main():
    customers = load_csv("olist_customers_dataset.csv")
    orders = load_csv("olist_orders_dataset.csv")
    items = load_csv("olist_order_items_dataset.csv")
    payments = load_csv("olist_order_payments_dataset.csv")
    reviews = load_csv("olist_order_reviews_dataset.csv")
    products = load_csv("olist_products_dataset.csv")
    sellers = load_csv("olist_sellers_dataset.csv")
    cat_translation = load_csv("product_category_name_translation.csv")

    # --- clean & join into one order-level fact table ---
    # aggregate payments (an order can have multiple payment installments/methods)
    pay_agg = payments.groupby("order_id", as_index=False)["payment_value"].sum()

    # take the most recent review per order (some orders have duplicate review rows)
    reviews_sorted = reviews.sort_values("review_creation_date").drop_duplicates(
        "order_id", keep="last"
    )

    fact_orders = (
        orders.merge(pay_agg, on="order_id", how="left")
        .merge(
            reviews_sorted[["order_id", "review_score", "review_comment_message"]],
            on="order_id",
            how="left",
        )
    )

    # parse timestamps
    ts_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for c in ts_cols:
        fact_orders[c] = pd.to_datetime(fact_orders[c], errors="coerce")

    products = products.merge(cat_translation, on="product_category_name", how="left")
    products = products.rename(
        columns={
            "product_category_name_english": "product_category",
            "product_weight_g": "product_weight_g",
        }
    )

    # --- write to DuckDB ---
    con = duckdb.connect(str(DB_PATH))
    con.execute(open(Path(__file__).resolve().parents[1] / "sql" / "schema.sql").read())

    con.register("df_customers", customers)
    con.execute("""
        INSERT INTO dim_customer
        SELECT DISTINCT customer_id, customer_unique_id, customer_city, customer_state
        FROM df_customers
    """)

    con.register("df_products", products)
    con.execute("""
        INSERT INTO dim_product
        SELECT DISTINCT product_id, product_category, product_weight_g, product_photos_qty
        FROM df_products
    """)

    con.register("df_sellers", sellers)
    con.execute("""
        INSERT INTO dim_seller
        SELECT DISTINCT seller_id, seller_city, seller_state
        FROM df_sellers
    """)

    con.register("df_fact_orders", fact_orders)
    con.execute("""
        INSERT INTO fact_orders
        SELECT
            order_id, customer_id, order_status,
            order_purchase_timestamp, order_approved_at,
            order_delivered_carrier_date, order_delivered_customer_date,
            order_estimated_delivery_date, payment_value,
            review_score, review_comment_message
        FROM df_fact_orders
    """)

    # marketing funnel (optional — only if you've downloaded it)
    mql_path = RAW / "olist_marketing_qualified_leads_dataset.csv"
    deals_path = RAW / "olist_closed_deals_dataset.csv"
    if mql_path.exists() and deals_path.exists():
        mql = pd.read_csv(mql_path)
        deals = pd.read_csv(deals_path)
        funnel = mql.merge(
            deals[["mql_id", "seller_id", "won_date", "business_segment", "lead_type"]],
            on="mql_id",
            how="left",
        )
        con.register("df_funnel", funnel)
        con.execute("""
            INSERT INTO fact_marketing_funnel
            SELECT mql_id, first_contact_date, landing_page_id, origin,
                   seller_id, won_date, business_segment, lead_type
            FROM df_funnel
        """)
        print("Marketing funnel data loaded.")
    else:
        print("Marketing funnel CSVs not found — skipping (order funnel still works fine).")

    n_orders = con.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0]
    print(f"Done. {n_orders:,} orders loaded into {DB_PATH}")
    con.close()


if __name__ == "__main__":
    main()
