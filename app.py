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

def update_item(name, quantity):
    return requests.post(f"{API}/update/{name}?quantity={quantity}")

def add_item(data):
    return requests.post(f"{API}/add", json=data)

# =========================
# 🧭 NAVIGATION
# =========================

st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", [
    "🏠 Main Menu",
    "🗄️ Database Editor"
])

# =========================
# 🏠 MAIN MENU (EMPTY HUB)
# =========================

if page == "🏠 Main Menu":
    st.title("🏠 Inventory System")

    st.info("This is your control hub.\n\nMore modules will be added here.")

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
        # 🗑️ DELETE ROW
        # =========================

        st.subheader("🗑️ Delete Item")

        item_to_delete = st.selectbox("Select item to delete", df["name"])

        if st.button("Delete"):
            item_id = df[df["name"] == item_to_delete]["id"].values[0]

            response = requests.delete(f"{API}/delete-item/{item_id}")

            if response.status_code == 200:
                st.success("Deleted!")
                st.rerun()
            else:
                st.error(response.text)

        st.divider()

        # =========================
        # 💾 SAVE CHANGES
        # =========================

        if st.button("💾 Save Changes"):
            changes_made = False

            for i, row in edited_df.iterrows():

                # Existing rows
                if i < len(df):
                    original = df.iloc[i]

                    if not row.equals(original):
                        response = requests.put(
                            f"{API}/update-item/{row['id']}",
                            json={
                                "name": row["name"],
                                "category": row["category"],
                                "quantity": int(row["quantity"]),
                                "threshold": int(row["threshold"])
                            }
                        )

                        if response.status_code == 200:
                            changes_made = True
                        else:
                            st.error(response.text)

                # New rows
                else:
                    if row["name"]:
                        response = requests.post(f"{API}/add", json={
                            "name": row["name"],
                            "category": row.get("category", ""),
                            "quantity": int(row.get("quantity", 0)),
                            "threshold": int(row.get("threshold", 0))
                        })

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
    # 🔍 ADVANCED FILTER
    # =========================
    
    st.subheader("🔍 Filter (SQL-like)")
    
    if not df.empty:
    
        col1, col2, col3 = st.columns(3)
    
        column = col1.selectbox("Column", df.columns, key="filter_column")
        operator = col2.selectbox(
            "Operator",
            ["=", "!=", ">", "<", "contains"],
            key="filter_operator"
        )
        value = col3.text_input("Value", key="filter_value")
    
        if st.button("Apply Filter", key="filter_button"):
    
            try:
                if operator == "=":
                    filtered = df[df[column] == value]
    
                elif operator == "!=":
                    filtered = df[df[column] != value]
    
                elif operator == ">":
                    filtered = df[df[column].astype(float) > float(value)]
    
                elif operator == "<":
                    filtered = df[df[column].astype(float) < float(value)]
    
                elif operator == "contains":
                    filtered = df[df[column].astype(str).str.contains(value, case=False)]
    
                st.dataframe(filtered, use_container_width=True)
    
            except Exception as e:
                st.error(f"Invalid filter: {e}")
    # =========================
    # 🔍 BASIC FILTER (EXTENDABLE)
    # =========================

    st.subheader("🔍 Filter View")

    if not df.empty:
        col = st.selectbox("Column", df.columns)
        value = st.text_input("Value contains")

        if value:
            filtered = df[df[col].astype(str).str.contains(value, case=False)]
            st.dataframe(filtered, use_container_width=True)
