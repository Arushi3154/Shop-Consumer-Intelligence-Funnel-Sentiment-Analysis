"""
Phase 2: Funnel analysis.
Computes stage-by-stage conversion/drop-off, delivery-time impact on satisfaction,
and monthly cohort repeat-purchase retention.
Outputs CSVs + charts to outputs/.
"""
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "warehouse.duckdb"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH))

# ---- 1. Stage-by-stage funnel counts ----
funnel_counts = con.execute("""
    SELECT
        COUNT(*)                                                          AS purchased,
        COUNT(order_approved_at)                                         AS approved,
        COUNT(order_delivered_carrier_date)                              AS shipped,
        COUNT(order_delivered_customer_date)                             AS delivered,
        COUNT(review_score)                                              AS reviewed
    FROM fact_orders
""").df()
funnel_counts.to_csv(OUT / "funnel_stage_counts.csv", index=False)
print("Funnel stage counts:\n", funnel_counts)

stages = ["purchased", "approved", "shipped", "delivered", "reviewed"]
values = funnel_counts.iloc[0][stages].values
drop_off = [round((1 - values[i] / values[i - 1]) * 100, 1) if i > 0 else 0 for i in range(len(values))]

plt.figure(figsize=(8, 5))
plt.bar(stages, values, color="#4C72B0")
for i, (v, d) in enumerate(zip(values, drop_off)):
    label = f"{v:,}" if i == 0 else f"{v:,}\n(-{d}%)"
    plt.text(i, v, label, ha="center", va="bottom", fontsize=9)
plt.title("Order Funnel: Purchase to Review")
plt.ylabel("Number of orders")
plt.tight_layout()
plt.savefig(OUT / "funnel_chart.png", dpi=150)
plt.close()

# ---- 2. Delivery time vs review score ----
delivery_sat = con.execute("""
    SELECT
        DATE_DIFF('day', order_purchase_timestamp, order_delivered_customer_date) AS delivery_days,
        review_score
    FROM fact_orders
    WHERE order_delivered_customer_date IS NOT NULL AND review_score IS NOT NULL
""").df()
delivery_sat = delivery_sat[(delivery_sat.delivery_days >= 0) & (delivery_sat.delivery_days <= 60)]
avg_by_score = delivery_sat.groupby("review_score")["delivery_days"].mean().round(1)
avg_by_score.to_csv(OUT / "delivery_days_by_review_score.csv")
print("\nAvg delivery days by review score:\n", avg_by_score)

# ---- 3. Monthly cohort repeat-purchase retention ----
cohort = con.execute("""
    WITH first_purchase AS (
        SELECT customer_id, MIN(DATE_TRUNC('month', order_purchase_timestamp)) AS cohort_month
        FROM fact_orders
        GROUP BY customer_id
    ),
    orders_with_cohort AS (
        SELECT o.customer_id, f.cohort_month,
               DATE_TRUNC('month', o.order_purchase_timestamp) AS order_month
        FROM fact_orders o
        JOIN first_purchase f USING (customer_id)
    )
    SELECT cohort_month,
           DATE_DIFF('month', cohort_month, order_month) AS month_number,
           COUNT(DISTINCT customer_id) AS active_customers
    FROM orders_with_cohort
    GROUP BY 1, 2
    ORDER BY 1, 2
""").df()
cohort.to_csv(OUT / "cohort_retention_raw.csv", index=False)
print(f"\nCohort retention table saved ({len(cohort)} rows). "
      f"Note: Olist is mostly single-purchase customers, so expect thin repeat-purchase "
      f"retention — that itself is a real, reportable insight.")

con.close()
print("\nPhase 2 complete. See outputs/ for charts and CSVs.")
