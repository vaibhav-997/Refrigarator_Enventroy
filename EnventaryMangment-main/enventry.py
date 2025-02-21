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

# Display Products with Edit and Delete Buttons
def display_products():
    st.title("All Registered Products")

    products = fetch_all_products()

    if products:
        # Prepare data for table
        table_data = []
        editable_product_id = st.session_state.get("editable_product_id", None)

        for product in products:
            product_name = product.get("ProductName", "N/A")
            lot_number = product.get("LotNumber", "N/A")
            manufacture_date = product.get("Mfg", "N/A")
            expiry_date = product.get("Expire", "N/A")

            # Create a downloadable link for QR Code
            qr_code_data = product.get("QRCode")
            if qr_code_data:
                b64 = base64.b64encode(qr_code_data).decode()  # Encode as Base64
                href = f'<a href="data:image/png;base64,{b64}" download="QR_{lot_number}.png">Download</a>'
            else:
                href = "No QR Code"

            # Edit and Delete buttons
            edit_button = f'<button onClick="window.location.href=\'#edit_{product["id"]}\'">Edit</button>'
            delete_button = f'<button style="color:red;" onClick="window.location.href=\'#delete_{product["id"]}\'">Delete</button>'

            # Append product details with buttons
            table_data.append([product_name, lot_number, manufacture_date, expiry_date, href, edit_button, delete_button])

        # Create DataFrame for table
        df = pd.DataFrame(table_data, columns=["Product Name", "Lot Number", "Manufacture Date", "Expiry Date", "Download QR Code", "Edit", "Delete"])

        # Display table with HTML rendering for download links
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Handling the form for editing a product
        if editable_product_id:
            editable_product = next(prod for prod in products if prod["id"] == editable_product_id)

            # Editable form for the selected product
            with st.form(key="edit_form"):
                product_name = st.text_input("Product Name", editable_product["ProductName"])
                lot_number = st.text_input("Lot Number", editable_product["LotNumber"])
                manufacture_date = st.date_input("Manufacture Date", datetime.datetime.strptime(editable_product["Mfg"], "%Y-%m-%d").date())
                expiry_date = st.date_input("Expiry Date", datetime.datetime.strptime(editable_product["Expire"], "%Y-%m-%d").date())

                if st.form_submit_button("Save Changes"):
                    edit_product(editable_product["id"], product_name, lot_number, manufacture_date, expiry_date)
                    st.session_state.editable_product_id = None  # Reset editable product id
                    st.experimental_rerun()

    else:
        st.warning("No products found in the database.")

    # Check if a product needs to be edited or deleted (based on URL hash)
    if st.experimental_get_query_params().get("edit"):
        product_id = int(st.experimental_get_query_params()["edit"][0])
        st.session_state["editable_product_id"] = product_id
        st.experimental_rerun()

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
