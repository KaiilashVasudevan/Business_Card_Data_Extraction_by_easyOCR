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

    # insert_script = 'INSERT INTO CUSTOMERS (company_name, card_holder_name,designation,' \
    #                 'mobile_number, email_address, website_URL, area, city, state, pincode) ' \
    #                 'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    # insert_values = ('ABC ltd', 'RAHUL', 'MANAGER', '5678493029', 'RAHUL@ABC.COM', 'WWW.ABC.COM',
    #                   'ANNA NAGAR', 'CHENNAI', 'TAMIL NADU', 600030)
    #
    # cur.execute(insert_script, insert_values)
    # cus_names = cur.execute('SELECT * FROM CUSTOMERS')
    # st.write(cus_names)


    # update_script = 'UPDATE CUSTOMERS SET SALARY = SALARY + (SALARY * 0.5)'
    # update_script = 'UPDATE CUSTOMERS SET (CONTACT, ADDRESS, PINCODE) VALUES (%s, %s, %s) WHERE NAME = Selva'
    # update_values = ('12345678', '123 ABC STREET VADAPALANI CHENNAI', 600006)
    # cur.execute(update_script, update_values)

    # delete_script = 'DELETE FROM CUSTOMERS WHERE CARD_HOLDER_NAME = %S'
    # delete_record = ('RAHUL',)
    # cur.execute(delete_script,delete_record)
#
#     cur.execute('SELECT * FROM CUSTOMERS;')
#     for record in cur.fetchall():
#         print(record['card_holder_name'], )
#
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