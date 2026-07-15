from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from model.production_job import ProductionJob
from repository import _json_store


class ProductionJobRepository(ABC):
    @abstractmethod
    def add(self, job: ProductionJob) -> None: ...

    @abstractmethod
    def get_by_order_id(self, order_id: str) -> Optional[ProductionJob]: ...

    @abstractmethod
    def get_all(self) -> list[ProductionJob]: ...

    @abstractmethod
    def update(self, job: ProductionJob) -> None: ...

    @abstractmethod
    def delete(self, order_id: str) -> None: ...


class JsonProductionJobRepository(ProductionJobRepository):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        _json_store.ensure_file(self._file_path)

    def add(self, job: ProductionJob) -> None:
        data = _json_store.read_json(self._file_path)
        data[job.order_id] = self._to_dict(job)
        _json_store.write_json(self._file_path, data)

    def get_by_order_id(self, order_id: str) -> Optional[ProductionJob]:
        data = _json_store.read_json(self._file_path)
        raw = data.get(order_id)
        return self._from_dict(raw) if raw is not None else None

    def get_all(self) -> list[ProductionJob]:
        data = _json_store.read_json(self._file_path)
        return [self._from_dict(raw) for raw in data.values()]

    def update(self, job: ProductionJob) -> None:
        self.add(job)

    def delete(self, order_id: str) -> None:
        data = _json_store.read_json(self._file_path)
        data.pop(order_id, None)
        _json_store.write_json(self._file_path, data)

    @staticmethod
    def _to_dict(job: ProductionJob) -> dict:
        return {
            "order_id": job.order_id,
            "sample_id": job.sample_id,
            "shortage": job.shortage,
            "actual_quantity": job.actual_quantity,
            "total_minutes": job.total_minutes,
            "elapsed_minutes": job.elapsed_minutes,
            "enqueued_at": job.enqueued_at.isoformat(),
        }

    @staticmethod
    def _from_dict(raw: dict) -> ProductionJob:
        return ProductionJob(
            order_id=raw["order_id"],
            sample_id=raw["sample_id"],
            shortage=raw["shortage"],
            actual_quantity=raw["actual_quantity"],
            total_minutes=raw["total_minutes"],
            elapsed_minutes=raw["elapsed_minutes"],
            enqueued_at=datetime.fromisoformat(raw["enqueued_at"]),
        )
