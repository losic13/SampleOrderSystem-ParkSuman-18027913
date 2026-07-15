from datetime import datetime

from model.production_job import ProductionJob
from repository.production_job_repository import JsonProductionJobRepository


def _make_job(order_id="ORD-20260101-AAAA", elapsed_minutes=0):
    return ProductionJob(
        order_id=order_id,
        sample_id="SMP-001",
        shortage=7,
        actual_quantity=8,
        total_minutes=80,
        elapsed_minutes=elapsed_minutes,
        enqueued_at=datetime(2026, 1, 1, 9, 0, 0),
    )


def test_add_and_get_by_order_id_returns_saved_job(production_job_repo):
    production_job_repo.add(_make_job())

    found = production_job_repo.get_by_order_id("ORD-20260101-AAAA")

    assert found == _make_job()


def test_get_all_preserves_fifo_insertion_order(production_job_repo):
    production_job_repo.add(_make_job("ORD-20260101-AAAA"))
    production_job_repo.add(_make_job("ORD-20260101-BBBB"))
    production_job_repo.add(_make_job("ORD-20260101-CCCC"))

    order_ids = [job.order_id for job in production_job_repo.get_all()]

    assert order_ids == ["ORD-20260101-AAAA", "ORD-20260101-BBBB", "ORD-20260101-CCCC"]


def test_update_persists_elapsed_minutes(production_job_repo):
    production_job_repo.add(_make_job())

    updated = _make_job(elapsed_minutes=40)
    production_job_repo.update(updated)

    assert production_job_repo.get_by_order_id("ORD-20260101-AAAA").elapsed_minutes == 40


def test_delete_removes_job(production_job_repo):
    production_job_repo.add(_make_job())

    production_job_repo.delete("ORD-20260101-AAAA")

    assert production_job_repo.get_by_order_id("ORD-20260101-AAAA") is None


def test_add_persists_enqueued_at_datetime_across_reload(tmp_path):
    file_path = tmp_path / "production_jobs.json"
    repo = JsonProductionJobRepository(file_path)
    repo.add(_make_job())

    reloaded_repo = JsonProductionJobRepository(file_path)
    reloaded = reloaded_repo.get_by_order_id("ORD-20260101-AAAA")

    assert reloaded.enqueued_at == datetime(2026, 1, 1, 9, 0, 0)
