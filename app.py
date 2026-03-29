import streamlit as st
import requests
import time


# =========================
# CONFIG
# =========================
API = "https://inventory-app-mi1m.onrender.com"

st.set_page_config(page_title="Inventory System", layout="wide")

def wake_server():
    try:
        requests.get(f"{API}/", timeout=5)
    except:
        time.sleep(2)

wake_server()

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

def fetch_group_members(group_id):
    try:
        r = requests.get(f"{API}/groups/{group_id}/members")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def add_member(group_id, data):
    try:
        r = requests.post(f"{API}/groups/{group_id}/members", json=data)
        return r.status_code == 200
    except:
        return False

def delete_member(member_id):
    try:
        r = requests.delete(f"{API}/members/{member_id}")
        return r.status_code == 200
    except:
        return False

def render_tree(group_id, level=0, visited=None):
    if visited is None:
        visited = set()

    # Prevent infinite loops
    if group_id in visited:
        st.write("   " * level + "⚠️ Cycle detected")
        return

    visited.add(group_id)

    members = fetch_group_members(group_id)

    if not members:
        st.write("   " * level + "• (empty)")
        return

    for m in members:
        # ITEM
        if m.get("item_name"):
            st.write("   " * level + f"📦 {m['item_name']}")

        # CHILD GROUP
        elif m.get("group_name"):
            st.write("   " * level + f"📁 {m['group_name']}")

            if m.get("child_group_id"):
                render_tree(m["child_group_id"], level + 1, visited)


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
            st.write(f"- {g['name']} (Ideal: {g.get('ideal_qty', 0)})")

    st.divider()

    # ---------------------
    # ADD GROUP
    # ---------------------
    st.subheader("➕ Add Group")

    new_name = st.text_input("Group Name")
    new_irreplacable = st.checkbox("Irreplacable")
    new_ideal_qty = st.number_input("Ideal Quantity", min_value=0, value=0)

    if st.button("Create Group"):
        if not new_name:
            st.error("Name required")
        else:
            result = create_group({
                "id": None,
                "name": new_name,
                "irreplacable": new_irreplacable,
                "ideal_qty": new_ideal_qty
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
        selected = st.selectbox("Select group", list(group_map.keys()), key="delete_group")

        if st.button("Delete Group"):
            success = delete_group(group_map[selected])

            if success:
                st.success(f"Group '{selected}' deleted")
                st.rerun()
            else:
                st.error("Failed to delete group")
    st.divider()

    # =========================
    # GROUP MEMBERS
    # =========================
    st.subheader("🔗 Manage Members")

    if groups:
        # ---------------------
        # SELECT GROUP
        # ---------------------
        group_map = {g["name"]: g["id"] for g in groups}
        selected_group_name = st.selectbox(
            "Select Group",
            list(group_map.keys()),
            key="member_group"
        )
        selected_group_id = group_map[selected_group_name]

        st.divider()

        # ---------------------
        # ADD MEMBER
        # ---------------------
        st.subheader("➕ Add to Group")

        member_type = st.radio("Type", ["Item", "Group"], horizontal=True)

        # ===== ADD ITEM =====
        if member_type == "Item":
            items = fetch_items()
            item_map = {i["name"]: i["id"] for i in items} if items else {}

            if item_map:
                selected_item_name = st.selectbox(
                    "Select Item",
                    list(item_map.keys()),
                    key="add_item_select"
                )

                if st.button("Add Item"):
                    success = add_member(selected_group_id, {
                        "group_id": selected_group_id,
                        "item_id": item_map[selected_item_name],
                        "child_group_id": None
                    })

                    if success:
                        st.success(f"Added '{selected_item_name}'")
                        st.rerun()
                    else:
                        st.error("Failed to add item")
            else:
                st.info("No items available")

        # ===== ADD GROUP (NESTED) =====
        elif member_type == "Group":
            group_map_full = {g["name"]: g["id"] for g in groups}

            available_groups = {
                name: gid for name, gid in group_map_full.items()
                if gid != selected_group_id
            }

            if available_groups:
                selected_child_name = st.selectbox(
                    "Select Group",
                    list(available_groups.keys()),
                    key="add_group_select"
                )

                if st.button("Add Group"):
                    success = add_member(selected_group_id, {
                        "group_id": selected_group_id,
                        "item_id": None,
                        "child_group_id": available_groups[selected_child_name]
                    })

                    if success:
                        st.success(f"Added group '{selected_child_name}'")
                        st.rerun()
                    else:
                        st.error("Failed to add group")
            else:
                st.info("No other groups available")

        st.divider()

        # ---------------------
        # VIEW MEMBERS
        # ---------------------
        st.subheader("📄 Members")

        members = fetch_group_members(selected_group_id)

        if not members:
            st.info("No members in this group")
        else:
            for m in members:
                name = m["item_name"] or f"[Group] {m['group_name']}"

                col1, col2 = st.columns([3, 1])
                col1.write(name)

                if col2.button("Remove", key=f"remove_{m['id']}"):
                    success = delete_member(m["id"])

                    if success:
                        st.success(f"Removed '{name}'")
                        st.rerun()
                    else:
                        st.error("Failed to remove member")

    # =========================
    # TREE VIEW
    # =========================
    st.divider()
    st.subheader("🌳 Group Tree View")
    
    if groups:
        group_map = {g["name"]: g["id"] for g in groups}
    
        selected_root = st.selectbox(
            "Select Root Group",
            list(group_map.keys()),
            key="tree_root"
        )
    
        st.write("### Structure")
    
        render_tree(group_map[selected_root])
