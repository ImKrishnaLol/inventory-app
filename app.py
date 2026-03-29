import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

API = "https://inventory-app-mi1m.onrender.com"

st.set_page_config(page_title="Inventory System", layout="wide")

# =========================
# UTILITIES
# =========================
executor = ThreadPoolExecutor(max_workers=5)

@st.cache_data(ttl=60)
def fetch_items(full=True):
    endpoint = "/items" if full else "/items-min"
    r = requests.get(f"{API}{endpoint}")
    if r.status_code != 200: return pd.DataFrame() if full else []
    data = r.json()
    return pd.DataFrame(data) if full else data

@st.cache_data(ttl=60)
def fetch_groups(full=True):
    endpoint = "/groups" if full else "/groups-min"
    r = requests.get(f"{API}{endpoint}")
    if r.status_code != 200: return pd.DataFrame() if full else []
    data = r.json()
    return pd.DataFrame(data) if full else data

def fetch_group_members(group_id):
    r = requests.get(f"{API}/group-members/{group_id}")
    return r.json() if r.status_code==200 else []

def show_message(msg):
    st.session_state.msg = msg
    st.session_state.rerun_needed = True

# =========================
# SESSION STATE
# =========================
if "msg" not in st.session_state: st.session_state.msg = None
if "rerun_needed" not in st.session_state: st.session_state.rerun_needed = False

# =========================
# NAVIGATION
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Main Menu", "🗄️ Database Editor", "🗂️ Groups Manager"])

# =========================
# MAIN MENU
# =========================
if page=="🏠 Main Menu":
    st.title("🏠 Inventory System")
    st.info("Control hub. Modules coming soon!")

# =========================
# DATABASE EDITOR
# =========================
elif page=="🗄️ Database Editor":
    st.title("🗄️ Database Editor")
    df_future = executor.submit(fetch_items)
    df = df_future.result()

    # Default row template matching Item model defaults
    default_row = {
        "name": "",
        "shop_category": "",
        "unit": "",
        "unit_factor": 1,
        "irreplacable": False,
        "current_qty": 0,
        "ideal_qty": 0,
        "low_stock_ratio": 0.3,
        "consumption_rate": None,
        "last_updated": ""
    }

    if df.empty:
        st.warning("No data found.")
        # Start with one default row
        df = pd.DataFrame([default_row])
    
    st.subheader("📊 Live Table")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # ➕ ADD NEW ROW BUTTON
    if st.button("➕ Add New Row"):
        # Append a new row with defaults
        edited_df = pd.concat([edited_df, pd.DataFrame([default_row])], ignore_index=True)
        st.rerun()  # rerun to update the editor with the new row

    st.divider()
    
    # DELETE ITEM
    st.subheader("🗑️ Delete Item")
    if not df.empty:
        item_to_delete = st.selectbox("Select item", df["name"])
        if st.button("Delete"):
            item_id = df[df["name"]==item_to_delete]["id"].values[0]
            r = requests.delete(f"{API}/delete-item/{item_id}")
            if r.status_code==200: show_message("Item deleted!")
            else: st.error(r.text)

    st.divider()
    
    # SAVE CHANGES BULK
    if st.button("💾 Save Changes"):
        changes=[]
        for i,row in edited_df.iterrows():
            if i<len(df) and not row.equals(df.iloc[i]):
                d=row.to_dict(); d["id"]=df.iloc[i]["id"]; changes.append(d)
            elif i>=len(df) and row["name"]: changes.append(row.to_dict())
        if changes:
            r=requests.put(f"{API}/update-items", json=changes)
            if r.status_code==200: show_message("Changes saved!")
            else: st.error(r.text)
        else: st.info("No changes detected.")

# =========================
# GROUPS MANAGER
# =========================
elif page=="🗂️ Groups Manager":
    st.title("🗂️ Groups Manager")
    groups = fetch_groups(full=False)  # list of dicts

    # Existing Groups
    st.subheader("📋 Existing Groups")
    if not groups: 
        st.info("No groups found.")
    else:
        for g in groups:
            st.markdown(f"- **{g['name']}**")

    st.divider()
    
    # ADD GROUP
    st.subheader("➕ Add Group")
    new_group_name = st.text_input("Group Name")
    new_group_irreplacable = st.checkbox("Irreplacable")
    if st.button("Add Group"):
        if new_group_name:
            r = requests.post(f"{API}/add-group", json={
                "name": new_group_name,
                "irreplacable": new_group_irreplacable
            })
            if r.status_code == 200: show_message(f"Group '{new_group_name}' added!")
            else: st.error(r.text)

    # DELETE GROUP
    st.subheader("🗑️ Delete Group")
    if groups:
        group_names = [g["name"] for g in groups]
        selected_group_name = st.selectbox("Select Group to Delete", group_names)
        selected_group = next(g for g in groups if g["name"]==selected_group_name)
        if st.button("Delete Group"):
            r = requests.delete(f"{API}/delete-group/{selected_group['id']}")
            if r.status_code == 200: show_message(f"Group '{selected_group_name}' deleted!")
            else: st.error(r.text)

    st.divider()
    
    # MEMBERS MANAGEMENT
    st.subheader("🔗 Add/Remove Members")
    if groups:
        selected_group_name = st.selectbox("Select Group", [g["name"] for g in groups], key="select_group_members")
        selected_group = next(g for g in groups if g["name"]==selected_group_name)
        selected_group_id = selected_group["id"]

        # Items for adding
        items = fetch_items(full=False)
        item_options = {i["name"]: i["id"] for i in items} if items else {}

        # Add Item or Group as member
        member_type = st.radio("Type", ["Item","Group"], horizontal=True)
        if member_type=="Item" and item_options:
            selected_item_name = st.selectbox("Select Item", list(item_options.keys()))
            selected_item_id = item_options[selected_item_name]
            if st.button("Add Item to Group"):
                r = requests.post(f"{API}/add-member", json={
                    "group_id": selected_group_id,
                    "item_id": selected_item_id
                })
                if r.status_code == 200: show_message(f"Item '{selected_item_name}' added!")
                else: st.error(r.text)

        # VIEW MEMBERS
        st.subheader("📄 Group Members")
        members = fetch_group_members(selected_group_id)
        if not members: st.info("No members in this group.")
        else:
            for m in members:
                name = m.get("item_name") or f"[Group] {m.get('group_name')}"
                c1, c2 = st.columns([3,1])
                c1.write(name)
                if c2.button("Remove", key=f"remove_member_{m['id']}"):
                    r = requests.delete(f"{API}/remove-member/{m['id']}")
                    if r.status_code == 200: show_message(f"Member '{name}' removed")
                    else: st.error(r.text)
# =========================
# HANDLE RERUN & MESSAGES
# =========================
if st.session_state.rerun_needed:
    st.session_state.rerun_needed=False
    st.rerun()
if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg=None
