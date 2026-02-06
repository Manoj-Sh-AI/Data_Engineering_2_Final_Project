cat > src/streaming/consumer.py << 'EOF'
"""
Pub/Sub streaming consumer with real-time analytics
"""

import os
import json
from google.cloud import pubsub_v1
from dotenv import load_dotenv
from .metrics import metrics_collector

load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')
SUBSCRIPTION_NAME = os.getenv('SUBSCRIPTION_NAME')

def process_message(message):
    """Process individual Pub/Sub message"""
    try:
        order = json.loads(message.data.decode('utf-8'))
        metrics_collector.process_order(order)
        
        # Log high-value orders
        if order.get('amount', 0) > 300:
            print(f"🔔 HIGH VALUE: ${order['amount']:.2f} - {order['order_id']}")
        
        message.ack()
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        message.nack()

def start_streaming_consumer():
    """Start continuous Pub/Sub consumer"""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
    
    print(f"🎧 Listening to: {subscription_path}")
    
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=process_message
    )
    
    try:
        streaming_pull_future.result()
    except Exception as e:
        streaming_pull_future.cancel()
        print(f"❌ Consumer stopped: {e}")
EOF
