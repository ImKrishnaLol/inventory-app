import streamlit as st
import requests
import time
from datetime import datetime
import threading

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

def needs_restock(item):
    return True

# =========================
# BACKGROUND UPDATE
# =========================
def update_qty_background(item_id, new_qty):
    """Send the update to backend in a thread."""
    def _update():
        update_item(item_id, {"current_qty": new_qty})
    threading.Thread(target=_update, daemon=True).start()

# =========================
# SAFE SESSION_STATE HELPER
# =========================
def set_qty(key_name, value, item):
    """Safely update session state and trigger background update."""
    st.session_state[key_name] = value
    item_copy = item.copy()
    item_copy["current_qty"] = value
    update_qty_background(item_copy)

# =========================
# SAFE BUTTON CALLBACKS
# =========================
def set_qty_callback(item_id, value):
    key_name = f"qty_{item_id}"
    if key_name not in st.session_state:
        st.session_state[key_name] = value
    else:
        st.session_state[key_name] = value

    # Update in background
    item = next((i for i in st.session_state.get("all_items", []) if i["id"] == item_id), None)
    if item:
        item_copy = item.copy()
        item_copy["current_qty"] = value
        update_qty_background(item_copy)


# =========================
# ITEM NODE COMPONENT
# =========================
def render_item_node(item):
    with st.expander(f"📦 {item['name']}", expanded=False):
        key_name = f"qty_{item['id']}"

        # Initialize session state
        if key_name not in st.session_state:
            st.session_state[key_name] = int(item.get("current_qty", 0))

        # Number input
        new_qty = st.number_input(
            "Update Quantity",
            min_value=0,
            value=st.session_state[key_name],
            step=1,
            key=key_name
        )

        # Detect manual change
        if new_qty != item.get("current_qty"):
            st.session_state[key_name] = new_qty
            update_qty_background(item["id"], new_qty)

        # Quick buttons
        col1, col2 = st.columns(2)

        # Set to 0
        if col1.button("Set to 0", key=f"zero_{item['id']}"):
            st.session_state[key_name] = 0
            update_qty_background(item["id"], 0)

        # Set to Ideal
        ideal_qty = int(item.get("ideal_qty") or 0)
        if col2.button("Set to Ideal", key=f"ideal_{item['id']}"):
            st.session_state[key_name] = ideal_qty
            update_qty_background(item["id"], ideal_qty)

