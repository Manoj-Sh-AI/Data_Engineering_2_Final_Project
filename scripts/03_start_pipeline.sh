#!/bin/bash
set -e

echo "🚀 Starting Data Pipeline..."

export $(cat .env | grep -v '^#' | xargs)

# 1. Build and deploy streaming consumer to Cloud Run
echo "Building Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/streaming-consumer .

echo "Deploying to Cloud Run..."
gcloud run deploy streaming-consumer \
    --image gcr.io/$PROJECT_ID/streaming-consumer \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 3 \
    --set-env-vars PROJECT_ID=$PROJECT_ID,SUBSCRIPTION_NAME=$SUBSCRIPTION_NAME

# Get service URL
SERVICE_URL=$(gcloud run services describe streaming-consumer \
    --region $REGION \
    --format='value(status.url)')

echo "✅ Streaming consumer deployed: $SERVICE_URL"

# 2. Start data generator (in background)
echo "Starting data generator..."
mkdir -p logs
nohup python src/data_generator/generator.py > logs/generator.log 2>&1 &
GENERATOR_PID=$!

echo "✅ Data generator started (PID: $GENERATOR_PID)"
echo "Monitor logs: tail -f logs/generator.log"

# 3. Test streaming endpoint
sleep 5
echo "Testing streaming consumer..."
curl -s $SERVICE_URL/health | jq

echo ""
echo "✅ Pipeline started successfully!"
echo ""
echo "📊 Monitoring URLs:"
echo "  - Health: $SERVICE_URL/health"
echo "  - Metrics: $SERVICE_URL/metrics"
echo "  - Logs: tail -f logs/generator.log"
echo ""
echo "🛑 To stop:"
echo "  - Kill generator: kill $GENERATOR_PID"
echo "  - Delete service: gcloud run services delete streaming-consumer --region $REGION"
