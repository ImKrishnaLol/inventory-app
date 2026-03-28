import streamlit as st
import requests
import pandas as pd
import time

API = "https://inventory-app-mi1m.onrender.com"

st.set_page_config(page_title="Home Inventory", layout="wide")

st.title("🏠 Home Inventory")

# 🔄 Wake up backend (Render sleep fix)
with st.spinner("Connecting to server..."):
    try:
        requests.get(f"{API}/items", timeout=5)
    except:
        time.sleep(5)

# 🔄 Fetch data
def fetch_items():
    try:
        response = requests.get(f"{API}/items")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error("Failed to fetch data")
            return pd.DataFrame()
    except:
        st.error("Server not responding")
        return pd.DataFrame()

df = fetch_items()

# 🔍 SEARCH
search = st.text_input("🔍 Search item")

if not df.empty and search:
    df = df[df["name"].str.contains(search, case=False)]

# ⚠️ Highlight low stock
def highlight_low_stock(row):
    return ['background-color: #ffcccc' if row.quantity < row.threshold else '' for _ in row]

st.subheader("📦 Inventory")

if not df.empty:
    st.dataframe(df.style.apply(highlight_low_stock, axis=1), use_container_width=True)
else:
    st.warning("No items found")

st.divider()

# ➕ ADD ITEM
st.subheader("➕ Add Item")

with st.form("add_form"):
    col1, col2, col3, col4 = st.columns(4)

    name = col1.text_input("Name")
    category = col2.text_input("Category")
    quantity = col3.number_input("Quantity", min_value=0)
    threshold = col4.number_input("Threshold", min_value=0)

    submitted = st.form_submit_button("Add Item")

    if submitted:
        response = requests.post(f"{API}/add", json={
            "name": name,
            "category": category,
            "quantity": quantity,
            "threshold": threshold
        })

        if response.status_code == 200:
            st.success("Item added!")
            st.rerun()
        else:
            st.error(response.text)

# 🔄 UPDATE ITEM
st.subheader("🔄 Update Quantity")

if not df.empty:
    item_names = df["name"].tolist()

    col1, col2 = st.columns(2)

    selected_item = col1.selectbox("Select Item", item_names)
    new_qty = col2.number_input("New Quantity", min_value=0)

    if st.button("Update Quantity"):
        response = requests.post(f"{API}/update/{selected_item}?quantity={new_qty}")

        if response.status_code == 200:
            st.success("Updated!")
            st.rerun()
        else:
            st.error(response.text)

st.divider()

# ⚠️ LOW STOCK
st.subheader("⚠️ Low Stock")

if not df.empty:
    low = df[df["quantity"] < df["threshold"]]

    if not low.empty:
        st.dataframe(low, use_container_width=True)
    else:
        st.success("All items are sufficiently stocked!")
