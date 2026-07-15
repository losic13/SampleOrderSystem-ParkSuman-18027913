from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from model.sample import Sample
from repository import _json_store


class SampleRepository(ABC):
    @abstractmethod
    def add(self, sample: Sample) -> None: ...

    @abstractmethod
    def get_by_id(self, sample_id: str) -> Optional[Sample]: ...

    @abstractmethod
    def get_all(self) -> list[Sample]: ...

    @abstractmethod
    def search_by_name(self, keyword: str) -> list[Sample]: ...

    @abstractmethod
    def update(self, sample: Sample) -> None: ...

    @abstractmethod
    def delete(self, sample_id: str) -> None: ...


class JsonSampleRepository(SampleRepository):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        _json_store.ensure_file(self._file_path)

    def add(self, sample: Sample) -> None:
        data = _json_store.read_json(self._file_path)
        data[sample.sample_id] = self._to_dict(sample)
        _json_store.write_json(self._file_path, data)

    def get_by_id(self, sample_id: str) -> Optional[Sample]:
        data = _json_store.read_json(self._file_path)
        raw = data.get(sample_id)
        return self._from_dict(raw) if raw is not None else None

    def get_all(self) -> list[Sample]:
        data = _json_store.read_json(self._file_path)
        return [self._from_dict(raw) for raw in data.values()]

    def search_by_name(self, keyword: str) -> list[Sample]:
        keyword_lower = keyword.lower()
        return [s for s in self.get_all() if keyword_lower in s.name.lower()]

    def update(self, sample: Sample) -> None:
        self.add(sample)

    def delete(self, sample_id: str) -> None:
        data = _json_store.read_json(self._file_path)
        data.pop(sample_id, None)
        _json_store.write_json(self._file_path, data)

    @staticmethod
    def _to_dict(sample: Sample) -> dict:
        return {
            "sample_id": sample.sample_id,
            "name": sample.name,
            "avg_production_time": sample.avg_production_time,
            "yield_rate": sample.yield_rate,
            "stock": sample.stock,
        }

    @staticmethod
    def _from_dict(raw: dict) -> Sample:
        return Sample(
            sample_id=raw["sample_id"],
            name=raw["name"],
            avg_production_time=raw["avg_production_time"],
            yield_rate=raw["yield_rate"],
            stock=raw["stock"],
        )
