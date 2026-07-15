import math
from typing import Optional

from model.production_job import ProductionJob
from repository.production_job_repository import ProductionJobRepository


class ProductionController:
    def __init__(self, production_job_repo: ProductionJobRepository) -> None:
        self._production_job_repo = production_job_repo

    def enqueue(
        self,
        order_id: str,
        sample_id: str,
        shortage: int,
        yield_rate: float,
        avg_production_time: float,
    ) -> ProductionJob:
        actual_quantity = math.ceil(shortage / yield_rate)
        total_minutes = round(avg_production_time * actual_quantity)
        job = ProductionJob(
            order_id=order_id,
            sample_id=sample_id,
            shortage=shortage,
            actual_quantity=actual_quantity,
            total_minutes=total_minutes,
        )
        self._production_job_repo.add(job)
        return job

    def list_queue(self) -> list[ProductionJob]:
        return self._production_job_repo.get_all()

    def current_job(self) -> Optional[ProductionJob]:
        queue = self.list_queue()
        return queue[0] if queue else None

    def advance_time(self, minutes: int) -> list[ProductionJob]:
        job = self.current_job()
        if job is None:
            return []

        job.elapsed_minutes += minutes
        if job.is_complete:
            self._production_job_repo.delete(job.order_id)
            return [job]

        self._production_job_repo.update(job)
        return []
