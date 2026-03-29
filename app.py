import streamlit as st
import requests

# =========================
# CONFIG
# =========================
API = "https://inventory-app-mi1m.onrender.com"

st.set_page_config(page_title="Inventory System", layout="wide")

# =========================
# API FUNCTIONS
# =========================
def check_api():
    try:
        r = requests.get(f"{API}/")
        return r.json() if r.status_code == 200 else None
    except:
        return None

def check_db():
    try:
        r = requests.get(f"{API}/test-db")
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fetch_items():
    try:
        r = requests.get(f"{API}/items")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def create_item(item_data):
    try:
        r = requests.post(f"{API}/items", json=item_data)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def delete_item(item_id):
    try:
        r = requests.delete(f"{API}/items/{item_id}")
        return r.status_code == 200
    except:
        return False

def update_item(item_id, item_data):
    try:
        r = requests.put(f"{API}/items/{item_id}", json=item_data)
        return r.status_code == 200
    except:
        return False

def fetch_groups():
    try:
        r = requests.get(f"{API}/groups")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def create_group(data):
    try:
        r = requests.post(f"{API}/groups", json=data)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def delete_group(group_id):
    try:
        r = requests.delete(f"{API}/groups/{group_id}")
        return r.status_code == 200
    except:
        return False

# =========================
# NAVIGATION
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "⚙️ System Status", "📦 Items", "➕ Add Item", "✏️ Edit Item", "🗂️ Groups"]
)

# =========================
# HOME PAGE
# =========================
if page == "🏠 Home":
    st.title("🏠 Inventory System")
    st.write("Clean base setup. Features will be added step by step.")
    st.info("Use the sidebar to navigate.")

# =========================
# SYSTEM STATUS PAGE
# =========================
elif page == "⚙️ System Status":
    st.title("⚙️ System Status")

    # API STATUS
    st.subheader("Backend API")
    api_status = check_api()
    if api_status:
        st.success("API is running")
        st.json(api_status)
    else:
        st.error("API is not reachable")

    st.divider()

    # DATABASE STATUS
    st.subheader("Database Connection")
    db_status = check_db()
    if db_status:
        st.success("Database connected")
        st.json(db_status)
    else:
        st.error("Database not reachable")

# =========================
# ITEMS PAGE
# =========================
elif page == "📦 Items":
    st.title("📦 Items")

    items = fetch_items()

    if not items:
        st.info("No items found.")
    else:
        st.success(f"{len(items)} items loaded")

        # Show table
        st.dataframe(items, use_container_width=True)

        st.divider()

        # DELETE SECTION
        st.subheader("🗑️ Delete Item")

        item_options = {item["name"]: item["id"] for item in items}

        selected_name = st.selectbox("Select item to delete", list(item_options.keys()))
        selected_id = item_options[selected_name]

        if st.button("Delete Item"):
            success = delete_item(selected_id)

            if success:
                st.success(f"Item '{selected_name}' deleted")
                st.rerun()
            else:
                st.error("Failed to delete item")

# =========================
# ADD ITEM PAGE
# =========================
elif page == "➕ Add Item":
    st.title("➕ Add Item")

    name = st.text_input("Name")
    category = st.text_input("Shop Category",value="Groceries")
    unit = st.text_input("Unit")

    unit_factor = st.number_input("Unit Factor", min_value=1, value=1)
    irreplacable = st.checkbox("Irreplacable")

    current_qty = st.number_input("Current Quantity", min_value=0, value=0)
    ideal_qty = st.number_input("Ideal Quantity", min_value=0, value=0)

    low_stock_ratio = st.slider("Low Stock Ratio", 0.0, 1.0, 0.3)
    consumption_rate = st.number_input("Consumption Rate", min_value=0, value=30)

    if st.button("Add Item"):
        if not name:
            st.error("Name is required")
        else:
            item_data = {
                "id":None,
                "name": name,
                "shop_category": category,
                "unit": unit,
                "unit_factor": unit_factor,
                "irreplacable": irreplacable,
                "current_qty": current_qty,
                "ideal_qty": ideal_qty,
                "low_stock_ratio": low_stock_ratio,
                "consumption_rate": consumption_rate
            }

            result = create_item(item_data)

            if result:
                st.success(f"Item '{name}' added successfully!")
            else:
                st.error("Failed to add item")

# =========================
# EDIT ITEM PAGE
# =========================
elif page == "✏️ Edit Item":
    st.title("✏️ Edit Item")

    items = fetch_items()

    if not items:
        st.info("No items available")
    else:
        item_map = {item["name"]: item for item in items}
        selected_name = st.selectbox("Select item", list(item_map.keys()))
        item = item_map[selected_name]

        st.subheader("Edit Details")

        name = st.text_input("Name", value=item["name"])
        category = st.text_input("Shop Category", value=item["shop_category"])
        unit = st.text_input("Unit", value=item["unit"])

        unit_factor = st.number_input("Unit Factor", min_value=1, value=item["unit_factor"])
        irreplacable = st.checkbox("Irreplacable", value=item["irreplacable"])

        current_qty = st.number_input("Current Quantity", min_value=0, value=item["current_qty"])
        ideal_qty = st.number_input("Ideal Quantity", min_value=0, value=item["ideal_qty"])

        low_stock_ratio = st.slider("Low Stock Ratio", 0.0, 1.0, float(item["low_stock_ratio"]))
        consumption_rate = st.number_input("Consumption Rate", min_value=0.0001, value=float(item["consumption_rate"]))

        if st.button("Save Changes"):
            updated_data = {
                "id":item["id"],
                "name": name,
                "shop_category": category,
                "unit": unit,
                "unit_factor": unit_factor,
                "irreplacable": irreplacable,
                "current_qty": current_qty,
                "ideal_qty": ideal_qty,
                "low_stock_ratio": low_stock_ratio,
                "consumption_rate": consumption_rate
            }

            success = update_item(item["id"], updated_data)

            if success:
                st.success(f"Item '{name}' updated!")
                st.rerun()
            else:
                st.error("Failed to update item")

# =========================
# GROUPS PAGE
# =========================
elif page == "🗂️ Groups":
    st.title("🗂️ Groups")

    groups = fetch_groups()

    # ---------------------
    # VIEW GROUPS
    # ---------------------
    st.subheader("📋 Existing Groups")

    if not groups:
        st.info("No groups found")
    else:
        for g in groups:
            st.write(f"- {g['name']}")

    st.divider()

    # ---------------------
    # ADD GROUP
    # ---------------------
    st.subheader("➕ Add Group")

    new_name = st.text_input("Group Name")
    new_irreplacable = st.checkbox("Irreplacable")

    if st.button("Create Group"):
        if not new_name:
            st.error("Name required")
        else:
            result = create_group({
                "name": new_name,
                "irreplacable": new_irreplacable
            })

            if result:
                st.success(f"Group '{new_name}' created")
                st.rerun()
            else:
                st.error("Failed to create group")

    st.divider()

    # ---------------------
    # DELETE GROUP
    # ---------------------
    st.subheader("🗑️ Delete Group")

    if groups:
        group_map = {g["name"]: g["id"] for g in groups}
        selected = st.selectbox("Select group", list(group_map.keys()))

        if st.button("Delete Group"):
            success = delete_group(group_map[selected])

            if success:
                st.success(f"Group '{selected}' deleted")
                st.rerun()
            else:
                st.error("Failed to delete group")
