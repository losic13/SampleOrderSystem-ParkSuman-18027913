from model.order_status import OrderStatus
from repository.order_repository import OrderRepository
from repository.sample_repository import SampleRepository

MONITORED_STATUSES = (
    OrderStatus.RESERVED,
    OrderStatus.CONFIRMED,
    OrderStatus.PRODUCING,
    OrderStatus.RELEASE,
)


class MonitorService:
    def __init__(self, order_repo: OrderRepository, sample_repo: SampleRepository) -> None:
        self._order_repo = order_repo
        self._sample_repo = sample_repo

    def count_orders_by_status(self) -> dict[OrderStatus, int]:
        return {
            status: len(self._order_repo.get_by_status(status))
            for status in MONITORED_STATUSES
        }

    def classify_stock(self) -> dict[str, str]:
        reserved_orders = self._order_repo.get_by_status(OrderStatus.RESERVED)
        result = {}
        for sample in self._sample_repo.get_all():
            reserved_quantity = sum(
                order.quantity for order in reserved_orders if order.sample_id == sample.sample_id
            )
            if sample.stock == 0:
                result[sample.sample_id] = "고갈"
            elif sample.stock < reserved_quantity:
                result[sample.sample_id] = "부족"
            else:
                result[sample.sample_id] = "여유"
        return result
