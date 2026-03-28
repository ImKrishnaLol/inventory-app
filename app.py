# ===== Streamlit Frontend with Live Updates =====
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
    return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()

def fetch_groups():
    response = requests.get(f"{API}/groups")
    return response.json() if response.status_code == 200 else []

def add_item(data):
    return requests.post(f"{API}/add", json=data)

def update_item(item_id, data):
    return requests.put(f"{API}/update-item/{item_id}", json=data)

def delete_item(item_id):
    return requests.delete(f"{API}/delete-item/{item_id}")

def add_group(data):
    return requests.post(f"{API}/add-group", json=data)

def add_group_member(data):
    return requests.post(f"{API}/add-member", json=data)

def remove_group_member(member_id):
    return requests.delete(f"{API}/remove-member/{member_id}")

def fetch_group_members(group_id):
    response = requests.get(f"{API}/group-members/{group_id}")
    return response.json() if response.status_code == 200 else []

# =========================
# 🧭 SESSION STATE FLAGS
# =========================
if "msg" not in st.session_state:
    st.session_state.msg = None
if "rerun_needed" not in st.session_state:
    st.session_state.rerun_needed = False

# Function to set a message and trigger rerun safely
def show_message(message):
    st.session_state.msg = message
    st.session_state.rerun_needed = True

# =========================
# 🧭 NAVIGATION
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "🏠 Main Menu",
    "🗄️ Database Editor",
    "🗂️ Groups Manager"
])

# =========================
# 🏠 MAIN MENU
# =========================
if page == "🏠 Main Menu":
    st.title("🏠 Inventory System")
    st.info("This is the control hub. Modules coming soon!")

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
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")

        st.divider()

        # ---------- DELETE ITEM ----------
        st.subheader("🗑️ Delete Item")
        item_to_delete = st.selectbox("Select item", df["name"], key="delete_select")
        if st.button("Delete", key="delete_btn"):
            item_id = df[df["name"] == item_to_delete]["id"].values[0]
            resp = delete_item(item_id)
            if resp.status_code == 200:
                show_message("Item deleted!")
            else:
                st.error(resp.text)

        st.divider()

        # ---------- SAVE CHANGES ----------
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
                            "consumption_rate": float(row["consumption_rate"]) if pd.notna(row["consumption_rate"]) else None
                        }
                        resp = update_item(row["id"], payload)
                        if resp.status_code == 200:
                            changes_made = True
                        else:
                            st.error(resp.text)
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
                            "consumption_rate": float(row.get("consumption_rate")) if pd.notna(row.get("consumption_rate")) else None
                        }
                        resp = add_item(payload)
                        if resp.status_code == 200:
                            changes_made = True
                        else:
                            st.error(resp.text)
            if changes_made:
                show_message("Changes saved!")
            else:
                st.info("No changes detected.")

# =========================
# 🗂️ GROUPS MANAGER
# =========================
elif page == "🗂️ Groups Manager":
    st.title("🗂️ Groups Manager")
    wake_server()

    # ---------- FETCH GROUPS ----------
    groups = fetch_groups()
    st.subheader("📋 Existing Groups")
    if not groups:
        st.info("No groups found.")
    else:
        for g in groups:
            st.markdown(f"- **{g['name']}** (Irreplacable: {g['irreplacable']})")

    st.divider()

    # ---------- ADD NEW GROUP ----------
    st.subheader("➕ Add Group")
    new_group_name = st.text_input("Group Name", key="new_group_name")
    new_group_irreplacable = st.checkbox("Irreplacable", key="new_group_irreplacable")
    if st.button("Add Group"):
        if new_group_name:
            resp = add_group({"name": new_group_name, "irreplacable": new_group_irreplacable})
            if resp.status_code == 200:
                show_message(f"Group '{new_group_name}' added!")
            else:
                st.error(resp.text)

    # ---------- ADD/REMOVE MEMBERS ----------
    st.subheader("🔗 Add/Remove Members")
    if groups:
        group_options = {g['name']: g['id'] for g in groups}
        selected_group_name = st.selectbox("Select Group", list(group_options.keys()), key="select_group")
        selected_group_id = group_options[selected_group_name]

        # Items
        df_items = fetch_items()
        item_options = {row["name"]: row["id"] for row in df_items.to_dict(orient="records")} if not df_items.empty else {}

        # Child groups
        child_groups_options = {g['name']: g['id'] for g in groups if g['id'] != selected_group_id}

        st.markdown("**Add a Member**")
        member_type = st.radio("Type", ["Item", "Group"], horizontal=True, key="member_type")

        # Add Item to Group
        if member_type == "Item" and item_options:
            selected_item_name = st.selectbox("Select Item", list(item_options.keys()), key="select_item")
            selected_item_id = item_options[selected_item_name]
            if st.button("Add Item to Group", key="add_item_member_btn"):
                resp = add_group_member({"group_id": selected_group_id, "item_id": selected_item_id, "child_group_id": None})
                if resp.status_code == 200:
                    show_message(f"Item '{selected_item_name}' added to group '{selected_group_name}'")
                else:
                    st.error(resp.text)

        # Add Child Group to Group
        elif member_type == "Group" and child_groups_options:
            selected_child_name = st.selectbox("Select Child Group", list(child_groups_options.keys()), key="select_child_group")
            selected_child_id = child_groups_options[selected_child_name]
            if st.button("Add Group to Group", key="add_group_member_btn"):
                resp = add_group_member({"group_id": selected_group_id, "item_id": None, "child_group_id": selected_child_id})
                if resp.status_code == 200:
                    show_message(f"Group '{selected_child_name}' added to '{selected_group_name}'")
                else:
                    st.error(resp.text)

        st.divider()

        # ---------- VIEW & REMOVE MEMBERS ----------
        st.subheader("📄 Group Members")
        members = fetch_group_members(selected_group_id)
        if not members:
            st.info("No members in this group.")
        else:
            for m in members:
                name = m.get("item_name") if m.get("item_name") else f"[Group] {m.get('group_name')}"
                col1, col2 = st.columns([3,1])
                col1.write(name)
                if col2.button("Remove", key=f"remove_member_{m['id']}"):
                    resp = remove_group_member(m["id"])
                    if resp.status_code == 200:
                        show_message(f"Member '{name}' removed")
                    else:
                        st.error(resp.text)

# =========================
# 🔄 HANDLE RERUN
# =========================
if st.session_state.rerun_needed:
    st.session_state.rerun_needed = False
    st.rerun()
if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = None
