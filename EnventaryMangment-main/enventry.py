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
            
            st.rerun()  # Force rerun to update the page
        if st.button(" Products registration"):
            st.session_state.view_products = False
            st.session_state.regester = True  # Set session state for product view
            st.rerun()  # Force rerun to update the page

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.view_products = False
            st.rerun()
#product_registration()
# Connect to MySQL
def connect_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

def fetch_recent_entry():
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Enventry ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        return result
    return None
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

def insert_product(product_name, lot_number, manufacture_date, expiry_date):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()

        # Generate QR code
        qr_data = f"{product_name} - {lot_number}"
        qr = qrcode.make(qr_data)
        qr_bytes = BytesIO()
        qr.save(qr_bytes, format="PNG")
        qr_code_data = qr_bytes.getvalue()

        try:
            cursor.execute(
                "INSERT INTO Enventry (ProductName, LotNumber, Mfg, Expire, QRCode) VALUES (%s, %s, %s, %s, %s)",
                (product_name, lot_number, manufacture_date, expiry_date, qr_code_data),
            )
            conn.commit()
            st.success("Product registered successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error inserting data: {e}")
        finally:
            conn.close()

def product_registration():
    st.title("Product Registration")

    product_name = st.text_input("Product Name")
    lot_number = st.text_input("Lot Number")
    manufacture_date = st.date_input("Manufacture Date", datetime.date.today())
    expiry_date = st.date_input("Expiry Date", datetime.date.today())

    if st.button("Submit"):
        insert_product(product_name, lot_number, manufacture_date, expiry_date)

        # Fetch and display the most recent entry
        recent_entry = fetch_recent_entry()

        if recent_entry:
            st.subheader("Most Recent Entry:")
            st.write({key: recent_entry[key] for key in recent_entry if key != "QRCode"})  # Exclude QRCode from print

            # Display QR Code from database
        if recent_entry["QRCode"]:
            st.image(BytesIO(recent_entry["QRCode"]), caption="Product QR Code", use_column_width=False)
    
            # Allow downloading the QR Code
            st.download_button(
                label="Download QR Code",
                data=recent_entry["QRCode"],
                file_name="product_qr.png",
                mime="image/png"
            )
        else:
            st.warning("No data found!")

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
