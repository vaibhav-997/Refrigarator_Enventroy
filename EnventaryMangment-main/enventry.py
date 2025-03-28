import streamlit as st
import mysql.connector
import datetime
import qrcode
from io import BytesIO
import pandas as pd
import base64

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "view_products" not in st.session_state:
    st.session_state.view_products = False

if "register_product" not in st.session_state:
    st.session_state.register_product = False

if "update_product" not in st.session_state:
    st.session_state.update_product = False  # Ensure this is initialized

# MySQL Database Connection
DB_CONFIG = {
    "host": "82.180.143.66",
    "user": "u263681140_students",
    "password": "testStudents@123",
    "database": "u263681140_students",
}

# Default login credentials
USERNAME = "admin"
PASSWORD = "admin"

# Login Page
def login():
    st.title("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password")

# Sidebar Navigation
def sidebar():
    with st.sidebar:
        st.write("Navigation")
        if st.button("Check Products"):
            st.session_state.view_products = True
            st.session_state.register_product = False
            st.session_state.update_product = False
            st.rerun()

        if st.button("Register Product"):
            st.session_state.view_products = False
            st.session_state.register_product = True
            st.session_state.update_product = False
            st.rerun()

        if st.button("Update Product"):
            st.session_state.view_products = False
            st.session_state.register_product = False
            st.session_state.update_product = True
            st.rerun()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.view_products = False
            st.session_state.register_product = False
            st.session_state.update_product = False
            st.rerun()

# Connect to MySQL
def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Fetch product names for dropdown
def fetch_product_names():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, ProductName FROM Enventry ORDER BY ProductName ASC")
        products = cursor.fetchall()
        conn.close()
        return products
    return []

# Fetch product details by ID
def fetch_product_details(product_id):
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ProductName, LotNumber, Mfg, COALESCE(Expire, '2000-01-01') AS Expire
            FROM Enventry WHERE id = %s
        """, (product_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else {}
    return {}# Update product 
def update_product(product_id, product_name, lot_number, manufacture_date, expiry_date):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Enventry SET ProductName = %s, LotNumber = %s, Mfg = %s, expire = %s WHERE id = %s",
                (product_name, lot_number, manufacture_date, expiry_date, product_id),
            )
            conn.commit()
            st.success("Product updated successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error updating data: {e}")
        finally:
            conn.close()

# Product Update Page
def product_update():
    st.title("Update Product Details")

    # Fetch available products
    products = fetch_product_names()
    if not products:
        st.warning("No products available for updating.")
        return

    product_dict = {name: pid for pid, name in products}
    selected_product_name = st.selectbox("Select Product to Update", list(product_dict.keys()))

    if selected_product_name:
        product_id = product_dict[selected_product_name]
        product_details = fetch_product_details(product_id)

        if product_details:
            new_product_name = st.text_input("Product Name", product_details["ProductName"])
            new_lot_number = st.text_input("Lot Number", product_details["LotNumber"])
            new_manufacture_date = st.date_input("Manufacture Date", datetime.datetime.strptime(product_details["Mfg"], "%Y-%m-%d").date())
            new_expiry_date = st.date_input("Expiry Date", datetime.datetime.strptime(product_details["Expire"], "%Y-%m-%d").date())

            if st.button("Update Product", key="update_product_button"):

                update_product(product_id, new_product_name, new_lot_number, new_manufacture_date, new_expiry_date)
        else:
            st.error("Error fetching product details.")
def fetch_all_products():
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ProductName, LotNumber, Mfg, COALESCE(Expire, '0000-00-00') AS Expire, QRCode FROM Enventry ORDER BY id DESC")
        results = cursor.fetchall()
        conn.close()
        return results
    return []    
# Display Products
def display_products():
    st.title("All Registered Products")

    products = fetch_all_products()

    if products:
        # Debug: Print column names to check their names
        #st.write("Fetched columns:", products[0].keys())

        # Prepare data for table
        table_data = []
        for product in products:
            # Ensure column names exist
            product_name = product.get("ProductName", "N/A")
            lot_number = product.get("LotNumber", "N/A")
            manufacture_date = product.get("Mfg", "N/A")  # Adjust key if different
            expiry_date = product.get("Expire", "N/A")  # Adjust key if different

            # Create a downloadable link for QR Code
            qr_code_data = product.get("QRCode")
            if qr_code_data:
                b64 = base64.b64encode(qr_code_data).decode()  # Encode as Base64
                href = f'<a href="data:image/png;base64,{b64}" download="QR_{lot_number}.png">Download</a>'
            else:
                href = "No QR Code"

            # Append product details along with the download link
            table_data.append([product_name, lot_number, manufacture_date, expiry_date, href])

        # Create DataFrame for table
        df = pd.DataFrame(table_data, columns=["Product Name", "Lot Number", "Manufacture Date", "Expiry Date", "Download QR Code"])

        # Display table with HTML rendering for download links
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    else:
        st.warning("No products found in the database.")
# Product Registration Page
def product_registration():
    st.title("Product Registration")

    product_name = st.text_input("Product Name")
    lot_number = st.text_input("Lot Number")
    manufacture_date = st.date_input("Manufacture Date", datetime.date.today())
    expiry_date = st.date_input("Expiry Date", datetime.date.today())

    if st.button("Submit"):
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Enventry (ProductName, LotNumber, Mfg, Expire) VALUES (%s, %s, %s, %s)",
                    (product_name, lot_number, manufacture_date, expiry_date),
                )
                conn.commit()
                st.success("Product registered successfully!")
            except mysql.connector.Error as e:
                st.error(f"Error inserting data: {e}")
            finally:
                conn.close()

# App Flow
if not st.session_state.logged_in:
    login()
else:
    sidebar()

    if st.session_state.view_products:
        display_products()
    elif st.session_state.register_product:
        product_registration()
    elif st.session_state.update_product:
        product_update()
