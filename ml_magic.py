from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import mysql.connector
import pandas as pd
import numpy as np

try:
    connection = mysql.connector.connect(
        host="host.docker.internal",
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

print('RFM stats')
print(rfm.describe().apply(lambda s: s.apply('{0:.2f}'.format)))

freq_cap = rfm['Frequency'].quantile(0.99)
mon_cap = rfm['Monetary'].quantile(0.99)

rfm_clean = rfm[(rfm['Frequency'] <= freq_cap) & (rfm['Monetary'] <= mon_cap)].copy()
print(f"Removed extreme outliers. Customers remaining: {len(rfm_clean)}")

scaler = StandardScaler()

rfm_scaled = scaler.fit_transform(rfm_clean[['Recency', 'Frequency', 'Monetary']])
print("Data is trimmed")

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)

kmeans.fit(rfm_scaled)

rfm_clean['Cluster'] = kmeans.labels_

print("Cluster complete")

cluster_profiles = rfm_clean.groupby('Cluster').agg({
    'Recency': 'mean',
    'Frequency': 'mean',
    'Monetary': ['mean', 'count'] 
}).round(1)

print(cluster_profiles)

cutoff_date = pd.Timestamp('2011-09-30')

feature_df = df[df['invoice_date'] <= cutoff_date].copy()
target_df = df[df['invoice_date'] > cutoff_date].copy()

print(f"Feature window: {feature_df['invoice_date'].min()} to {feature_df['invoice_date'].max()}")
print(f"Target window:  {target_df['invoice_date'].min()} to {target_df['invoice_date'].max()}")
print(f"Customers in feature window: {feature_df['customer_ID'].nunique()}")

customer_features = feature_df.groupby('customer_ID').agg(
    Recency=('invoice_date', lambda x: (cutoff_date - x.max()).days),
    Frequency=('invoice', 'nunique'),
    Monetary=('total_price', 'sum'),
    TotalQuantity=('quantity', 'sum'),
    UniqueProducts=('stock_code', 'nunique'),
    FirstPurchase=('invoice_date', 'min'),
    LastPurchase=('invoice_date', 'max')
).reset_index()

customer_features['Tenure'] = (customer_features['LastPurchase'] - customer_features['FirstPurchase']).dt.days
customer_features['AvgOrderValue'] = customer_features['Monetary'] / customer_features['Frequency']
customer_features['AvgItemsPerOrder'] = customer_features['TotalQuantity'] / customer_features['Frequency']

customer_features = customer_features.replace([np.inf, -np.inf], 0).fillna(0)

print(f"Engineered features for {len(customer_features)} customers")
print(customer_features.head())