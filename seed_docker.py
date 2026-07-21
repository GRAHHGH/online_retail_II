import mysql.connector
import pandas as pd 
import csv

try:
    connection = mysql.connector.connect(
        host = "127.0.0.1",
        user = "root",
        password = "1234",
        database = "uci_projects", 
        port = "3307"
    )

    cursor = connection.cursor()
    print("succefull, its connected to the docker jayde!")

    df = pd.read_csv('online_retail_II.csv', encoding='latin1')

    df = df[df['Invoice'] != 'Invoice']
    df = df[df['StockCode'] != 'StockCode']
    df = df[df['Description'] != 'Description']
    df = df[df['Quantity'] != 'Quantity']
    df = df[df['InvoiceDate'] != 'InvoiceDate']
    df = df[df['Price'] != 'Price']
    df = df[df['Customer ID'] != 'Customer ID']
    df = df[df['Country'] != 'Country']

    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['InvoiceDate'] = df['InvoiceDate'].dt.strftime('%Y-%m-%d %H:%M:%S')

    df = df.astype(object).where(pd.notnull(df), None)
        
    query = ("""
        CREATE TABLE IF NOT EXISTS online_retail(
            invoice VARCHAR(50),
            stock_code VARCHAR(50),
            description VARCHAR(150),
            quantity VARCHAR(50),
            invoice_date DATETIME,
            price VARCHAR(50),
            customer_ID VARCHAR(50),
            country VARCHAR(50)
            )
            """)
    
    cursor.execute(query)
    print("reading data rows")
    
    data_to_insert = [tuple(row) for row in df.values]
    print(f"Pushing {len(data_to_insert)} rows into the db")
    cursor.executemany(
        "INSERT INTO online_retail VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
        data_to_insert
    )

    connection.commit()
    print("all data is in docker")

except mysql.connector.Error as error:
    print(f"Database error occured: {error}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()