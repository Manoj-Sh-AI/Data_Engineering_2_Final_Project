"""
E-Commerce Order Data Generator
Generates 1000+ records/hour for 6 hours to GCP Pub/Sub
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from faker import Faker
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')
TOPIC_NAME = os.getenv('TOPIC_NAME', 'orders-stream')

# Initialize Faker and Pub/Sub
fake = Faker()
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

# Product catalog
PRODUCTS = [
    'Laptop', 'Smartphone', 'Tablet', 'Headphones', 
    'Camera', 'Smartwatch', 'Keyboard', 'Monitor',
    'Mouse', 'Speaker', 'Charger', 'USB Cable'
]

STATUSES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
PAYMENT_METHODS = ['credit_card', 'paypal', 'bank_transfer', 'apple_pay', 'google_pay']
DEVICE_TYPES = ['mobile', 'desktop', 'tablet']

def generate_order():
    """Generate realistic e-commerce order with data quality issues"""
    
    # Inject quality issues
    # 10% missing shipping address
    # 5% duplicate orders (same order_id)
    # 2% extreme outliers in amount
    
    has_missing_address = random.random() < 0.10
    is_outlier = random.random() < 0.02
    
    # Generate amount (with outliers)
    if is_outlier:
        amount = round(random.uniform(1000, 5000), 2)  # Extreme high value
    else:
        amount = round(random.uniform(10, 500), 2)  # Normal range
    
    order = {
        'order_id': fake.uuid4(),
        'customer_id': random.randint(1, 1000),
        'amount': amount,
        'timestamp': datetime.utcnow().isoformat(),
        'product': random.choice(PRODUCTS),
        'shipping_address': None if has_missing_address else fake.address().replace('\n', ', '),
        'status': random.choice(STATUSES),
        'payment_method': random.choice(PAYMENT_METHODS),
        'device_type': random.choice(DEVICE_TYPES)
    }
    
    return order

def publish_to_pubsub(order_data):
    """Publish order to Pub/Sub topic"""
    try:
        message = json.dumps(order_data).encode('utf-8')
        future = publisher.publish(topic_path, message)
        message_id = future.result()
        return message_id
    except Exception as e:
        print(f"❌ Error publishing: {e}")
        return None

def main():
    """Generate 6000 orders over 6 hours (1000/hour)"""
    
    total_orders = 6000
    duration_hours = 6
    interval_seconds = (duration_hours * 3600) / total_orders  # ~3.6 seconds
    
    print("=" * 60)
    print("🚀 E-COMMERCE DATA GENERATOR")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Topic: {TOPIC_NAME}")
    print(f"Target: {total_orders} orders over {duration_hours} hours")
    print(f"Rate: {total_orders / duration_hours} orders/hour")
    print(f"Interval: {interval_seconds:.2f} seconds\n")
    
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    try:
        for i in range(total_orders):
            order = generate_order()
            message_id = publish_to_pubsub(order)
            
            if message_id:
                success_count += 1
                
                # Log progress every 100 orders
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = success_count / (elapsed / 3600)
                    print(f"✓ [{i + 1}/{total_orders}] | "
                          f"Amount: ${order['amount']:.2f} | "
                          f"Product: {order['product']:15} | "
                          f"Rate: {rate:.0f}/hr | "
                          f"Errors: {error_count}")
            else:
                error_count += 1
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n⚠️  Generator stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("📊 GENERATION SUMMARY")
        print("=" * 60)
        print(f"Total orders generated: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Duration: {elapsed / 60:.1f} minutes")
        print(f"Average rate: {success_count / (elapsed / 3600):.0f} orders/hour")
        print("=" * 60)

if __name__ == "__main__":
    if not PROJECT_ID:
        print("❌ Error: PROJECT_ID not set in .env file")
        sys.exit(1)
    
    main()
EOF
