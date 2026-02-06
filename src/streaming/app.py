cat > src/streaming/app.py << 'EOF'
"""
Flask API for streaming consumer with health checks and metrics
"""

import threading
from flask import Flask, jsonify
from datetime import datetime
from .consumer import start_streaming_consumer
from .metrics import metrics_collector

app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'streaming-consumer',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/metrics')
def metrics():
    """Real-time metrics endpoint"""
    return jsonify(metrics_collector.get_metrics())

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'E-Commerce Streaming Consumer',
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics'
        }
    })

def main():
    """Start consumer in background thread and Flask app"""
    # Start Pub/Sub consumer in background
    consumer_thread = threading.Thread(
        target=start_streaming_consumer,
        daemon=True
    )
    consumer_thread.start()
    
    # Start Flask API
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()
EOF
