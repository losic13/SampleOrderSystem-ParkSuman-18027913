from model.order_status import OrderStatus
from repository.sample_repository import JsonSampleRepository
from repository.order_repository import JsonOrderRepository
from repository.production_job_repository import JsonProductionJobRepository
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from monitor.monitor_service import MonitorService


def _build_system(tmp_path):
    sample_repo = JsonSampleRepository(tmp_path / "samples.json")
    order_repo = JsonOrderRepository(tmp_path / "orders.json")
    production_job_repo = JsonProductionJobRepository(tmp_path / "production_jobs.json")

    production_controller = ProductionController(production_job_repo)
    sample_controller = SampleController(sample_repo)
    order_controller = OrderController(order_repo, sample_repo, production_controller)
    monitor_service = MonitorService(order_repo, sample_repo)

    return sample_controller, order_controller, production_controller, monitor_service, sample_repo


def test_full_order_lifecycle_from_reservation_to_release_via_production_queue(tmp_path):
    sample_controller, order_controller, production_controller, monitor_service, sample_repo = (
        _build_system(tmp_path)
    )

    sample_controller.register(
        sample_id="SMP-001", name="Wafer-A", avg_production_time=10.0, yield_rate=0.5, stock=5,
    )

    order = order_controller.place_order("SMP-001", "Alice", 12)
    assert order.status == OrderStatus.RESERVED

    stock_state_before_approval = monitor_service.classify_stock()
    assert stock_state_before_approval["SMP-001"] == "부족"

    approved = order_controller.approve(order.order_id)
    assert approved.status == OrderStatus.PRODUCING
    assert sample_repo.get_by_id("SMP-001").stock == 0

    job = production_controller.current_job()
    assert job.order_id == order.order_id
    assert job.shortage == 7
    assert job.actual_quantity == 14
    assert job.total_minutes == 140

    stock_state_while_producing = monitor_service.classify_stock()
    assert stock_state_while_producing["SMP-001"] == "여유"

    partial_completion = production_controller.advance_time(50)
    assert partial_completion == []
    assert 0 < production_controller.current_job().progress_ratio < 1

    completed_jobs = production_controller.advance_time(90)
    assert [j.order_id for j in completed_jobs] == [order.order_id]

    confirmed = order_controller.complete_production(completed_jobs[0])
    assert confirmed.status == OrderStatus.CONFIRMED
    assert sample_repo.get_by_id("SMP-001").stock == 7

    released = order_controller.release(order.order_id)
    assert released.status == OrderStatus.RELEASE

    final_counts = monitor_service.count_orders_by_status()
    assert final_counts[OrderStatus.RELEASE] == 1
    assert final_counts[OrderStatus.RESERVED] == 0
    assert final_counts[OrderStatus.PRODUCING] == 0
    assert final_counts[OrderStatus.CONFIRMED] == 0


def test_rejected_order_excluded_from_status_monitoring(tmp_path):
    sample_controller, order_controller, _production_controller, monitor_service, _sample_repo = (
        _build_system(tmp_path)
    )

    sample_controller.register(
        sample_id="SMP-001", name="Wafer-A", avg_production_time=10.0, yield_rate=0.5, stock=5,
    )
    order = order_controller.place_order("SMP-001", "Bob", 3)
    order_controller.reject(order.order_id)

    counts = monitor_service.count_orders_by_status()

    assert OrderStatus.REJECTED not in counts
    assert sum(counts.values()) == 0
