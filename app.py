import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="Finance Tracker", layout="wide")
st.title("💰 Personal Finance Tracker (Income + Expenses)")

# ----------------------------
# Session State Init
# ----------------------------
if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=[
        "Date", "Type", "Category", "Description", "Amount", "Payment Method"
    ])

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "user_address" not in st.session_state:
    st.session_state.user_address = ""

# ----------------------------
# Function: Convert to Excel
# ----------------------------
def to_excel(df, name, address):
    output = BytesIO()

    try:
        engine = "xlsxwriter"
        writer = pd.ExcelWriter(output, engine=engine)
    except:
        engine = "openpyxl"
        writer = pd.ExcelWriter(output, engine=engine)

    with writer:
        # Write user details
        info_df = pd.DataFrame({
            "Details": ["Name", "Address"],
            "Value": [name, address]
        })
        info_df.to_excel(writer, index=False, sheet_name="User Info")

        # Write transactions
        df.to_excel(writer, index=False, sheet_name="Transactions")

    return output.getvalue()

# ----------------------------
# Sidebar - Personal Details
# ----------------------------
st.sidebar.header("👤 Personal Details")

st.session_state.user_name = st.sidebar.text_input(
    "Name", value=st.session_state.user_name
)

st.session_state.user_address = st.sidebar.text_area(
    "Address", value=st.session_state.user_address
)

# ----------------------------
# Sidebar - Add Transaction
# ----------------------------
st.sidebar.header("➕ Add Transaction")

with st.sidebar.form("txn_form"):
    date = st.date_input("Date", value=datetime.today())
    txn_type = st.selectbox("Type", ["Income", "Expense"])

    category = st.selectbox("Category", [
        "Salary", "Business", "Food", "Travel", "Shopping",
        "Bills", "Health", "Entertainment", "Rent", "Investment", "Others"
    ])

    description = st.text_input("Description")
    amount = st.number_input("Amount (INR)", min_value=0.0, step=1.0)
    payment = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Bank"])

    submitted = st.form_submit_button("Add Transaction")

    if submitted:
        new_row = pd.DataFrame([{
            "Date": date,
            "Type": txn_type,
            "Category": category,
            "Description": description,
            "Amount": amount,
            "Payment Method": payment
        }])

        st.session_state.transactions = pd.concat(
            [st.session_state.transactions, new_row],
            ignore_index=True
        )

        st.success(f"{txn_type} added successfully!")

# ----------------------------
# Data
# ----------------------------
df = st.session_state.transactions

if df.empty:
    st.info("No transactions yet. Add income or expenses.")
    st.stop()

# ----------------------------
# Balance Calculation
# ----------------------------
income_total = df[df["Type"] == "Income"]["Amount"].sum()
expense_total = df[df["Type"] == "Expense"]["Amount"].sum()
balance = income_total - expense_total

# ----------------------------
# Summary Cards
# ----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Income 💰", f"₹{income_total:.2f}")
col2.metric("Total Expenses 💸", f"₹{expense_total:.2f}")
col3.metric("Balance 🏦", f"₹{balance:.2f}")

st.markdown("---")

# ----------------------------
# Filters
# ----------------------------
st.subheader("🔎 Filters")

col1, col2 = st.columns(2)

with col1:
    type_filter = st.multiselect(
        "Filter by Type",
        options=df["Type"].unique(),
        default=df["Type"].unique()
    )

with col2:
    payment_filter = st.multiselect(
        "Filter by Payment Method",
        options=df["Payment Method"].unique(),
        default=df["Payment Method"].unique()
    )

filtered_df = df[
    (df["Type"].isin(type_filter)) &
    (df["Payment Method"].isin(payment_filter))
]

# ----------------------------
# Table
# ----------------------------
st.subheader("📋 Filtered Transactions")
st.dataframe(filtered_df, use_container_width=True)

# ----------------------------
# Export Buttons
# ----------------------------
st.subheader("📤 Export Reports")

col1, col2 = st.columns(2)

with col1:
    excel_full = to_excel(df, st.session_state.user_name, st.session_state.user_address)
    st.download_button(
        label="⬇️ Download Full Report (Excel)",
        data=excel_full,
        file_name="full_finance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col2:
    excel_filtered = to_excel(filtered_df, st.session_state.user_name, st.session_state.user_address)
    st.download_button(
        label="⬇️ Download Filtered Report (Excel)",
        data=excel_filtered,
        file_name="filtered_finance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ----------------------------
# Charts
# ----------------------------
st.subheader("📊 Insights Dashboard")

col1, col2 = st.columns(2)

with col1:
    cat_df = filtered_df.groupby(["Category", "Type"])["Amount"].sum().reset_index()
    fig1 = px.bar(
        cat_df,
        x="Category",
        y="Amount",
        color="Type",
        barmode="group",
        title="Category-wise Income vs Expenses"
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    pie_df = filtered_df.groupby("Type")["Amount"].sum().reset_index()
    fig2 = px.pie(
        pie_df,
        names="Type",
        values="Amount",
        title="Income vs Expenses Split"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ----------------------------
# Trend Chart
# ----------------------------
st.subheader("📈 Daily Trend")

trend_df = filtered_df.copy()
trend_df["Date"] = pd.to_datetime(trend_df["Date"])
trend_df = trend_df.groupby(["Date", "Type"])["Amount"].sum().reset_index()

fig3 = px.line(
    trend_df,
    x="Date",
    y="Amount",
    color="Type",
    title="Daily Income & Expense Trend"
)

st.plotly_chart(fig3, use_container_width=True)

# ----------------------------
# Reset Data
# ----------------------------
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset All Data"):
    st.session_state.transactions = pd.DataFrame(columns=[
        "Date", "Type", "Category", "Description", "Amount", "Payment Method"
    ])
    st.success("All data cleared!")