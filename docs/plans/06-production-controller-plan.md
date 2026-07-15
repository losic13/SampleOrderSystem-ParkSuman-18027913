# 태스크 6 계획: 생산 컨트롤러 (`controller/production_`) — Red-Green-Review

## Context

`repository/`(태스크4)와 `OrderController`(태스크5)가 끝났다는 전제로 진행한다. 이 저장소가
처음으로 구현하는 생산라인 FIFO 큐 + 수동 tick 시뮬레이션이다. 태스크5에서 `OrderController`가
이미 `ProductionController.enqueue(...)`를 호출하는 형태로 배선돼 있으므로, 여기서는 그 인터페이스를
실제로 채우고 태스크5의 테스트 더블을 실제 구현으로 교체해 통합이 맞는지 재확인한다.

**단방향 의존 재확인**: `ProductionController`는 `OrderController`/`Order`를 import하지 않는다.
생산 완료 시 주문 상태를 `PRODUCING → CONFIRMED`로 바꾸고 재고를 복원하는 책임은 `OrderController.
complete_production(job)`(태스크5에서 확정)에 있다. `ProductionController.advance_time`은 단지
**완료된 `ProductionJob` 목록을 반환**할 뿐이고, 그 목록을 받아 `OrderController.complete_production`을
호출하는 것은 상위 계층(뷰/main.py, 태스크8)의 책임이다. 이렇게 해야 `ProductionController`가
`OrderController`를 몰라도 되는 OCP 원칙이 유지된다.

## 확정 설계

### `controller/production_controller.py`

- 생성자: `ProductionController(production_job_repo)`
- `enqueue(order_id, sample_id, shortage, yield_rate, avg_production_time) -> ProductionJob`
  - `actual_quantity = math.ceil(shortage / yield_rate)` (PRD §7)
  - `total_minutes = round(avg_production_time * actual_quantity)` — 분 단위 정수로 저장
    (`ProductionJob.total_minutes: int`이므로 반올림. 소수점 처리 방식은 GREEN 단계에서 확정하고
    이유를 REVIEW에서 재검토)
  - `ProductionJob(order_id, sample_id, shortage, actual_quantity, total_minutes)` 생성 후 repo에 `add`
- `list_queue() -> list[ProductionJob]` — `production_job_repo.get_all()` 위임 (FIFO 순서 보존)
- `current_job() -> Optional[ProductionJob]` — 큐의 첫 번째 작업 (없으면 `None`)
- `advance_time(minutes) -> list[ProductionJob]`
  - 큐가 비어 있으면 빈 리스트 반환
  - 현재 작업(큐의 첫 번째)에만 `elapsed_minutes += minutes` 적용 (생산라인은 1개, 나머지 대기 작업은
    영향 없음 — PRD §7 "생산라인은 1개만 존재" 원칙)
  - `is_complete`가 되면 repo에서 `delete`(큐에서 제거)하고 완료 목록에 추가, 완료 목록을 반환
  - 한 번의 `advance_time` 호출로 여러 작업이 연쇄 완료될 가능성은 다루지 않는다 (분 입력이 항상
    현재 작업 하나를 완료시키는 정도로 사용된다고 가정 — PRD 비목표 항목과 일관되게 단순 모델 유지.
    현재 작업의 `total_minutes`를 초과하는 분을 입력해도 초과분은 다음 작업으로 이월되지 않고
    버려진다 — **사용자 확인 완료된 의도적 단순화**. 만약 초과분이 다음 작업으로 이월돼야 한다는
    요구가 나오면 이 가정을 재검토해야 함)

## Phase 세분화

### Phase 1 — RED

- 1.1 `tests/conftest.py`에 `production_controller` 픽스처 추가 (`production_job_repo` 픽스처 기반)
- 1.2 `tests/test_production_controller.py`
  - `test_enqueue_computes_actual_quantity_as_ceil_shortage_over_yield_rate`
  - `test_enqueue_computes_total_minutes_as_avg_time_times_actual_quantity`
  - `test_list_queue_preserves_fifo_order_across_multiple_enqueues`
  - `test_current_job_returns_first_job_in_queue`
  - `test_current_job_returns_none_when_queue_empty`
  - `test_advance_time_increments_elapsed_minutes_of_current_job_only`
  - `test_advance_time_completes_and_dequeues_job_when_elapsed_reaches_total`
  - `test_advance_time_returns_empty_list_when_no_job_completes`
  - `test_advance_time_promotes_next_job_to_current_after_completion`
- `controller/production_controller.py`가 없으므로 `ModuleNotFoundError`로 전부 실패 확인 후
  **커밋 6a (RED)**

### Phase 2 — GREEN

- 2.1 `controller/production_controller.py` 구현
- 2.2 태스크5의 `OrderController` 테스트에서 쓰던 fake `production_controller`를 실제
  `ProductionController`로 교체 가능한지 `tests/test_order_controller.py` 재확인 (필요 시 fixture만
  조정, 프로덕션 코드 변경 없음)
- `pytest -v` 전체 통과 확인 후 **커밋 6b (GREEN)**

### Phase 3 — REVIEW

- 3.1 `verify` 스킬로 pytest/커버리지 재확인
- 3.2 `architecture-guardian` — `ProductionController`가 `OrderController`/`Order`를 import하지
  않는지(단방향 의존 확인), FIFO 큐 순서 보장이 `_json_store`/dict 삽입 순서 원칙과 일치하는지 검토
- 3.3 `code-review`/`simplify` — `math.ceil` 경계값, 부동소수점 처리 등 검토
- 3.4 지적사항 반영 후 **커밋 6c (REVIEW)** (없으면 생략, 사유 보고)

## 검증

- Phase마다 `pytest -v` 실행 결과 확인
- FIFO 순서(`list_queue`)와 "현재 작업만 진행"(`advance_time`) 두 불변식이 테스트로 실제 커버되는지 중점 확인
- `git log --oneline`으로 6a/6b/6c 커밋 확인, push는 사용자 확인 후 진행
