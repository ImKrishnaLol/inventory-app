import streamlit as st
import requests

# =========================
# CONFIG
# =========================
API = "http://127.0.0.1:8000"

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

# =========================
# NAVIGATION
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home", "⚙️ System Status"])

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
