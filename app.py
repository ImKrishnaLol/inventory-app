import streamlit as st
import pandas as pd
import requests
import time

API = "https://inventory-app-mi1m.onrender.com"

st.set_page_config(page_title="Inventory System", layout="wide")

# =========================
# 🔧 UTILITIES
# =========================
@st.cache_data(ttl=60)
def fetch_items(full=True):
    """Fetch items; full table or minimal for dropdowns."""
    endpoint = "/items" if full else "/items-min"
    resp = requests.get(f"{API}{endpoint}")
    if resp.status_code != 200:
        return pd.DataFrame() if full else []
    data = resp.json()
    return pd.DataFrame(data) if full else data

@st.cache_data(ttl=60)
def fetch_groups(full=True):
    endpoint = "/groups" if full else "/groups-min"
    resp = requests.get(f"{API}{endpoint}")
    if resp.status_code != 200:
        return pd.DataFrame() if full else []
    data = resp.json()
    return pd.DataFrame(data) if full else data

def fetch_group_members(group_id):
    resp = requests.get(f"{API}/group-members/{group_id}")
    return resp.json() if resp.status_code == 200 else []

def wake_server():
    """Ping server to wake it if sleeping."""
    try:
        requests.get(f"{API}/items", timeout=3)
    except:
        time.sleep(3)

def show_message(msg):
    st.session_state.msg = msg
    st.session_state.rerun_needed = True

# =========================
# 🧭 SESSION STATE
# =========================
if "msg" not in st.session_state:
    st.session_state.msg = None
if "rerun_needed" not in st.session_state:
    st.session_state.rerun_needed = False

# =========================
# 🧭 NAVIGATION
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Main Menu", "🗄️ Database Editor", "🗂️ Groups Manager"])

# =========================
# 🏠 MAIN MENU
# =========================
if page == "🏠 Main Menu":
    st.title("🏠 Inventory System")
    st.info("Control hub. Modules coming soon!")

# =========================
# 🗄️ DATABASE EDITOR
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

        # ---------- DELETE ----------
        st.subheader("🗑️ Delete Item")
        item_to_delete = st.selectbox("Select item", df["name"], key="delete_select")
        if st.button("Delete", key="delete_btn"):
            item_id = df[df["name"] == item_to_delete]["id"].values[0]
            resp = requests.delete(f"{API}/delete-item/{item_id}")
            if resp.status_code == 200:
                show_message("Item deleted!")
            else:
                st.error(resp.text)

        st.divider()

        # ---------- SAVE CHANGES (BULK) ----------
        if st.button("💾 Save Changes", key="save_btn"):
            changes = []
            for i, row in edited_df.iterrows():
                if i < len(df) and not row.equals(df.iloc[i]):
                    row_data = row.to_dict()
                    row_data["id"] = df.iloc[i]["id"]
                    changes.append(row_data)
                elif i >= len(df) and row["name"]:
                    changes.append(row.to_dict())
            if changes:
                resp = requests.put(f"{API}/update-items", json=changes)
                if resp.status_code == 200:
                    show_message("Changes saved!")
                else:
                    st.error(resp.text)
            else:
                st.info("No changes detected.")

# =========================
# 🗂️ GROUPS MANAGER
elif page == "🗂️ Groups Manager":
    st.title("🗂️ Groups Manager")
    wake_server()

    # ---------- FETCH GROUPS ----------
    groups = fetch_groups(full=False)
    st.subheader("📋 Existing Groups")
    if not groups:
        st.info("No groups found.")
    else:
        for g in groups:
            st.markdown(f"- **{g['name']}**")

    st.divider()

    # ---------- ADD GROUP ----------
    st.subheader("➕ Add Group")
    new_group_name = st.text_input("Group Name", key="new_group_name")
    new_group_irreplacable = st.checkbox("Irreplacable", key="new_group_irreplacable")
    if st.button("Add Group"):
        if new_group_name:
            resp = requests.post(f"{API}/add-group", json={"name": new_group_name, "irreplacable": new_group_irreplacable})
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

        # Fetch minimal items
        items = fetch_items(full=False)
        item_options = {i['name']: i['id'] for i in items} if items else {}

        st.markdown("**Add a Member**")
        member_type = st.radio("Type", ["Item", "Group"], horizontal=True, key="member_type")

        if member_type == "Item" and item_options:
            selected_item_name = st.selectbox("Select Item", list(item_options.keys()), key="select_item")
            selected_item_id = item_options[selected_item_name]
            if st.button("Add Item to Group", key="add_item_member_btn"):
                resp = requests.post(f"{API}/add-member", json={"group_id": selected_group_id, "item_id": selected_item_id})
                if resp.status_code == 200:
                    show_message(f"Item '{selected_item_name}' added!")
                else:
                    st.error(resp.text)

        # ---------- VIEW MEMBERS ----------
        st.subheader("📄 Group Members")
        members = fetch_group_members(selected_group_id)
        if not members:
            st.info("No members in this group.")
        else:
            for m in members:
                name = m.get("item_name") or f"[Group] {m.get('group_name')}"
                col1, col2 = st.columns([3, 1])
                col1.write(name)
                if col2.button("Remove", key=f"remove_member_{m['id']}"):
                    resp = requests.delete(f"{API}/remove-member/{m['id']}")
                    if resp.status_code == 200:
                        show_message(f"Member '{name}' removed")
                    else:
                        st.error(resp.text)

# =========================
# 🔄 HANDLE RERUN & MESSAGES
# =========================
if st.session_state.rerun_needed:
    st.session_state.rerun_needed = False
    st.rerun()
if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = None
