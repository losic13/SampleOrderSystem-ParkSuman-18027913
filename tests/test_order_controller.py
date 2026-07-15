import pytest

from model.order_status import OrderStatus
from model.production_job import ProductionJob
from model.sample import Sample


def _register_sample(sample_repo, sample_id="SMP-001", stock=5):
    sample_repo.add(
        Sample(
            sample_id=sample_id,
            name="Wafer-A",
            avg_production_time=10.0,
            yield_rate=0.5,
            stock=stock,
        )
    )


def test_place_order_creates_reserved_order(order_controller, sample_repo):
    _register_sample(sample_repo)

    order = order_controller.place_order("SMP-001", "Alice", 3)

    assert order.status == OrderStatus.RESERVED
    assert order.sample_id == "SMP-001"
    assert order.quantity == 3


def test_place_order_rejects_unregistered_sample(order_controller):
    with pytest.raises(ValueError):
        order_controller.place_order("NOPE", "Alice", 3)


def test_place_order_rejects_quantity_below_one(order_controller, sample_repo):
    _register_sample(sample_repo)

    with pytest.raises(ValueError):
        order_controller.place_order("SMP-001", "Alice", 0)


def test_approve_with_sufficient_stock_confirms_and_deducts_stock(order_controller, sample_repo):
    _register_sample(sample_repo, stock=10)
    order = order_controller.place_order("SMP-001", "Alice", 4)

    approved = order_controller.approve(order.order_id)

    assert approved.status == OrderStatus.CONFIRMED
    assert sample_repo.get_by_id("SMP-001").stock == 6


def test_approve_with_insufficient_stock_moves_to_producing_and_zeroes_stock(
    order_controller, sample_repo
):
    _register_sample(sample_repo, stock=5)
    order = order_controller.place_order("SMP-001", "Alice", 12)

    approved = order_controller.approve(order.order_id)

    assert approved.status == OrderStatus.PRODUCING
    assert sample_repo.get_by_id("SMP-001").stock == 0


def test_approve_with_insufficient_stock_calls_production_controller_enqueue_with_shortage(
    order_controller, sample_repo, fake_production_controller
):
    _register_sample(sample_repo, stock=5)
    order = order_controller.place_order("SMP-001", "Alice", 12)

    order_controller.approve(order.order_id)

    assert len(fake_production_controller.enqueue_calls) == 1
    order_id, sample_id, shortage, yield_rate, avg_production_time = (
        fake_production_controller.enqueue_calls[0]
    )
    assert order_id == order.order_id
    assert sample_id == "SMP-001"
    assert shortage == 7
    assert yield_rate == 0.5
    assert avg_production_time == 10.0


def test_reject_moves_order_to_rejected(order_controller, sample_repo):
    _register_sample(sample_repo)
    order = order_controller.place_order("SMP-001", "Alice", 3)

    rejected = order_controller.reject(order.order_id)

    assert rejected.status == OrderStatus.REJECTED


def test_complete_production_restores_shortage_and_confirms_order(
    order_controller, sample_repo
):
    _register_sample(sample_repo, stock=5)
    order = order_controller.place_order("SMP-001", "Alice", 12)
    order_controller.approve(order.order_id)

    job = ProductionJob(
        order_id=order.order_id,
        sample_id="SMP-001",
        shortage=7,
        actual_quantity=14,
        total_minutes=140,
        elapsed_minutes=140,
    )
    completed = order_controller.complete_production(job)

    assert completed.status == OrderStatus.CONFIRMED
    assert sample_repo.get_by_id("SMP-001").stock == 7


def test_release_moves_confirmed_order_to_release(order_controller, sample_repo):
    _register_sample(sample_repo, stock=10)
    order = order_controller.place_order("SMP-001", "Alice", 4)
    order_controller.approve(order.order_id)

    released = order_controller.release(order.order_id)

    assert released.status == OrderStatus.RELEASE
