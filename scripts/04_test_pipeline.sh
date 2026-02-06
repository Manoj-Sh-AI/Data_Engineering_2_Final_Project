cat > scripts/04_test_pipeline.sh << 'EOF'
#!/bin/bash
set -e

echo "🧪 Testing Pipeline Components..."

export $(cat .env | grep -v '^#' | xargs)

# 1. Test Pub/Sub
echo "Testing Pub/Sub..."
gcloud pubsub topics describe $TOPIC_NAME
MESSAGE_COUNT=$(gcloud pubsub subscriptions describe $SUBSCRIPTION_NAME --format='value(messageCount)')
echo "Messages in queue: $MESSAGE_COUNT"

# 2. Test BigQuery
echo "Testing BigQuery..."
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`$PROJECT_ID.$DATASET_NAME.orders\`"

# 3. Test Cloud Storage
echo "Testing Cloud Storage..."
gsutil ls -r gs://$BUCKET_NAME/ | head -20

# 4. Test streaming consumer
SERVICE_URL=$(gcloud run services describe streaming-consumer --region $REGION --format='value(status.url)')
echo "Testing streaming consumer at $SERVICE_URL..."
curl -s $SERVICE_URL/metrics | jq

echo "✅ All tests passed!"
EOF

chmod +x scripts/04_test_pipeline.sh
