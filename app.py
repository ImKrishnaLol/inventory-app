import streamlit as st
import requests
import pandas as pd
import time

API = "https://inventory-app-mi1m.onrender.com"

st.set_page_config(page_title="Inventory System", layout="wide")

# =========================
# 🔧 UTIL FUNCTIONS
# =========================

def wake_server():
    try:
        requests.get(f"{API}/items", timeout=5)
    except:
        time.sleep(5)

def fetch_items():
    response = requests.get(f"{API}/items")
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Failed to fetch data")
        return pd.DataFrame()

def add_item(data):
    return requests.post(f"{API}/add", json=data)

def update_item(item_id, data):
    return requests.put(f"{API}/update-item/{item_id}", json=data)

def delete_item(item_id):
    return requests.delete(f"{API}/delete-item/{item_id}")

# =========================
# 🧭 NAVIGATION
# =========================

st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", [
    "🏠 Main Menu",
    "🗄️ Database Editor"
])

# =========================
# 🏠 MAIN MENU
# =========================

if page == "🏠 Main Menu":
    st.title("🏠 Inventory System")
    st.info("Control hub (modules coming soon)")

# =========================
# 🗄️ DATABASE EDITOR
# =========================

elif page == "🗄️ Database Editor":

    st.title("🗄️ Database Editor")

    wake_server()
    df = fetch_items()

    if df.empty:
        st.warning("No data found.")
    else:
        st.subheader("📊 Live Table")

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="editor"
        )

        st.divider()

        # =========================
        # 🗑️ DELETE
        # =========================

        st.subheader("🗑️ Delete Item")

        item_to_delete = st.selectbox(
            "Select item",
            df["name"],
            key="delete_select"
        )

        if st.button("Delete", key="delete_btn"):
            item_id = df[df["name"] == item_to_delete]["id"].values[0]

            response = delete_item(item_id)

            if response.status_code == 200:
                st.success("Deleted!")
                st.rerun()
            else:
                st.error(response.text)

        st.divider()

        # =========================
        # 💾 SAVE CHANGES
        # =========================

        if st.button("💾 Save Changes", key="save_btn"):

            changes_made = False

            for i, row in edited_df.iterrows():

                # Existing rows
                if i < len(df):
                    original = df.iloc[i]

                    if not row.equals(original):

                        payload = {
                            "name": row["name"],
                            "shop_category": row["shop_category"],
                            "unit": row["unit"],
                            "unit_factor": int(row["unit_factor"]),
                            "irreplacable": bool(row["irreplacable"]),
                            "current_qty": int(row["current_qty"]),
                            "ideal_qty": int(row["ideal_qty"]),
                            "low_stock_ratio": float(row["low_stock_ratio"]),
                            "consumption_rate": (
                                float(row["consumption_rate"])
                                if pd.notna(row["consumption_rate"])
                                else None
                            )
                        }

                        response = update_item(row["id"], payload)

                        if response.status_code == 200:
                            changes_made = True
                        else:
                            st.error(response.text)

                # New rows
                else:
                    if row["name"]:

                        payload = {
                            "name": row["name"],
                            "shop_category": row.get("shop_category", ""),
                            "unit": row.get("unit", ""),
                            "unit_factor": int(row.get("unit_factor", 1)),
                            "irreplacable": bool(row.get("irreplacable", False)),
                            "current_qty": int(row.get("current_qty", 0)),
                            "ideal_qty": int(row.get("ideal_qty", 0)),
                            "low_stock_ratio": float(row.get("low_stock_ratio", 0.3)),
                            "consumption_rate": (
                                float(row["consumption_rate"])
                                if pd.notna(row.get("consumption_rate"))
                                else None
                            )
                        }

                        response = add_item(payload)

                        if response.status_code == 200:
                            changes_made = True
                        else:
                            st.error(response.text)

            if changes_made:
                st.success("Changes saved!")
                st.rerun()
            else:
                st.info("No changes detected.")

    st.divider()

    # =========================
    # 🔍 SMART FILTER
    # =========================

    st.subheader("🔍 Filter (SQL-like)")

    if not df.empty:

        col1, col2, col3 = st.columns(3)

        column = col1.selectbox("Column", df.columns, key="filter_column")

        is_numeric = pd.api.types.is_numeric_dtype(df[column])

        if is_numeric:
            operator = col2.selectbox("Operator", ["=", "!=", ">", "<"], key="filter_op")
        else:
            operator = col2.selectbox("Operator", ["=", "!=", "contains"], key="filter_op")

        value = col3.text_input("Value", key="filter_val")

        if st.button("Apply Filter", key="filter_btn"):

            try:
                if is_numeric:
                    value = float(value)

                    if operator == "=":
                        filtered = df[df[column] == value]
                    elif operator == "!=":
                        filtered = df[df[column] != value]
                    elif operator == ">":
                        filtered = df[df[column] > value]
                    elif operator == "<":
                        filtered = df[df[column] < value]

                else:
                    if operator == "=":
                        filtered = df[df[column].astype(str) == value]
                    elif operator == "!=":
                        filtered = df[df[column].astype(str) != value]
                    elif operator == "contains":
                        filtered = df[df[column].astype(str).str.contains(value, case=False)]

                st.dataframe(filtered, use_container_width=True)

            except Exception as e:
                st.error(f"Filter error: {e}")
