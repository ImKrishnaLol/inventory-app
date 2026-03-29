import streamlit as st
import pandas as pd
import requests
import numpy as np
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

API = "https://inventory-app-mi1m.onrender.com"
executor = ThreadPoolExecutor(max_workers=5)

# =========================
# UTILITIES
# =========================
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

def sanitize_row(row):
    return {k: (int(v) if isinstance(v,np.integer)
                else float(v) if isinstance(v,np.floating)
                else bool(v) if isinstance(v,bool)
                else str(v) if isinstance(v,str)
                else v)
            for k,v in row.items() if k not in ["_changed"]}

def save_changes_bulk(df):
    changes = [sanitize_row(r) for _, r in df.iterrows() if r.get("_changed")]
    if not changes: return
    r = requests.put(f"{API}/update-items", json=changes)
    if r.status_code==200: show_message("Changes saved!")
    else: st.error("Failed to save changes: "+r.text)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Inventory System", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Main Menu", "🗄️ Database Editor", "🗂️ Groups Manager"])

if "edited_df" not in st.session_state: st.session_state.edited_df = pd.DataFrame()
if "msg" not in st.session_state: st.session_state.msg = None
if "rerun_needed" not in st.session_state: st.session_state.rerun_needed = False

# =========================
# MAIN MENU
# =========================
if page=="🏠 Main Menu":
    st.title("🏠 Inventory System")
    st.info("Control hub. Modules coming soon!")

# =========================
# DATABASE EDITOR
elif page=="🗄️ Database Editor":
    st.title("🗄️ Database Editor")
    df_future = executor.submit(fetch_items)
    df = df_future.result()

    default_row = {
        "id": str(uuid4()),
        "name": "", "shop_category": "", "unit": "", "unit_factor":1,
        "irreplacable":False, "current_qty":0, "ideal_qty":0,
        "low_stock_ratio":0.3, "consumption_rate":0.01, "last_updated":""
    }

    if df.empty and st.session_state.edited_df.empty:
        st.session_state.edited_df = pd.DataFrame([default_row])
    elif not df.empty and st.session_state.edited_df.empty:
        st.session_state.edited_df = df.copy()

    # ➕ Add new row
    st.subheader("➕ Add New Row")
    if st.button("➕ Add New Row"):
        save_changes_bulk(st.session_state.edited_df)
        r = requests.post(f"{API}/add-item", json=default_row)
        if r.status_code==200:
            new_row = r.json()
            new_row["_changed"] = True
            st.session_state.edited_df = pd.concat([st.session_state.edited_df, pd.DataFrame([new_row])], ignore_index=True)
            st.rerun()
        else: st.error("Failed to add new row: "+r.text)

    # Editable table
    st.subheader("📊 Live Table")
    edited_df = st.data_editor(
        st.session_state.edited_df,
        num_rows="dynamic",
        use_container_width=True
    )

    # Track changes
    for idx, row in edited_df.iterrows():
        orig = df[df["id"]==row.get("id")]
        st.session_state.edited_df.at[idx,"_changed"] = True if orig.empty else not row.equals(orig.iloc[0])
    st.session_state.edited_df = edited_df

    # Manual save
    st.subheader("💾 Save Changes")
    if st.button("Save Changes"):
        save_changes_bulk(st.session_state.edited_df)
        df = fetch_items()
        st.session_state.edited_df = df.copy()

# =========================
# GROUPS MANAGER
elif page=="🗂️ Groups Manager":
    st.title("🗂️ Groups Manager")
    groups = fetch_groups(full=False)

    st.subheader("📋 Existing Groups")
    if not groups: st.info("No groups found.")
    else:
        for g in groups:
            st.markdown(f"- **{g['name']}**")

    st.divider()
    # ➕ Add Group
    st.subheader("➕ Add Group")
    new_group_name = st.text_input("Group Name")
    new_group_irreplacable = st.checkbox("Irreplacable")
    if st.button("Add Group"):
        if new_group_name:
            r = requests.post(f"{API}/add-group", json={"name":new_group_name,"irreplacable":new_group_irreplacable})
            if r.status_code==200: show_message(f"Group '{new_group_name}' added!"); groups = fetch_groups(full=False)
            else: st.error(r.text)

    # 🗑️ Delete Group
    st.subheader("🗑️ Delete Group")
    if groups:
        selected_group_name = st.selectbox("Select Group to Delete", [g["name"] for g in groups])
        selected_group = next(g for g in groups if g["name"]==selected_group_name)
        if st.button("Delete Group"):
            r = requests.delete(f"{API}/delete-group/{selected_group['id']}")
            if r.status_code==200: show_message(f"Group '{selected_group_name}' deleted!"); groups = fetch_groups(full=False)
            else: st.error(r.text)

    st.divider()
    # 🔗 Add/Remove Members
    st.subheader("🔗 Add/Remove Members")
    if groups:
        selected_group_name = st.selectbox("Select Group", [g["name"] for g in groups], key="select_group_members")
        selected_group = next(g for g in groups if g["name"]==selected_group_name)
        selected_group_id = selected_group["id"]

        items = fetch_items(full=False)
        item_options = {i["name"]:i["id"] for i in items} if items else {}

        member_type = st.radio("Type", ["Item","Group"], horizontal=True)
        if member_type=="Item" and item_options:
            selected_item_name = st.selectbox("Select Item", list(item_options.keys()))
            selected_item_id = item_options[selected_item_name]
            if st.button("Add Item to Group"):
                r = requests.post(f"{API}/add-member", json={"group_id":selected_group_id,"item_id":selected_item_id})
                if r.status_code==200: show_message(f"Item '{selected_item_name}' added!")
                else: st.error(r.text)

        st.subheader("📄 Group Members")
        members = fetch_group_members(selected_group_id)
        if not members: st.info("No members in this group.")
        else:
            for m in members:
                name = m.get("item_name") or f"[Group] {m.get('group_name')}"
                c1,c2 = st.columns([3,1])
                c1.write(name)
                if c2.button("Remove", key=f"remove_member_{m['id']}"):
                    r = requests.delete(f"{API}/remove-member/{m['id']}")
                    if r.status_code==200: show_message(f"Member '{name}' removed")
                    else: st.error(r.text)

# =========================
# RERUN & MESSAGES
# =========================
if st.session_state.rerun_needed: st.session_state.rerun_needed=False; st.rerun()
if st.session_state.msg: st.success(st.session_state.msg); st.session_state.msg=None
