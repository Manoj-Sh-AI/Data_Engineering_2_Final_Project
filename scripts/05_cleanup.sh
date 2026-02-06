cat > scripts/05_cleanup.sh << 'EOF'
#!/bin/bash
set -e

echo "🧹 Cleaning up GCP resources..."

export $(cat .env | grep -v '^#' | xargs)

read -p "Are you sure you want to delete all resources? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

# Delete Cloud Run service
gcloud run services delete streaming-consumer --region $REGION --quiet || true

# Delete Pub/Sub
gcloud pubsub subscriptions delete $SUBSCRIPTION_NAME --quiet || true
gcloud pubsub topics delete $TOPIC_NAME --quiet || true

# Delete BigQuery dataset
bq rm -r -f -d $PROJECT_ID:$DATASET_NAME || true

# Delete GCS bucket
gsutil -m rm -r gs://$BUCKET_NAME || true

echo "✅ Cleanup complete!"
EOF

chmod +x scripts/05_cleanup.sh
