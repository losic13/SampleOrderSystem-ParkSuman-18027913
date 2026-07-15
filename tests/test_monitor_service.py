from model.order import Order
from model.order_status import OrderStatus
from model.sample import Sample


def _make_order(order_id, status, sample_id="SMP-001", quantity=1):
    return Order(
        order_id=order_id,
        sample_id=sample_id,
        customer_name="Alice",
        quantity=quantity,
        status=status,
    )


def test_count_orders_by_status_excludes_rejected(monitor_service, order_repo):
    order_repo.add(_make_order("ORD-1", OrderStatus.RESERVED))
    order_repo.add(_make_order("ORD-2", OrderStatus.REJECTED))

    counts = monitor_service.count_orders_by_status()

    assert OrderStatus.REJECTED not in counts


def test_count_orders_by_status_counts_each_monitored_status_correctly(monitor_service, order_repo):
    order_repo.add(_make_order("ORD-1", OrderStatus.RESERVED))
    order_repo.add(_make_order("ORD-2", OrderStatus.RESERVED))
    order_repo.add(_make_order("ORD-3", OrderStatus.CONFIRMED))
    order_repo.add(_make_order("ORD-4", OrderStatus.PRODUCING))
    order_repo.add(_make_order("ORD-5", OrderStatus.RELEASE))

    counts = monitor_service.count_orders_by_status()

    assert counts[OrderStatus.RESERVED] == 2
    assert counts[OrderStatus.CONFIRMED] == 1
    assert counts[OrderStatus.PRODUCING] == 1
    assert counts[OrderStatus.RELEASE] == 1


def test_classify_stock_returns_gone_when_stock_is_zero(monitor_service, sample_repo):
    sample_repo.add(Sample("SMP-001", "Wafer-A", 10.0, 0.9, stock=0))

    result = monitor_service.classify_stock()

    assert result["SMP-001"] == "고갈"


def test_classify_stock_returns_shortage_when_stock_below_reserved_quantity(
    monitor_service, sample_repo, order_repo
):
    sample_repo.add(Sample("SMP-001", "Wafer-A", 10.0, 0.9, stock=5))
    order_repo.add(_make_order("ORD-1", OrderStatus.RESERVED, quantity=10))

    result = monitor_service.classify_stock()

    assert result["SMP-001"] == "부족"


def test_classify_stock_returns_sufficient_when_stock_covers_reserved_quantity(
    monitor_service, sample_repo, order_repo
):
    sample_repo.add(Sample("SMP-001", "Wafer-A", 10.0, 0.9, stock=10))
    order_repo.add(_make_order("ORD-1", OrderStatus.RESERVED, quantity=5))

    result = monitor_service.classify_stock()

    assert result["SMP-001"] == "여유"


def test_classify_stock_ignores_producing_order_quantity_in_shortage_calculation(
    monitor_service, sample_repo, order_repo
):
    sample_repo.add(Sample("SMP-001", "Wafer-A", 10.0, 0.9, stock=5))
    order_repo.add(_make_order("ORD-1", OrderStatus.PRODUCING, quantity=100))

    result = monitor_service.classify_stock()

    assert result["SMP-001"] == "여유"
