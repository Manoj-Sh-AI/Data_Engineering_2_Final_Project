cat > src/streaming/metrics.py << 'EOF'
"""Real-time metrics calculator"""

from collections import deque
from statistics import mean, stdev
from datetime import datetime

class MetricsCollector:
    def __init__(self, max_size=1000):
        self.recent_orders = deque(maxlen=max_size)
        self.total_processed = 0
        self.high_value_count = 0
        self.anomaly_count = 0
        self.product_counts = {}
        self.last_updated = None
    
    def process_order(self, order):
        """Process incoming order and update metrics"""
        self.recent_orders.append(order)
        self.total_processed += 1
        
        # High-value detection
        if order.get('amount', 0) > 300:
            self.high_value_count += 1
        
        # Product tracking
        product = order.get('product', 'Unknown')
        self.product_counts[product] = self.product_counts.get(product, 0) + 1
        
        # Anomaly detection (if enough data)
        if len(self.recent_orders) >= 100:
            amounts = [o.get('amount', 0) for o in self.recent_orders]
            avg = mean(amounts)
            std = stdev(amounts)
            if order.get('amount', 0) > avg + 2 * std:
                self.anomaly_count += 1
        
        self.last_updated = datetime.utcnow().isoformat()
    
    def get_metrics(self):
        """Get current metrics snapshot"""
        amounts = [o.get('amount', 0) for o in self.recent_orders]
        
        top_products = sorted(
            self.product_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_processed': self.total_processed,
            'avg_order_value': round(mean(amounts), 2) if amounts else 0,
            'high_value_orders': self.high_value_count,
            'anomalies_detected': self.anomaly_count,
            'top_products': dict(top_products),
            'buffer_size': len(self.recent_orders),
            'last_updated': self.last_updated
        }

# Global metrics instance
metrics_collector = MetricsCollector()
EOF
