cat > src/data_generator/schemas.py << 'EOF'
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Order(BaseModel):
    """E-commerce order schema"""
    order_id: str = Field(..., description="Unique order identifier")
    customer_id: int = Field(..., ge=1, description="Customer ID")
    amount: float = Field(..., ge=0, description="Order amount in USD")
    timestamp: str = Field(..., description="Order timestamp (ISO format)")
    product: str = Field(..., description="Product name")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    status: str = Field(..., description="Order status")
    payment_method: str = Field(..., description="Payment method")
    device_type: str = Field(..., description="Device type used for order")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": 123,
                "amount": 299.99,
                "timestamp": "2026-02-06T12:00:00",
                "product": "Laptop",
                "shipping_address": "123 Main St, Berlin, Germany",
                "status": "pending",
                "payment_method": "credit_card",
                "device_type": "desktop"
            }
        }
EOF
