import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(
    page_title="Olist | Monthly Seller Performance",
    layout="wide"
)

st.title("Monthly Seller Performance Overview")

@st.cache_resource
def get_connection():
    return duckdb.connect("olist.duckdb", read_only=False)

@st.cache_data
def load_kpis():
    con = get_connection()

    # Create KPI table if it does NOT exist
    tables = con.sql("SHOW TABLES").df()

    if "seller_monthly_kpis" not in tables["name"].values:
        con.sql("""
        CREATE TABLE seller_monthly_kpis AS
        SELECT
            i.seller_id,
            DATE_TRUNC('month', o.order_purchase_timestamp)::date AS order_month,
            COUNT(DISTINCT o.order_id) AS total_orders,
            SUM(i.price + i.freight_value) AS total_revenue,
            AVG(
                CASE
                    WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                    THEN 1 ELSE 0
                END
            ) AS late_delivery_pct
        FROM olist_orders o
        JOIN olist_order_items i
            ON o.order_id = i.order_id
        GROUP BY i.seller_id, order_month
        """)

    return con.sql("SELECT * FROM seller_monthly_kpis").df()

df_kpis = load_kpis()

st.sidebar.header("Month Filter")

available_months = sorted(df_kpis["order_month"].unique())
selected_month = st.sidebar.selectbox("Select month", available_months)

df_month = df_kpis[df_kpis["order_month"] == selected_month].copy()
df_month["red_flag"] = df_month["late_delivery_pct"] > 0.2

st.subheader("Top Sellers by Revenue")
st.dataframe(
    df_month.sort_values("total_revenue", ascending=False),
    use_container_width=True
)

st.subheader("Top Sellers by Orders")
st.dataframe(
    df_month.sort_values("total_orders", ascending=False),
    use_container_width=True
)

st.subheader("Red-Flagged Sellers (>20% Late Delivery)")
df_red = df_month[df_month["red_flag"]]

if df_red.empty:
    st.success("No sellers flagged this month.")
else:
    st.dataframe(df_red, use_container_width=True)
