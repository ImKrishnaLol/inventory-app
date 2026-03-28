import streamlit as st
import requests

API = "https://inventory-app-mi1m.onrender.com"

st.title("🏠 Home Inventory")

menu = st.sidebar.selectbox("Menu", [
    "View Items", "Add Item", "Update Quantity", "Low Stock"
])

if menu == "View Items":
    data = requests.get(f"{API}/items").json()
    st.write(data)

elif menu == "Add Item":
    name = st.text_input("Item Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=0)
    threshold = st.number_input("Threshold", min_value=0)

    if st.button("Add"):
        requests.post(f"{API}/add", json={
            "name": name,
            "category": category,
            "quantity": quantity,
            "threshold": threshold
        })
        st.success("Item Added!")

elif menu == "Update Quantity":
    name = st.text_input("Item Name")
    quantity = st.number_input("New Quantity", min_value=0)

    if st.button("Update"):
        requests.post(f"{API}/update/{name}?quantity={quantity}")
        st.success("Updated!")

elif menu == "Low Stock":
    data = requests.get(f"{API}/low-stock").json()
    st.write(data)
