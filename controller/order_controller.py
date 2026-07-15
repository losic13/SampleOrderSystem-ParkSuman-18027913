import uuid
from datetime import datetime

from model.order import Order
from model.order_status import OrderStatus
from model.production_job import ProductionJob
from repository.order_repository import OrderRepository
from repository.sample_repository import SampleRepository


class OrderController:
    def __init__(
        self,
        order_repo: OrderRepository,
        sample_repo: SampleRepository,
        production_controller,
    ) -> None:
        self._order_repo = order_repo
        self._sample_repo = sample_repo
        self._production_controller = production_controller

    def place_order(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        if self._sample_repo.get_by_id(sample_id) is None:
            raise ValueError(f"registered sample not found: {sample_id}")
        if quantity < 1:
            raise ValueError("quantity must be at least 1")

        order = Order(
            order_id=self._generate_order_id(),
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
        )
        self._order_repo.add(order)
        return order

    def list_reserved(self) -> list[Order]:
        return self._order_repo.get_by_status(OrderStatus.RESERVED)

    def list_confirmed(self) -> list[Order]:
        return self._order_repo.get_by_status(OrderStatus.CONFIRMED)

    def approve(self, order_id: str) -> Order:
        order = self._get_order_in_status(order_id, OrderStatus.RESERVED)
        sample = self._sample_repo.get_by_id(order.sample_id)

        if sample.stock >= order.quantity:
            sample.stock -= order.quantity
            order.status = OrderStatus.CONFIRMED
        else:
            shortage = order.quantity - sample.stock
            sample.stock = 0
            self._production_controller.enqueue(
                order.order_id, sample.sample_id, shortage, sample.yield_rate,
                sample.avg_production_time,
            )
            order.status = OrderStatus.PRODUCING

        self._sample_repo.update(sample)
        self._order_repo.update(order)
        return order

    def reject(self, order_id: str) -> Order:
        order = self._get_order_in_status(order_id, OrderStatus.RESERVED)
        order.status = OrderStatus.REJECTED
        self._order_repo.update(order)
        return order

    def complete_production(self, job: ProductionJob) -> Order:
        order = self._order_repo.get_by_id(job.order_id)
        sample = self._sample_repo.get_by_id(job.sample_id)

        sample.stock += job.shortage
        order.status = OrderStatus.CONFIRMED

        self._sample_repo.update(sample)
        self._order_repo.update(order)
        return order

    def release(self, order_id: str) -> Order:
        order = self._get_order_in_status(order_id, OrderStatus.CONFIRMED)
        order.status = OrderStatus.RELEASE
        self._order_repo.update(order)
        return order

    def _get_order_in_status(self, order_id: str, expected_status: OrderStatus) -> Order:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise ValueError(f"order not found: {order_id}")
        if order.status != expected_status:
            raise ValueError(
                f"order is not {expected_status.value}: {order_id} ({order.status.value})"
            )
        return order

    @staticmethod
    def _generate_order_id() -> str:
        return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
