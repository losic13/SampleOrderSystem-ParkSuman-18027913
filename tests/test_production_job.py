from datetime import datetime

from model.production_job import ProductionJob


def test_production_job_stores_all_fields():
    enqueued_at = datetime(2026, 1, 1, 9, 0, 0)
    job = ProductionJob(
        order_id="ORD-20260101-ABCD",
        sample_id="SMP-001",
        shortage=7,
        actual_quantity=8,
        total_minutes=80,
        elapsed_minutes=20,
        enqueued_at=enqueued_at,
    )

    assert job.order_id == "ORD-20260101-ABCD"
    assert job.sample_id == "SMP-001"
    assert job.shortage == 7
    assert job.actual_quantity == 8
    assert job.total_minutes == 80
    assert job.elapsed_minutes == 20
    assert job.enqueued_at == enqueued_at


def test_is_complete_true_when_elapsed_reaches_total_minutes():
    job = ProductionJob(
        order_id="ORD-1", sample_id="SMP-1", shortage=1,
        actual_quantity=1, total_minutes=10, elapsed_minutes=10,
    )

    assert job.is_complete is True


def test_is_complete_false_while_elapsed_below_total_minutes():
    job = ProductionJob(
        order_id="ORD-1", sample_id="SMP-1", shortage=1,
        actual_quantity=1, total_minutes=10, elapsed_minutes=9,
    )

    assert job.is_complete is False


def test_progress_ratio_returns_elapsed_over_total():
    job = ProductionJob(
        order_id="ORD-1", sample_id="SMP-1", shortage=1,
        actual_quantity=1, total_minutes=20, elapsed_minutes=5,
    )

    assert job.progress_ratio == 0.25


def test_progress_ratio_capped_at_one_when_elapsed_exceeds_total():
    job = ProductionJob(
        order_id="ORD-1", sample_id="SMP-1", shortage=1,
        actual_quantity=1, total_minutes=10, elapsed_minutes=15,
    )

    assert job.progress_ratio == 1.0
