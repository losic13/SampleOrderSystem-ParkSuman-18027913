import pytest

from repository.sample_repository import JsonSampleRepository
from repository.order_repository import JsonOrderRepository
from repository.production_job_repository import JsonProductionJobRepository


@pytest.fixture
def sample_repo(tmp_path):
    return JsonSampleRepository(tmp_path / "samples.json")


@pytest.fixture
def order_repo(tmp_path):
    return JsonOrderRepository(tmp_path / "orders.json")


@pytest.fixture
def production_job_repo(tmp_path):
    return JsonProductionJobRepository(tmp_path / "production_jobs.json")
