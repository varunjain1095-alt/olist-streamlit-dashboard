import streamlit as st
import duckdb
import pandas as pd

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Olist | Monthly Seller Performance",
    layout="wide"
)

# --------------------------------------------------
# Title & context
# --------------------------------------------------
st.title("Monthly Seller Performance Overview")
st.caption(
    "Marketing dashboard showing seller revenue, order volume, "
    "and delivery risk indicators."
)

# --------------------------------------------------
# DuckDB connection (READ-ONLY — IMPORTANT ON WINDOWS)
# --------------------------------------------------
@st.cache_resource
def get_connection():
    return duckdb.connect("olist.duckdb", read_only=True)

# --------------------------------------------------
# Load base data
# --------------------------------------------------
@st.cache_data
def load_kpis():
    con = get_connection()
    return con.sql(
        "SELECT * FROM seller_monthly_kpis"
    ).df()

df_kpis = load_kpis()

# --------------------------------------------------
# Sidebar — Filters
# --------------------------------------------------
st.sidebar.header("Filters")

available_months = (
    df_kpis["order_month"]
    .sort_values()
    .unique()
)

selected_month = st.sidebar.selectbox(
    label="Select month",
    options=available_months,
    index=len(available_months) - 1
)

# --------------------------------------------------
# Core business logic (UNCHANGED)
# --------------------------------------------------
df_month = df_kpis[df_kpis["order_month"] == selected_month].copy()
df_month["red_flag"] = df_month["late_delivery_pct"] > 0.2

# --------------------------------------------------
# Section 1 — Top sellers by revenue
# --------------------------------------------------
st.subheader("Top Sellers by Revenue")

df_revenue = (
    df_month
    .sort_values("total_revenue", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(
    df_revenue[
        ["seller_id", "total_revenue", "total_orders", "late_delivery_pct"]
    ],
    use_container_width=True
)

# --------------------------------------------------
# Section 2 — Top sellers by order volume
# --------------------------------------------------
st.subheader("Top Sellers by Order Volume")

df_orders = (
    df_month
    .sort_values("total_orders", ascending=False)
    .reset_index(drop=True)
)

st.dataframe(
    df_orders[
        ["seller_id", "total_orders", "total_revenue", "late_delivery_pct"]
    ],
    use_container_width=True
)

# --------------------------------------------------
# Section 3 — Red-flagged sellers
# --------------------------------------------------
st.subheader("Red-Flagged Sellers (Late Delivery > 20%)")

df_red_flag = df_month[df_month["red_flag"]].copy()

if df_red_flag.empty:
    st.success("No sellers breached the late-delivery threshold for this month.")
else:
    st.dataframe(
        df_red_flag[
            ["seller_id", "late_delivery_pct", "total_orders", "total_revenue"]
        ]
        .sort_values("late_delivery_pct", ascending=False),
        use_container_width=True
    )