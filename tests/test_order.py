from datetime import datetime

from model.order import Order
from model.order_status import OrderStatus


def test_order_stores_all_fields():
    created_at = datetime(2026, 1, 1, 12, 0, 0)
    order = Order(
        order_id="ORD-20260101-ABCD",
        sample_id="SMP-001",
        customer_name="Alice",
        quantity=10,
        status=OrderStatus.CONFIRMED,
        created_at=created_at,
    )

    assert order.order_id == "ORD-20260101-ABCD"
    assert order.sample_id == "SMP-001"
    assert order.customer_name == "Alice"
    assert order.quantity == 10
    assert order.status == OrderStatus.CONFIRMED
    assert order.created_at == created_at


def test_order_status_defaults_to_reserved():
    order = Order(
        order_id="ORD-20260101-ABCD",
        sample_id="SMP-001",
        customer_name="Alice",
        quantity=10,
    )

    assert order.status == OrderStatus.RESERVED


def test_order_created_at_defaults_to_datetime_now():
    before = datetime.now()
    order = Order(
        order_id="ORD-20260101-ABCD",
        sample_id="SMP-001",
        customer_name="Alice",
        quantity=10,
    )
    after = datetime.now()

    assert before <= order.created_at <= after