def render_tree(group_id, group_name, items_dict, visited=None):
    """Recursive function to display group tree."""
    if visited is None:
        visited = set()

    if group_id in visited:
        st.warning("Cycle detected")
        return

    visited.add(group_id)
    members = fetch_group_members(group_id)

    with st.expander(f"📁 {group_name}", expanded=False):
        if not members:
            st.write("• (empty)")
            return

        for m in members:
            # Item node
            if m.get("item_id"):
                item = items_dict.get(m["item_id"])
                if item and needs_restock(item):
                    render_item_node(item)

            # Child group node
            elif m.get("child_group_id"):
                child_name = m.get("group_name", "Unnamed Group")
                render_tree(
                    m["child_group_id"],
                    child_name,
                    items_dict,
                    visited.copy()
                )

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
    st.title("🛒 Shopping Overview")

    items = fetch_items()
    groups = fetch_groups()
    items_dict = {item["id"]: item for item in items} if items else {}

    if not items:
        st.info("No items available")
    else:
        st.subheader("📁 Groups")
        seen_items = set()

        if groups:
            for g in groups:
                render_tree(g["id"], g["name"], items_dict)

        st.divider()

        # =========================
        # STANDALONE ITEMS
        # =========================
        st.subheader("📦 Other Items")

        # Mark all items in groups as seen
        for g in groups:
            members = fetch_group_members(g["id"])
            for m in members:
                if m.get("item_id"):
                    seen_items.add(m["item_id"])

        remaining = [
            item for item in items
            if item["id"] not in seen_items and needs_restock(item)
        ]

        if not remaining:
            st.write("✅ Nothing else")
        else:
            for item in remaining:
                render_item_node(item)

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

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 View",
        "➕ Create",
        "✏️ Edit",
        "🔗 Members"
    ])

    # =========================
    # 📋 VIEW
    # =========================
    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("All Groups")

            if not groups:
                st.info("No groups found")
            else:
                st.dataframe(groups, use_container_width=True)

        with col2:
            st.subheader("🗑️ Delete")

            if groups:
                group_map = {g["name"]: g["id"] for g in groups}
                selected = st.selectbox("Select", list(group_map.keys()), key="delete_group")

                if st.button("Delete Group", key="delete_group_btn"):
                    if delete_group(group_map[selected]):
                        st.success("Deleted")
                        st.rerun()
                    else:
                        st.error("Failed")

    # =========================
    # ➕ CREATE
    # =========================
    with tab2:
        st.subheader("Create Group")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Group Name", key="create_name")
            ideal_qty = st.number_input("Ideal Quantity", min_value=0, value=0, key="create_ideal")

        with col2:
            irreplacable = st.checkbox("Irreplacable", key="create_irrep")

        if st.button("Create Group", key="create_btn"):
            if not name:
                st.error("Name required")
            else:
                result = create_group({
                    "id": None,
                    "name": name,
                    "irreplacable": irreplacable,
                    "ideal_qty": ideal_qty
                })

                if result:
                    st.success("Created")
                    st.rerun()
                else:
                    st.error("Failed")

    # =========================
    # ✏️ EDIT
    # =========================
    with tab3:
        st.subheader("Edit Group")

        if not groups:
            st.info("No groups available")
        else:
            group_map = {g["name"]: g for g in groups}

            selected_name = st.selectbox(
                "Select group",
                list(group_map.keys()),
                key="edit_select"
            )
            group = group_map[selected_name]

            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name", value=group["name"], key="edit_name")
                ideal_qty = st.number_input(
                    "Ideal Quantity",
                    min_value=0,
                    value=int(group.get("ideal_qty", 0)),
                    key="edit_ideal"
                )

            with col2:
                irreplacable = st.checkbox(
                    "Irreplacable",
                    value=group["irreplacable"],
                    key="edit_irrep"
                )

            if st.button("Save Changes", key="edit_btn"):
                r = requests.put(
                    f"{API}/groups/{group['id']}",
                    json={
                        "id": group["id"],
                        "name": name,
                        "irreplacable": irreplacable,
                        "ideal_qty": ideal_qty
                    }
                )

                if r.status_code == 200:
                    st.success("Updated")
                    st.rerun()
                else:
                    st.error("Failed to update")

    # =========================
    # 🔗 MEMBERS
    # =========================
    with tab4:
        st.subheader("Manage Group Members")

        if not groups:
            st.info("No groups available")
        else:
            group_map = {g["name"]: g["id"] for g in groups}

            selected_group_name = st.selectbox(
                "Select Group",
                list(group_map.keys()),
                key="member_group"
            )

            selected_group_id = group_map[selected_group_name]

            st.divider()

            # =========================
            # ADD MEMBER
            # =========================
            st.subheader("➕ Add Member")

            member_type = st.radio("Type", ["Item", "Group"], horizontal=True, key="member_type")

            if member_type == "Item":
                items = fetch_items()
                item_map = {i["name"]: i["id"] for i in items} if items else {}

                if item_map:
                    selected_item = st.selectbox(
                        "Select Item",
                        list(item_map.keys()),
                        key="member_item"
                    )

                    if st.button("Add Item to Group", key="add_item_btn"):
                        success = add_member(selected_group_id, {
                            "group_id": selected_group_id,
                            "item_id": item_map[selected_item],
                            "child_group_id": None
                        })

                        if success:
                            st.success("Item added")
                            st.rerun()
                        else:
                            st.error("Failed")
                else:
                    st.info("No items available")

            else:
                available_groups = {
                    name: gid for name, gid in group_map.items()
                    if gid != selected_group_id
                }

                if available_groups:
                    selected_child = st.selectbox(
                        "Select Group",
                        list(available_groups.keys()),
                        key="member_group_add"
                    )

                    if st.button("Add Group to Group", key="add_group_btn"):
                        success = add_member(selected_group_id, {
                            "group_id": selected_group_id,
                            "item_id": None,
                            "child_group_id": available_groups[selected_child]
                        })

                        if success:
                            st.success("Group added")
                            st.rerun()
                        else:
                            st.error("Failed")
                else:
                    st.info("No other groups available")

            st.divider()

            # =========================
            # VIEW MEMBERS
            # =========================
            st.subheader("📄 Current Members")

            members = fetch_group_members(selected_group_id)

            if not members:
                st.info("No members in this group")
            else:
                for m in members:
                    name = m["item_name"] or f"[Group] {m['group_name']}"

                    col1, col2 = st.columns([3, 1])
                    col1.write(name)

                    if col2.button("Remove", key=f"remove_{m['id']}"):
                        if delete_member(m["id"]):
                            st.success("Removed")
                            st.rerun()
                        else:
                            st.error("Failed")
