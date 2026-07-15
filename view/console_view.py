from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.sample_controller import SampleController
from monitor.monitor_service import MonitorService


class ConsoleView:
    def __init__(
        self,
        sample_controller: SampleController,
        order_controller: OrderController,
        production_controller: ProductionController,
        monitor_service: MonitorService,
    ) -> None:
        self._sample_controller = sample_controller
        self._order_controller = order_controller
        self._production_controller = production_controller
        self._monitor_service = monitor_service

    def run(self) -> None:
        while True:
            print(
                "\n[1]시료관리 [2]시료주문 [3]주문승인/거절 [4]모니터링 "
                "[5]생산라인조회 [6]출고처리 [0]종료"
            )
            choice = input("메뉴 선택: ").strip()

            if choice == "1":
                self._handle_sample_menu()
            elif choice == "2":
                self._handle_place_order()
            elif choice == "3":
                self._handle_approve_reject()
            elif choice == "4":
                self._handle_monitoring()
            elif choice == "5":
                self._handle_production_line()
            elif choice == "6":
                self._handle_release()
            elif choice == "0":
                print("종료합니다.")
                return
            else:
                print("알 수 없는 메뉴입니다.")

    def _handle_sample_menu(self) -> None:
        print("\n[1]시료등록 [2]시료목록 [3]시료검색 [0]뒤로")
        choice = input("메뉴 선택: ").strip()

        if choice == "1":
            sample_id = input("시료 ID: ").strip()
            name = input("이름: ").strip()
            avg_production_time = float(input("평균 생산시간(분): ").strip())
            yield_rate = float(input("수율(0~1): ").strip())
            stock_input = input("초기 재고(엔터=0): ").strip()
            stock = int(stock_input) if stock_input else 0
            sample = self._sample_controller.register(
                sample_id, name, avg_production_time, yield_rate, stock
            )
            print(f"등록됨: {sample}")
        elif choice == "2":
            for sample in self._sample_controller.list_all():
                print(f"{sample.sample_id} | {sample.name} | 재고 {sample.stock}")
        elif choice == "3":
            keyword = input("검색어: ").strip()
            for sample in self._sample_controller.search_by_name(keyword):
                print(f"{sample.sample_id} | {sample.name} | 재고 {sample.stock}")

    def _handle_place_order(self) -> None:
        sample_id = input("시료 ID: ").strip()
        customer_name = input("고객명: ").strip()
        quantity = int(input("수량: ").strip())
        try:
            order = self._order_controller.place_order(sample_id, customer_name, quantity)
            print(f"주문 접수됨: {order.order_id}")
        except ValueError as e:
            print(f"주문 거부: {e}")

    def _handle_approve_reject(self) -> None:
        reserved = self._order_controller.list_reserved()
        if not reserved:
            print("승인/거절 대기 중인 주문이 없습니다.")
            return
        for order in reserved:
            print(f"{order.order_id} | {order.sample_id} | 수량 {order.quantity} | {order.customer_name}")

        order_id = input("주문 ID: ").strip()
        decision = input("[A]승인 [R]거절: ").strip().upper()
        if decision == "A":
            order = self._order_controller.approve(order_id)
            print(f"승인됨: {order.order_id} -> {order.status.value}")
        elif decision == "R":
            order = self._order_controller.reject(order_id)
            print(f"거절됨: {order.order_id} -> {order.status.value}")

    def _handle_monitoring(self) -> None:
        counts = self._monitor_service.count_orders_by_status()
        print("\n[주문량 확인]")
        for status, count in counts.items():
            print(f"{status.value}: {count}건")

        print("\n[재고량 확인]")
        for sample_id, state in self._monitor_service.classify_stock().items():
            print(f"{sample_id}: {state}")

    def _handle_production_line(self) -> None:
        current = self._production_controller.current_job()
        if current is None:
            print("현재 진행 중인 생산 작업이 없습니다.")
        else:
            print(
                f"현재 작업: {current.order_id} | 실생산량 {current.actual_quantity} | "
                f"진행률 {current.progress_ratio:.0%}"
            )

        print("\n[대기 큐]")
        for job in self._production_controller.list_queue():
            print(f"{job.order_id} | 실생산량 {job.actual_quantity} | 총생산시간 {job.total_minutes}분")

        choice = input("\n[T]시간 경과 [0]뒤로: ").strip().upper()
        if choice == "T":
            minutes = int(input("경과시킬 분: ").strip())
            completed_jobs = self._production_controller.advance_time(minutes)
            for job in completed_jobs:
                order = self._order_controller.complete_production(job)
                print(f"생산 완료: {job.order_id} -> {order.status.value}")

    def _handle_release(self) -> None:
        confirmed = self._order_controller.list_confirmed()
        if not confirmed:
            print("출고 대기 중인 주문이 없습니다.")
            return
        for order in confirmed:
            print(f"{order.order_id} | {order.sample_id} | 수량 {order.quantity} | {order.customer_name}")

        order_id = input("출고 처리할 주문 ID: ").strip()
        order = self._order_controller.release(order_id)
        print(f"출고 완료: {order.order_id} -> {order.status.value}")
