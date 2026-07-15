from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from model.order import Order
from model.order_status import OrderStatus
from repository import _json_store


class OrderRepository(ABC):
    @abstractmethod
    def add(self, order: Order) -> None: ...

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]: ...

    @abstractmethod
    def get_all(self) -> list[Order]: ...

    @abstractmethod
    def get_by_status(self, status: OrderStatus) -> list[Order]: ...

    @abstractmethod
    def update(self, order: Order) -> None: ...

    @abstractmethod
    def delete(self, order_id: str) -> None: ...


class JsonOrderRepository(OrderRepository):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        _json_store.ensure_file(self._file_path)

    def add(self, order: Order) -> None:
        data = _json_store.read_json(self._file_path)
        data[order.order_id] = self._to_dict(order)
        _json_store.write_json(self._file_path, data)

    def get_by_id(self, order_id: str) -> Optional[Order]:
        data = _json_store.read_json(self._file_path)
        raw = data.get(order_id)
        return self._from_dict(raw) if raw is not None else None

    def get_all(self) -> list[Order]:
        data = _json_store.read_json(self._file_path)
        return [self._from_dict(raw) for raw in data.values()]

    def get_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self.get_all() if o.status == status]

    def update(self, order: Order) -> None:
        self.add(order)

    def delete(self, order_id: str) -> None:
        data = _json_store.read_json(self._file_path)
        data.pop(order_id, None)
        _json_store.write_json(self._file_path, data)

    @staticmethod
    def _to_dict(order: Order) -> dict:
        return {
            "order_id": order.order_id,
            "sample_id": order.sample_id,
            "customer_name": order.customer_name,
            "quantity": order.quantity,
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
        }

    @staticmethod
    def _from_dict(raw: dict) -> Order:
        return Order(
            order_id=raw["order_id"],
            sample_id=raw["sample_id"],
            customer_name=raw["customer_name"],
            quantity=raw["quantity"],
            status=OrderStatus(raw["status"]),
            created_at=datetime.fromisoformat(raw["created_at"]),
        )
