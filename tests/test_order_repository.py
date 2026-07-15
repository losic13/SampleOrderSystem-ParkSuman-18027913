from datetime import datetime

from model.order import Order
from model.order_status import OrderStatus
from repository.order_repository import JsonOrderRepository


def _make_order(order_id="ORD-20260101-AAAA", status=OrderStatus.RESERVED):
    return Order(
        order_id=order_id,
        sample_id="SMP-001",
        customer_name="Alice",
        quantity=10,
        status=status,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


def test_add_and_get_by_id_returns_saved_order(order_repo):
    order_repo.add(_make_order())

    found = order_repo.get_by_id("ORD-20260101-AAAA")

    assert found == _make_order()


def test_get_all_returns_every_saved_order(order_repo):
    order_repo.add(_make_order("ORD-20260101-AAAA"))
    order_repo.add(_make_order("ORD-20260101-BBBB"))

    all_orders = order_repo.get_all()

    assert {o.order_id for o in all_orders} == {"ORD-20260101-AAAA", "ORD-20260101-BBBB"}


def test_get_by_status_filters_by_status(order_repo):
    order_repo.add(_make_order("ORD-20260101-AAAA", status=OrderStatus.RESERVED))
    order_repo.add(_make_order("ORD-20260101-BBBB", status=OrderStatus.CONFIRMED))

    reserved = order_repo.get_by_status(OrderStatus.RESERVED)

    assert [o.order_id for o in reserved] == ["ORD-20260101-AAAA"]


def test_update_persists_changed_fields(order_repo):
    order_repo.add(_make_order())

    updated = _make_order(status=OrderStatus.CONFIRMED)
    order_repo.update(updated)

    assert order_repo.get_by_id("ORD-20260101-AAAA").status == OrderStatus.CONFIRMED


def test_delete_removes_order(order_repo):
    order_repo.add(_make_order())

    order_repo.delete("ORD-20260101-AAAA")

    assert order_repo.get_by_id("ORD-20260101-AAAA") is None


def test_get_by_id_returns_none_when_not_found(order_repo):
    assert order_repo.get_by_id("NOPE") is None


def test_add_persists_enum_and_datetime_fields_across_reload(tmp_path):
    file_path = tmp_path / "orders.json"
    repo = JsonOrderRepository(file_path)
    repo.add(_make_order(status=OrderStatus.PRODUCING))

    reloaded_repo = JsonOrderRepository(file_path)
    reloaded = reloaded_repo.get_by_id("ORD-20260101-AAAA")

    assert reloaded.status == OrderStatus.PRODUCING
    assert reloaded.created_at == datetime(2026, 1, 1, 12, 0, 0)
