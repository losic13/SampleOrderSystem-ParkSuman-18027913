from model.sample import Sample
from repository.sample_repository import SampleRepository


class SampleController:
    def __init__(self, sample_repo: SampleRepository) -> None:
        self._sample_repo = sample_repo

    def register(
        self,
        sample_id: str,
        name: str,
        avg_production_time: float,
        yield_rate: float,
        stock: int = 0,
    ) -> Sample:
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
            stock=stock,
        )
        self._sample_repo.add(sample)
        return sample

    def list_all(self) -> list[Sample]:
        return self._sample_repo.get_all()

    def search_by_name(self, keyword: str) -> list[Sample]:
        return self._sample_repo.search_by_name(keyword)
