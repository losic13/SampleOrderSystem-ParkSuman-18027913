import pytest

from repository.sample_repository import JsonSampleRepository
from repository.order_repository import JsonOrderRepository
from repository.production_job_repository import JsonProductionJobRepository
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from monitor.monitor_service import MonitorService


@pytest.fixture
def sample_repo(tmp_path):
    return JsonSampleRepository(tmp_path / "samples.json")


@pytest.fixture
def order_repo(tmp_path):
    return JsonOrderRepository(tmp_path / "orders.json")


@pytest.fixture
def production_job_repo(tmp_path):
    return JsonProductionJobRepository(tmp_path / "production_jobs.json")


class FakeProductionController:
    """order_controller 테스트에서 실제 ProductionController(태스크6) 대신 쓰는 테스트 더블."""

    def __init__(self) -> None:
        self.enqueue_calls = []

    def enqueue(self, order_id, sample_id, shortage, yield_rate, avg_production_time) -> None:
        self.enqueue_calls.append(
            (order_id, sample_id, shortage, yield_rate, avg_production_time)
        )


@pytest.fixture
def fake_production_controller():
    return FakeProductionController()


@pytest.fixture
def sample_controller(sample_repo):
    return SampleController(sample_repo)


@pytest.fixture
def order_controller(order_repo, sample_repo, fake_production_controller):
    return OrderController(order_repo, sample_repo, fake_production_controller)


@pytest.fixture
def production_controller(production_job_repo):
    return ProductionController(production_job_repo)


@pytest.fixture
def monitor_service(order_repo, sample_repo):
    return MonitorService(order_repo, sample_repo)
