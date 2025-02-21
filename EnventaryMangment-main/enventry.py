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

if "regester" not in st.session_state:
    st.session_state.regester = False

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
            st.session_state.view_products = True  # Set session state for product view
            st.session_state.regester = False  # Reset registration state
            st.rerun()  # Force rerun to update the page
        if st.button("Product Registration"):
            st.session_state.view_products = False
            st.session_state.regester = True  # Set session state for product view
            st.rerun()  # Force rerun to update the page
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.view_products = False
            st.session_state.regester = False
            st.rerun()

# Connect to MySQL
def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Fetch all product data
def fetch_all_products():
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, ProductName, LotNumber, Mfg, COALESCE(Expire, '0000-00-00') AS Expire, QRCode FROM Enventry ORDER BY id DESC")
        results = cursor.fetchall()
        conn.close()
        return results
    return []    

# Edit Product
def edit_product(product_id, product_name, lot_number, manufacture_date, expiry_date):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE Enventry SET ProductName = %s, LotNumber = %s, Mfg = %s, Expire = %s WHERE id = %s",
                (product_name, lot_number, manufacture_date, expiry_date, product_id)
            )
            conn.commit()
            st.success("Product updated successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error updating data: {e}")
        finally:
            conn.close()

# Delete Product
def delete_product(product_id):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM Enventry WHERE id = %s", (product_id,))
            conn.commit()
            st.success("Product deleted successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error deleting data: {e}")
        finally:
            conn.close()

# Display Products with Edit and Delete Buttons
def display_products():
    st.title("All Registered Products")

    products = fetch_all_products()

    if products:
        # Prepare data for table
        table_data = []
        for product in products:
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

            # Edit and Delete buttons
            edit_button = f'<a href="?edit={product["id"]}">Edit</a>'
            delete_button = f'<a href="?delete={product["id"]}" style="color:red;">Delete</a>'

            # Append product details with buttons
            table_data.append([product_name, lot_number, manufacture_date, expiry_date, href, edit_button, delete_button])

        # Create DataFrame for table
        df = pd.DataFrame(table_data, columns=["Product Name", "Lot Number", "Manufacture Date", "Expiry Date", "Download QR Code", "Edit", "Delete"])

        # Display table with HTML rendering for download links
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    else:
        st.warning("No products found in the database.")

    # Handling Edit and Delete Logic via URL Parameters
    if "edit" in st.experimental_get_query_params():
        product_id = int(st.experimental_get_query_params()["edit"][0])
        product = next((prod for prod in products if prod["id"] == product_id), None)

        if product:
            st.subheader("Edit Product")
            product_name = st.text_input("Product Name", product["ProductName"])
            lot_number = st.text_input("Lot Number", product["LotNumber"])
            manufacture_date = st.date_input("Manufacture Date", datetime.datetime.strptime(product["Mfg"], "%Y-%m-%d").date())
            expiry_date = st.date_input("Expiry Date", datetime.datetime.strptime(product["Expire"], "%Y-%m-%d").date())

            if st.button("Save Changes"):
                edit_product(product_id, product_name, lot_number, manufacture_date, expiry_date)
                st.session_state.view_products = True  # Redirect to the products view
                st.rerun()

    # Handle Delete action
    if "delete" in st.experimental_get_query_params():
        product_id = int(st.experimental_get_query_params()["delete"][0])
        if st.button(f"Are you sure you want to delete product ID {product_id}?"):
            delete_product(product_id)
            st.session_state.view_products = True  # Redirect to the products view
            st.rerun()

# App Flow
if not st.session_state.logged_in:
    login()
else:
    sidebar()

    if st.session_state.view_products:
        display_products()
    elif st.session_state.regester:
        product_registration()
    else:
        product_registration()
