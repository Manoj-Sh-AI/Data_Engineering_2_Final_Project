#!/bin/bash
set -e

echo "🚀 Setting up GCP Project..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found! Copy .env.example to .env first."
    exit 1
fi

# Authenticate (if not already)
echo "Checking authentication..."
gcloud auth list

# Set project
echo "Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# Enable required APIs
echo "Enabling GCP APIs..."
gcloud services enable \
    pubsub.googleapis.com \
    storage.googleapis.com \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    run.googleapis.com \
    composer.googleapis.com \
    monitoring.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    cloudscheduler.googleapis.com

echo "✅ GCP setup complete!"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
