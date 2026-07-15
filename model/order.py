from dataclasses import dataclass, field
from datetime import datetime

from model.order_status import OrderStatus


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
    created_at: datetime = field(default_factory=datetime.now)
