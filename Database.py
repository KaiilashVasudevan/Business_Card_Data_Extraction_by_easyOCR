import psycopg2
import psycopg2.extras
import streamlit as st

hostname = 'localhost'
database = 'Business_card_Database'
username = 'postgres'
pwd = 'Environment!123'
port_id = '5432'
conn = None
cur = None
try:
    conn = psycopg2.connect(host=hostname, dbname=database,
                            user=username, password=pwd,
                            port=port_id)

    # cursor need to be opened, help to do SQL operations and store values
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # create_script = ''' CREATE TABLE IF NOT EXISTS CUSTOMERS(
    #                     company_name VARCHAR(40), card_holder_name VARCHAR(20) PRIMARY KEY, designation VARCHAR(20),
    #                     mobile_number VARCHAR(20), email_address VARCHAR(20), website_URL VARCHAR(20),
    #                     area VARCHAR(20), city VARCHAR(20), state VARCHAR(20), pincode INT)'''
    # cur.execute(create_script)

    conn.commit()
except Exception as error:
    print(error)
finally:
    if cur is not None:
        # We need to close the cursor
        cur.close()
    if conn is not None:
        # We need close the connection
        conn.close()