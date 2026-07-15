# 태스크 5 계획: 시료/주문 컨트롤러 (`controller/sample_,order_`) — Red-Green-Review

## Context

`repository/`(태스크4)가 끝났다는 전제로 진행한다. 이 태스크에서 처음으로 재고 예약 모델
(CLAUDE.md 핵심 설계 결정)이 코드로 구현된다. `OrderController`는 재고 부족 분기에서
`ProductionController`(태스크6에서 구현)를 호출해야 하므로, 이 태스크는 `ProductionController`의
퍼블릭 인터페이스(특히 `enqueue`)를 먼저 확정한 뒤 생성자 주입으로 의존하게 만든다. 실제
`ProductionController` 구현은 태스크6에서 하되, 이 태스크의 테스트에서는 테스트 더블(간단한
스텁/페이크 또는 실제 `ProductionJobRepository`를 직접 조립한 최소 버전)로 대체 가능하다 — 태스크6
착수 시점에 실제 구현으로 자연스럽게 맞물리는지 재확인한다.

레이어 규칙: `controller`는 `repository`/`model`만 import한다. `OrderController → ProductionController`
단방향 의존만 허용하고 역방향은 금지한다 (architecture-guardian 검토 대상).

## 확정 설계

### `controller/sample_controller.py`

- `register(sample_id, name, avg_production_time, yield_rate, stock=0) -> Sample`
- `list_all() -> list[Sample]`
- `search_by_name(keyword) -> list[Sample]` (repository에 위임)

### `controller/order_controller.py`

- 생성자: `OrderController(order_repo, sample_repo, production_controller)`
- `place_order(sample_id, customer_name, quantity) -> Order`
  - 등록되지 않은 `sample_id` → `ValueError` (PRD §5 "[2] 시료 주문" — 등록 안 된 시료 거부)
  - `quantity < 1` → `ValueError`
  - `order_id`는 CONVENTIONS.md `_generate_order_id()` (`ORD-{YYYYMMDD}-{hex4}`)
- `list_reserved() -> list[Order]` (승인/거절 메뉴용, `get_by_status(RESERVED)` 위임)
- `approve(order_id) -> Order`
  - `sample.stock >= order.quantity` → 즉시 `CONFIRMED`, `sample.stock -= order.quantity`
  - `sample.stock < order.quantity` → `shortage = order.quantity - sample.stock`, **`sample.stock = 0`**,
    `production_controller.enqueue(order_id, sample_id, shortage, sample.yield_rate, sample.avg_production_time)`
    호출 후 주문 상태를 `PRODUCING`으로 변경
  - 두 분기 모두 `sample_repo.update(sample)`, `order_repo.update(order)` 호출
- `reject(order_id) -> Order` — 즉시 `REJECTED`
- `complete_production(job) -> Order` — `ProductionController.advance_time`이 반환한 완료된
  `ProductionJob`을 받아 `sample.stock += job.shortage`, 해당 주문을 `PRODUCING → CONFIRMED`로 전환
  (호출 주체는 view/main.py — 태스크6 계획 참고. `OrderController`가 이 메서드를 갖고 `ProductionController`가
  이를 호출하지 않는 것이 단방향 의존 유지의 핵심)
- `release(order_id) -> Order` — `CONFIRMED → RELEASE` (태스크는 6번 출고 메뉴지만 상태 전이 자체는
  `OrderController` 책임이므로 이 태스크에서 같이 구현. 뷰 배선은 태스크8)

## Phase 세분화

### Phase 1 — RED

- 1.1 `tests/conftest.py`에 `sample_controller`, `order_controller` 픽스처 추가 (fake/stub
  `production_controller`도 함께 — 예: `enqueue` 호출을 기록만 하는 간단한 테스트 더블)
- 1.2 `tests/test_sample_controller.py`
  - `test_register_persists_sample_with_given_fields`
  - `test_search_by_name_delegates_to_repository`
- 1.3 `tests/test_order_controller.py`
  - `test_place_order_creates_reserved_order`
  - `test_place_order_rejects_unregistered_sample`
  - `test_place_order_rejects_quantity_below_one`
  - `test_approve_with_sufficient_stock_confirms_and_deducts_stock`
  - `test_approve_with_insufficient_stock_moves_to_producing_and_zeroes_stock`
  - `test_approve_with_insufficient_stock_calls_production_controller_enqueue_with_shortage`
  - `test_reject_moves_order_to_rejected`
  - `test_complete_production_restores_shortage_and_confirms_order`
  - `test_release_moves_confirmed_order_to_release`
- `controller/` 파일이 없으므로 `ModuleNotFoundError`로 전부 실패 확인 후 **커밋 5a (RED)**

### Phase 2 — GREEN

- 2.1 `controller/sample_controller.py`
- 2.2 `controller/order_controller.py`
- `pytest -v` 전체 통과 확인 후 **커밋 5b (GREEN)**

### Phase 3 — REVIEW

- 3.1 `verify` 스킬로 pytest/커버리지 재확인
- 3.2 `architecture-guardian` — `OrderController → ProductionController` 단방향 의존 확인(역방향 import
  없는지), 재고 예약 모델 불변식(승인 시 즉시 차감, 이중 소비 없는지) 검토
- 3.3 `code-review`/`simplify` — 검증 로직 중복, 네이밍 등 검토
- 3.4 지적사항 반영 후 **커밋 5c (REVIEW)** (없으면 생략, 사유 보고)

## 검증

- Phase마다 `pytest -v` 실행 결과 확인
- 특히 GREEN 단계에서 "이중 소비 버그가 실제로 재발하지 않는지"를 확인하는 테스트
  (`test_approve_with_insufficient_stock_moves_to_producing_and_zeroes_stock`)가 통과하는지 중점 확인
- `git log --oneline`으로 5a/5b/5c 커밋 확인, push는 사용자 확인 후 진행
