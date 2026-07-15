from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    shortage: int
    actual_quantity: int
    total_minutes: int
    elapsed_minutes: int = 0
    enqueued_at: datetime = field(default_factory=datetime.now)

    @property
    def is_complete(self) -> bool:
        return self.elapsed_minutes >= self.total_minutes

    @property
    def progress_ratio(self) -> float:
        if self.total_minutes == 0:
            return 1.0
        return min(self.elapsed_minutes / self.total_minutes, 1.0)
