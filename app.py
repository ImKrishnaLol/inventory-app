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

        # Editable table
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True
        )

        st.divider()

        # =========================
        # 🔄 SAVE CHANGES
        # =========================

        if st.button("💾 Save Changes"):
        changes_made = False
    
        for i, row in edited_df.iterrows():
    
            # Existing rows
            if i < len(df):
                original = df.iloc[i]
    
                # 🔥 Detect ANY change
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
