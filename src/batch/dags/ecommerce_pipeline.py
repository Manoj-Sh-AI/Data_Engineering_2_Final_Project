cat > src/batch/dags/ecommerce_pipeline.py << 'EOF'
"""
E-Commerce Batch Processing Pipeline
Daily: Ingest → Clean → Aggregate → Features → BigQuery
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from google.cloud import pubsub_v1, storage, bigquery
import pandas as pd
import json

# Configuration
PROJECT_ID = os.getenv('PROJECT_ID', 'your-project-id')
BUCKET_NAME = f"{PROJECT_ID}-data-lake"
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_NAME', 'orders-subscription')
DATASET_NAME = 'ecommerce_analytics'

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 2, 6),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ecommerce_batch_pipeline',
    default_args=default_args,
    description='Daily e-commerce order processing',
    schedule_interval='@daily',
    catchup=False,
    tags=['production', 'ecommerce'],
)

def ingest_from_pubsub(**context):
    """Pull messages from Pub/Sub"""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    orders = []
    response = subscriber.pull(
        request={"subscription": subscription_path, "max_messages": 1000}
    )
    
    for msg in response.received_messages:
        order = json.loads(msg.message.data.decode('utf-8'))
        orders.append(order)
        subscriber.acknowledge(
            request={
                "subscription": subscription_path,
                "ack_ids": [msg.ack_id]
            }
        )
    
    # Save to GCS
    df = pd.DataFrame(orders)
    execution_date = context['ds']
    filename = f"raw/orders_{execution_date}.csv"
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(df.to_csv(index=False), 'text/csv')
    
    print(f"✓ Ingested {len(orders)} orders")
    return filename

def clean_data(**context):
    """Clean and validate data"""
    ti = context['ti']
    filename = ti.xcom_pull(task_ids='ingest_data')
    
    df = pd.read_csv(f'gs://{BUCKET_NAME}/{filename}')
    
    # Cleaning steps
    df = df.drop_duplicates(subset=['order_id'])
    df['shipping_address'].fillna('Unknown', inplace=True)
    df = df[(df['amount'] >= 5) & (df['amount'] <= 1000)]
    df['data_quality_score'] = 1.0
    df.loc[df['shipping_address'] == 'Unknown', 'data_quality_score'] = 0.8
    
    # Save cleaned data
    execution_date = context['ds']
    clean_filename = f"cleaned/orders_{execution_date}.csv"
    df.to_csv(f'gs://{BUCKET_NAME}/{clean_filename}', index=False)
    
    print(f"✓ Cleaned {len(df)} records")
    return clean_filename

def aggregate_analytics(**context):
    """Compute daily aggregations"""
    ti = context['ti']
    filename = ti.xcom_pull(task_ids='clean_data')
    
    df = pd.read_csv(f'gs://{BUCKET_NAME}/{filename}')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    summary = df.groupby(df['timestamp'].dt.date).agg({
        'order_id': 'count',
        'amount': ['sum', 'mean'],
        'customer_id': 'nunique'
    }).reset_index()
    
    summary.columns = ['date', 'total_orders', 'total_revenue', 
                      'avg_order_value', 'unique_customers']
    
    # Save
    execution_date = context['ds']
    agg_filename = f"aggregated/summary_{execution_date}.csv"
    summary.to_csv(f'gs://{BUCKET_NAME}/{agg_filename}', index=False)
    
    print(f"✓ Aggregated {len(summary)} records")
    return agg_filename

def engineer_features(**context):
    """Create ML features"""
    ti = context['ti']
    filename = ti.xcom_pull(task_ids='clean_data')
    
    df = pd.read_csv(f'gs://{BUCKET_NAME}/{filename}')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_high_value'] = (df['amount'] > 200).astype(int)
    
    # Save
    execution_date = context['ds']
    features_filename = f"features/orders_{execution_date}.csv"
    df.to_csv(f'gs://{BUCKET_NAME}/{features_filename}', index=False)
    
    print(f"✓ Features created")
    return features_filename

def load_to_bigquery(**context):
    """Load to BigQuery"""
    ti = context['ti']
    clean_file = ti.xcom_pull(task_ids='clean_data')
    agg_file = ti.xcom_pull(task_ids='aggregate_data')
    
    bq_client = bigquery.Client()
    
    # Load orders
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition='WRITE_APPEND'
    )
    
    uri = f'gs://{BUCKET_NAME}/{clean_file}'
    table_id = f'{PROJECT_ID}.{DATASET_NAME}.orders'
    job = bq_client.load_table_from_uri(uri, table_id, job_config=job_config)
    job.result()
    
    # Load summary
    uri_summary = f'gs://{BUCKET_NAME}/{agg_file}'
    table_id_summary = f'{PROJECT_ID}.{DATASET_NAME}.daily_summary'
    job_summary = bq_client.load_table_from_uri(uri_summary, table_id_summary, job_config=job_config)
    job_summary.result()
    
    print("✓ Loaded to BigQuery")

# Define tasks
t1 = PythonOperator(task_id='ingest_data', python_callable=ingest_from_pubsub, dag=dag)
t2 = PythonOperator(task_id='clean_data', python_callable=clean_data, dag=dag)
t3 = PythonOperator(task_id='aggregate_data', python_callable=aggregate_analytics, dag=dag)
t4 = PythonOperator(task_id='engineer_features', python_callable=engineer_features, dag=dag)
t5 = PythonOperator(task_id='load_to_bigquery', python_callable=load_to_bigquery, dag=dag)

# Dependencies
t1 >> t2 >> [t3, t4] >> t5
EOF
