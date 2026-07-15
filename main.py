import sys
from pathlib import Path

from repository.sample_repository import JsonSampleRepository
from repository.order_repository import JsonOrderRepository
from repository.production_job_repository import JsonProductionJobRepository
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from monitor.monitor_service import MonitorService
from view.console_view import ConsoleView

DATA_DIR = Path(__file__).parent / "data"


def _use_utf8_console() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")


def main() -> None:
    _use_utf8_console()

    sample_repo = JsonSampleRepository(DATA_DIR / "samples.json")
    order_repo = JsonOrderRepository(DATA_DIR / "orders.json")
    production_job_repo = JsonProductionJobRepository(DATA_DIR / "production_jobs.json")

    production_controller = ProductionController(production_job_repo)
    sample_controller = SampleController(sample_repo)
    order_controller = OrderController(order_repo, sample_repo, production_controller)
    monitor_service = MonitorService(order_repo, sample_repo)

    view = ConsoleView(sample_controller, order_controller, production_controller, monitor_service)
    view.run()


if __name__ == "__main__":
    main()
