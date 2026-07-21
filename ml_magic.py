import mysql.connector
import pandas as pd
import numpy as np

try:
    connection = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="1234",  
        database="uci_projects",
        port = "3307"
    )

    cursor = connection.cursor()

    query = "SELECT * FROM online_retail;"
    cursor.execute(query)

    raw_data = cursor.fetchall()

    column_header = cursor.column_names

    df = pd.DataFrame(raw_data, columns = column_header)

    print("Data succefully loaded into pandas")
    print(df.head())

except mysql.connector.Error as error:
    print(f"Database error occured {error}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()

# instead of all string make them int and datetime values
df['quantity'] = pd.to_numeric(df['quantity'])
df['price'] = pd.to_numeric(df['price'])
df['invoice_date'] = pd.to_datetime(df['invoice_date'])

df = df.dropna(subset =['customer_ID']) # to drop missing values

df = df[df['quantity'] > 0]

df['total_price'] = df['price'] * df['quantity']

print(f"Cleaned data. Remaining rows: {len(df)}")

snapshot_date = df['invoice_date'].max() + pd.Timedelta(days=1)

rfm = df.groupby('customer_ID').agg({
        'invoice_date': lambda x: (snapshot_date - x.max()).days,  # Recency: Days since last order
        'invoice': 'nunique',                                      # Frequency: Count of unique receipts
        'total_price': 'sum'                                       # Monetary: Total money spent
    }).reset_index()

rfm.rename(columns={
        'invoice_date': 'Recency',
        'invoice': 'Frequency',
        'total_price': 'Monetary'
    }, inplace=True)

print(f"Crushed down to {len(rfm)} unique customers!")
print(rfm.head())