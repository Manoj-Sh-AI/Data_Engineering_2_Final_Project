#!/bin/bash
set -e

echo "🚀 Deploying GCP Infrastructure..."

# Load environment
export $(cat .env | grep -v '^#' | xargs)

# 1. Create Cloud Storage Bucket
echo "Creating GCS bucket: $BUCKET_NAME"
gsutil mb -l $REGION gs://$BUCKET_NAME || echo "Bucket already exists"

# Create folder structure
gsutil -m mkdir -p gs://$BUCKET_NAME/raw/
gsutil -m mkdir -p gs://$BUCKET_NAME/cleaned/
gsutil -m mkdir -p gs://$BUCKET_NAME/aggregated/
gsutil -m mkdir -p gs://$BUCKET_NAME/features/
gsutil -m mkdir -p gs://$BUCKET_NAME/ml/

# 2. Create Pub/Sub Topic & Subscription
echo "Creating Pub/Sub topic: $TOPIC_NAME"
gcloud pubsub topics create $TOPIC_NAME || echo "Topic already exists"

echo "Creating Pub/Sub subscription: $SUBSCRIPTION_NAME"
gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
    --topic=$TOPIC_NAME \
    --ack-deadline=60 \
    --message-retention-duration=7d || echo "Subscription already exists"

# 3. Create BigQuery Dataset
echo "Creating BigQuery dataset: $DATASET_NAME"
bq mk --location=$REGION --dataset $PROJECT_ID:$DATASET_NAME || echo "Dataset already exists"

# 4. Create BigQuery Tables
echo "Creating BigQuery tables..."

# Orders table
bq mk --table $PROJECT_ID:$DATASET_NAME.orders \
    order_id:STRING,\
    customer_id:INTEGER,\
    amount:FLOAT,\
    timestamp:TIMESTAMP,\
    product:STRING,\
    shipping_address:STRING,\
    status:STRING,\
    payment_method:STRING,\
    device_type:STRING,\
    data_quality_score:FLOAT || echo "Orders table exists"

# Daily summary table
bq mk --table $PROJECT_ID:$DATASET_NAME.daily_summary \
    date:DATE,\
    total_orders:INTEGER,\
    total_revenue:FLOAT,\
    avg_order_value:FLOAT,\
    unique_customers:INTEGER || echo "Summary table exists"

# ML predictions table
bq mk --table $PROJECT_ID:$DATASET_NAME.predictions \
    order_id:STRING,\
    prediction:INTEGER,\
    confidence:FLOAT,\
    timestamp:TIMESTAMP || echo "Predictions table exists"

echo "✅ Infrastructure deployment complete!"
echo "Bucket: gs://$BUCKET_NAME"
echo "Topic: $TOPIC_NAME"
echo "Dataset: $PROJECT_ID:$DATASET_NAME"
