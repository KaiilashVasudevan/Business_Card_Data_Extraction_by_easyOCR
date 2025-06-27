import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit_authenticator as stauth
import easyocr
import psycopg2
import psycopg2.extras
from psycopg2 import DatabaseError
import re
import io
from PIL import Image

# User Login Authentication
names = ["Administrator", "Manager"]
usernames = ["admin", "manager"]

# Loading Hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
# Read the file in read binary mode and load the pickle file
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

# Home Page Title
st.set_page_config(page_title="BizCardX_ Extracting Business Card Data with OCR", layout="wide")

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                                    'BizCardX Project Menu', 'guvi', cookie_expiry_days=30)

names, authentication_status, username = authenticator.login("Login", "main")

# Initialize DataBase connection.
# Uses st.cache_resource to only run once, for models, connection, tools.
@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

# 2. DB Operations
# -------------------------
def create_table():
    conn = init_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS CUSTOMERS (CUSTOMER_ID SERIAL PRIMARY KEY, NAME VARCHAR(50), DESIGNATION
            VARCHAR(50),COMPANY_NAME VARCHAR(50), CONTACT VARCHAR(50), EMAIL VARCHAR(50),
            WEBSITE VARCHAR(50), ADDRESS TEXT, PINCODE VARCHAR(50), BIZ_CARD BYTEA);""")
        conn.commit()
    except DatabaseError as e:
        conn.rollback()
        st.error(f"Database Error: {e}")
    finally:
        cur.close()

# conn = init_connection()
# cur = conn.cursor()
def insert_card(insert_final_values):
    conn = init_connection()
    try:
        cur = conn.cursor()
        insert_script = "INSERT INTO CUSTOMERS (NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, " \
                        "WEBSITE, ADDRESS, PINCODE, BIZ_CARD) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cur.execute(insert_script, insert_final_values)
        conn.commit()
    except DatabaseError as e:
        conn.rollback()
        st.error(f"Insert Failed: {e}")
    finally:
        cur.close()

def add_new_customer(name,designation,company,contact,email,website,add,pin):
    conn = init_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO CUSTOMERS (NAME,DESIGNATION,COMPANY_NAME,contact,email,website,addRESS,pinCODE) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (name,designation,company,contact,email,website,add,pin));
            conn.commit()
            st.success("Customer Added Successfully !")
    except DatabaseError as e:
        conn.rollback()
        st.error(f"Insert Failed: {e}")
    finally:
        cur.close()

def update_card(updated_final_values):
    conn = init_connection()
    try:
        cur = conn.cursor()
        update_script = ("UPDATE CUSTOMERS SET NAME = %s, DESIGNATION = %s,COMPANY_NAME = %s, CONTACT=%s, EMAIL=%s, "
                         "WEBSITE=%s, ADDRESS = %s, PINCODE = %s WHERE NAME =%s;")
        cur.execute(update_script, updated_final_values)
        conn.commit()
    except DatabaseError as e:
        conn.rollback()
        st.error(f"Update Failed: {e}")
    finally:
        cur.close()

def delete_card(selected_name):
    conn = init_connection()
    try:
        cur = conn.cursor()
        delete_script = f"DELETE FROM CUSTOMERS WHERE NAME ='{selected_name}'"
        cur.execute(delete_script)
        conn.commit()
    except DatabaseError as e:
        conn.rollback()
        st.error(f"Update Failed: {e}")
    finally:
        cur.close()

# @st.cache_data
def get_all_contacts():
    conn = init_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT NAME FROM CUSTOMERS")
        rows = cur.fetchall()
        return rows
    except DatabaseError as e:
        st.error(f"Read failed: {e}")
        return []
    finally:
        cur.close()

def get_one_contact(name):
    conn = init_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM CUSTOMERS WHERE NAME ={name}")
        rows = cur.fetchall()
        return rows
    except DatabaseError as e:
        st.error(f"Read failed: {e}")
        return []
    finally:
        cur.close()

def duplicate_contact(verify_values):
    conn = init_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM CUSTOMERS WHERE NAME = %s AND  DESIGNATION = %s", (verify_values))
        count = cur.fetchone()[0]
        return count > 0
    except psycopg2.DatabaseError as e:
        st.error(f"Error checking for duplicates: {e}")
        return False
    finally:
        cur.close()

# Processing Extra Text Data
def uploaded_image(Card_img):
    image_dict = {'Name': [], 'Designation': [], 'Company': [], 'Contact': [],
                  'Email': [], 'Website': [],
                  'Address': [], 'Pincode': []
                  }
    image_dict['Name'].append(bounds1[0])
    image_dict['Designation'].append(bounds1[1])

    for i in range(2, len(bounds1)):
        if bounds1[i].startswith('+') or (bounds1[i].replace('-', '').isdigit() and '-' in bounds1[i]):
            image_dict['Contact'].append(bounds1[i])

        elif '@' in bounds1[i] and '.com' in bounds1[i]:
            smaller = bounds1[i].lower()
            image_dict['Email'].append(smaller)

        elif 'www' in bounds1[i] or 'WWW ' in bounds1[i] or 'wwW' in bounds1[i]:
            smaller = bounds1[i].lower()
            image_dict['Website'].append(smaller)

        elif 'Tamil Nadu' in bounds1[i] or 'TamilNadu' in bounds1[i] or bounds1[i].isdigit():
            image_dict['Pincode'].append(bounds1[i])

        elif re.match(r'^[A-Za-z]', bounds1[i]):
            image_dict['Company'].append(bounds1[i])

        else:
            remove_colon = re.sub(r'[.,;]', '', bounds1[i])
            image_dict['Address'].append(remove_colon)

    for key, values in image_dict.items():
        if len(values) > 0:
            concat_string = ' '.join(values)
            image_dict[key] = [concat_string]
        else:
            values = 'NA'
            image_dict[key] = [values]
    return image_dict

bounds2_df = []

# User Login Process - all states
if authentication_status == False:
    st.error("Username / Password is incorrect, Please Try Again!!!")

if authentication_status == None:
    st.error("Please enter your Username and password to login")

if authentication_status:
    st.write(f"Welcome {names}")
    # authenticator.logout("Logout", "main")
    with st.sidebar:
        selected = option_menu(
            menu_title="BizCardX Project Menu",
            options=["Home", "Upload and Manage DB", "Settings", "Contact"],
            icons=["house", "upload", "gear", "envelope"],
            menu_icon="cast",
            default_index=0,
            # orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#AFBFAB"},
                "icon": {"color": "orange", "font-size": "15px"},
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "left",
                    "margin": "5px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "grey"},
            },
        )
    # authenticator.logout("Logout", "main")
    df = []
    bound1_df = []
    # st.cache_data for files, APIs, data.
    # Image Reader : EasyOCR
    @st.cache_data
    def image_reco_easyocr():
        reader = easyocr.Reader(['en'])
        return reader

    # reader_easyocr = image_reco_easyocr()

    if selected == "Upload and Manage DB":
        create_table()
        # User upload the image
        selected = option_menu(
            menu_title="Manage Customer Data", options=["Upload BusinessCard", "Add / Update Customer", "Delete Record"],
            icons=["database","database-add", "database-dash"], menu_icon="database-gear",
            default_index=0, orientation="horizontal")

        if selected == "Upload BusinessCard":

            uploaded_image_file = st.file_uploader("Upload a Business card Image file", type=['png', 'jpg', 'jpeg'])
            if uploaded_image_file is not None:
                # Image received, processed and displayed the Image
                reader_easyocr = image_reco_easyocr()
                input_uploaded_image_file = Image.open(uploaded_image_file)
                st.image(input_uploaded_image_file, width=400, caption='Uploaded Customer Business Card')
                bounds1 = reader_easyocr.readtext(np.array(input_uploaded_image_file), detail=0)
                bounds1_df = uploaded_image(bounds1)
                df = pd.DataFrame(bounds1_df)

                # Prepare Image to store in Database
                image_bytes = io.BytesIO()
                input_uploaded_image_file.save(image_bytes, format='PNG')
                image_data = image_bytes.getvalue()

                data = {"Image": [image_data]}
                df1 = pd.DataFrame(data)
                Total_df = pd.concat([df, df1], axis=1)

                # DataBase Operations
                create = st.button('Create Business Card Contact in DB')
                if create:
                    with st.spinner('Connecting with database...'):
                        for index, i in Total_df.iterrows():
                            insert_final_values = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8])

                    if duplicate_contact(insert_final_values[0:2]):
                        st.warning(f"{i[0]} Contact already exists in the Database, Update this customer details by using "
                                   f"'Add / Update Customer Menu' !!!")

                        # Explore Additional Feature = Display details from DataBase for modification
                        # Show_details = st.button('Show details')
                        # if Show_details:
                        #     bounds1_df = get_one_contact(i[0])
                    else:
                        insert_card(insert_final_values)
                        st.success('Customer Business Card Contact Created Successfully')

                with st.form("Edit Record"):
                    col_1, col_2 = st.columns([4, 4])
                    with col_1:
                        edited_name = st.text_input('Name', bounds1_df["Name"][0])
                        edited_des = st.text_input('Designation', bounds1_df["Designation"][0])
                        edited_com = st.text_input('Company name', bounds1_df["Company"][0])
                        edited_num = st.text_input('Mobile', bounds1_df["Contact"][0])
                        Total_df["Name"], Total_df["Designation"], Total_df["Company"], Total_df["Contact"] = \
                            edited_name, edited_des, edited_com, edited_num
                    with col_2:
                        edited_email = st.text_input('Email', bounds1_df["Email"][0])
                        edited_web = st.text_input('Website', bounds1_df["Website"][0])
                        edited_add = st.text_input('Address', bounds1_df["Address"][0])
                        edited_pin = st.text_input('Pincode', bounds1_df["Pincode"][0])
                        Total_df["Email"], Total_df["Website"], Total_df["Address"], Total_df[
                            "Pincode"] = edited_email, \
                            edited_web, edited_add, edited_pin
                        update = st.form_submit_button("Update Record")
                        if update:
                            st.spinner("Updating data...")
                            modified_df = Total_df[['Name', 'Designation', 'Company', 'Contact', 'Email', 'Website',
                                                    'Address', 'Pincode']]

                            modified_name = modified_df['Name']

                            for index, i in modified_df.iterrows():
                                updated_final_values = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[0])
                                update_card(updated_final_values)
                            st.success("Customer Business Card Data updated successfully")

        if selected == "Add / Update Customer":

            selected = option_menu(
                menu_title="Update / Add Customer", options=["Add New Customer" , "Update Customer"],
                icons=["database", "database-add"], menu_icon="database-gear", default_index=0, orientation="horizontal")

            if selected == "Add New Customer":
                with st.form("Add_New_Customer"):
                    col_1, col_2 = st.columns([4, 4])
                    with col_1:
                        new_name = st.text_input('Name *')
                        new_des = st.text_input('Designation *')
                        new_com = st.text_input('Company name')
                        new_num = st.text_input('Mobile')

                    with col_2:
                        new_email = st.text_input('Email')
                        new_web = st.text_input('Website')
                        new_add = st.text_input('Address')
                        new_pin = st.text_input('Pincode')

                        add_new = st.form_submit_button("Add New Record")
                        if add_new:
                            if new_name and new_des:
                                add_new_customer(new_name, new_des, new_com, new_num, new_email, new_web, new_add, new_pin)
                            else:
                                st.warning("Name and Designation are required to create New Customer")

                            st.spinner("Updating data...")

            if selected == "Update Customer":
                names = ["Select Customer Name"]
                list_of_names = get_all_contacts()
                # names = ["Select Customer Name"]
                for i in list_of_names:
                    if i not in names:
                        names.append(i[0])
                # selected_name = st.selectbox("Select Customer Details", options=names)
                # customers = get_all_customers()

                customer_names = [f"{cust['id']}: {cust['name']}" for cust in list_of_names]
                selected = st.selectbox("Select a customer to edit", customer_names)

                if selected:
                    cust_id = int(selected.split(":")[0])
                    selected_cust = next(c for c in CUSTOMERS if c['id'] == cust_id)
                    with st.form("update_form"):
                        col_1, col_2 = st.columns([4, 4])
                        with col_1:
                            edited_name = st.text_input('Name *', value=selected_cust["name"])
                            edited_des = st.text_input('Designation *', value=selected_cust[""])
                            edited_com = st.text_input('Company name', value=selected_cust[""])
                            edited_num = st.text_input('Mobile', value=selected_cust["phone"])

                        with col_2:
                            edited_email = st.text_input('Email', value=selected_cust["email"])
                            edited_web = st.text_input('Website', value=selected_cust[""])
                            edited_add = st.text_input('Address', value=selected_cust["city"])
                            edited_pin = st.text_input('Pincode', value=selected_cust[""])

                            update_contact = st.form_submit_button("Update contact")

                        update_btn = st.form_submit_button("Update Customer")

                        if update_btn:
                            update_customer(cust_id, name, email, phone, city, country)
                # for index, i in modified_df.iterrows():
                #     updated_final_values = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8])
                #     update_card(updated_final_values)















        if selected == "Delete Record":
            names = ["Select Customer Name"]
            list_of_names = get_all_contacts()
            # names = ["Select Customer Name"]
            for i in list_of_names:
                if i not in names:
                    names.append(i[0])
            selected_name = st.selectbox("Select Customer Details", options=names)
            delete = st.button('Delete Customer Data')
            if selected_name and delete:
                st.spinner("Customer Data being deleted...")
                delete_card(selected_name)
                st.success('Customer Business Card Deleted successfully')
            list_of_names = get_all_contacts()

    # User Settings
    if selected == "Settings":
        st.subheader("User Settings")
        authenticator.logout("Logout Application", "main")

    # Contact Information
    if selected == "Contact":
        st.subheader("My Contact Details")
        st.write("Project: BizCardX_Extracting Business Card Data")
        st.write("Created by: Akellesh Vasudevan")
        st.write("LinkedIn Profile:")
        st.markdown("https://www.linkedin.com/in/akellesh/")
        st.write("Github Profile:")
        st.markdown("https://github.com/Akellesh/BizCardX_-Extracting-Business-Card-Data-with-OCR")

    # Home Page of Project
    if selected == "Home":
        # st.title(f"you have selected {selected}")
        st.subheader('BizCardX_Extracting Business Card with OCR')
        st.subheader("Problem Statement:")
        st.write('''You have been tasked with developing a Streamlit application that allows users to upload an image 
                of a business card and extract relevant information from it using easyOCR. The extracted information 
                should include the company name, card holder name, designation, mobile number, email address, 
                website URL, area, city, state, and pin code. The extracted information should then be displayed in the 
                application's graphical user interface (GUI).''')
        st.write('''In addition, the application should allow users to save the extracted information into a database 
                along with the uploaded business card image. The database should be able to store multiple entries, 
                each with its own business card image and extracted information.''')
        st.write('''To achieve this, you will need to use Python, Streamlit, easyOCR, and a database management 
                system like SQLite or MySQL. The application should have a simple and intuitive user interface 
                that guides users through the process of uploading the business card image and extracting its information. 
                The extracted information should be displayed in a clean and organized manner, and users should be able 
                to easily add it to the database with the click of a button. And Allow the user to Read the data,
                Update the data and Allow the user to delete the data through the streamlit UI.''')
        st.write('''This project will require skills in image processing, OCR, GUI development, and database management.
                It will also require you to carefully design and plan the application architecture to ensure that it is 
                scalable, maintainable, and extensible. Good documentation and code organization will also be important 
                for this project.''')