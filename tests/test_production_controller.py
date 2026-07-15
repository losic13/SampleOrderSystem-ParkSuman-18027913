def test_enqueue_computes_actual_quantity_as_ceil_shortage_over_yield_rate(production_controller):
    job = production_controller.enqueue("ORD-1", "SMP-1", 7, 0.5, 10.0)

    assert job.actual_quantity == 14


def test_enqueue_computes_total_minutes_as_avg_time_times_actual_quantity(production_controller):
    job = production_controller.enqueue("ORD-1", "SMP-1", 7, 0.5, 10.0)

    assert job.total_minutes == 140


def test_list_queue_preserves_fifo_order_across_multiple_enqueues(production_controller):
    production_controller.enqueue("ORD-1", "SMP-1", 1, 1.0, 10.0)
    production_controller.enqueue("ORD-2", "SMP-1", 2, 1.0, 10.0)
    production_controller.enqueue("ORD-3", "SMP-1", 3, 1.0, 10.0)

    order_ids = [job.order_id for job in production_controller.list_queue()]

    assert order_ids == ["ORD-1", "ORD-2", "ORD-3"]


def test_current_job_returns_first_job_in_queue(production_controller):
    production_controller.enqueue("ORD-1", "SMP-1", 1, 1.0, 10.0)
    production_controller.enqueue("ORD-2", "SMP-1", 2, 1.0, 10.0)

    assert production_controller.current_job().order_id == "ORD-1"


def test_current_job_returns_none_when_queue_empty(production_controller):
    assert production_controller.current_job() is None


def test_advance_time_increments_elapsed_minutes_of_current_job_only(production_controller):
    production_controller.enqueue("ORD-1", "SMP-1", 1, 1.0, 100.0)
    production_controller.enqueue("ORD-2", "SMP-1", 1, 1.0, 100.0)

    production_controller.advance_time(10)

    queue = production_controller.list_queue()
    assert queue[0].elapsed_minutes == 10
    assert queue[1].elapsed_minutes == 0


def test_advance_time_completes_and_dequeues_job_when_elapsed_reaches_total(production_controller):
    production_controller.enqueue("ORD-1", "SMP-1", 1, 1.0, 10.0)

    completed = production_controller.advance_time(10)

    assert [job.order_id for job in completed] == ["ORD-1"]
    assert production_controller.list_queue() == []


def test_advance_time_returns_empty_list_when_no_job_completes(production_controller):
    production_controller.enqueue("ORD-1", "SMP-1", 1, 1.0, 100.0)

    completed = production_controller.advance_time(10)

    assert completed == []


def test_advance_time_promotes_next_job_to_current_after_completion(production_controller):
    production_controller.enqueue("ORD-1", "SMP-1", 1, 1.0, 10.0)
    production_controller.enqueue("ORD-2", "SMP-1", 1, 1.0, 10.0)

    production_controller.advance_time(10)

    assert production_controller.current_job().order_id == "ORD-2"
