# 태스크 7 계획: 모니터링 서비스 (`monitor/`) — Red-Green-Review

## Context

`repository/`(태스크4)가 끝났다는 전제로 진행한다. DataMonitor PoC의 재고 분류(여유/부족/고갈)
골격을 계승하되, 이 저장소의 재고 예약 모델에 맞게 미해결 수요 계산 공식을 조정한다
(CLAUDE.md 핵심 설계 결정 — `PRODUCING`은 이미 재고를 0으로 예약 처리했으므로 미해결 수요에서 제외).

`monitor`는 조회 전용이며 `order_repo`/`sample_repo`를 읽기만 한다 (CUD 없음). `controller`를
import하지 않는다 (architecture-guardian 검토 대상 — `view → monitor` 직접 호출 관계).

## 확정 설계

### `monitor/monitor_service.py`

- 생성자: `MonitorService(order_repo, sample_repo)`
- 상수: `MONITORED_STATUSES = (RESERVED, CONFIRMED, PRODUCING, RELEASE)` — `REJECTED` 제외
  (PRD §5 "[4] 모니터링 — 주문량 확인": `REJECTED` 제외 명시)
- `count_orders_by_status() -> dict[OrderStatus, int]`
  - `MONITORED_STATUSES` 각각에 대해 `order_repo.get_by_status(status)` 개수 집계
- `classify_stock() -> dict[str, str]` (sample_id → "여유"/"부족"/"고갈") 또는 이름 붙은 결과 객체
  (GREEN 단계에서 반환 타입 확정 — 문자열 리터럴보다 별도 `StockStatus` Enum이 나을지 REVIEW에서
  단순성 관점으로 재검토)
  - 시료별 `reserved_quantity = sum(order.quantity for RESERVED orders of this sample_id)`
  - `sample.stock == 0` → 고갈
  - `sample.stock < reserved_quantity` → 부족
  - 그 외 → 여유
  - **`PRODUCING` 주문 수량은 집계에 포함하지 않는다** (승인 시 이미 재고 0 차감 완료 — 이중 계산 방지.
    이 지점이 DataMonitor PoC와 달라지는 유일한 공식 차이)

## Phase 세분화

### Phase 1 — RED

- 1.1 `tests/conftest.py`에 `monitor_service` 픽스처 추가 (`order_repo`, `sample_repo` 픽스처 기반)
- 1.2 `tests/test_monitor_service.py`
  - `test_count_orders_by_status_excludes_rejected`
  - `test_count_orders_by_status_counts_each_monitored_status_correctly`
  - `test_classify_stock_returns_gone_when_stock_is_zero`
  - `test_classify_stock_returns_shortage_when_stock_below_reserved_quantity`
  - `test_classify_stock_returns_sufficient_when_stock_covers_reserved_quantity`
  - `test_classify_stock_ignores_producing_order_quantity_in_shortage_calculation`
    (재고 예약 모델 정합성 확인 핵심 테스트 — `PRODUCING` 주문이 있어도 부족 판정에 영향 없어야 함)
- `monitor/` 파일이 없으므로 `ModuleNotFoundError`로 전부 실패 확인 후 **커밋 7a (RED)**

### Phase 2 — GREEN

- 2.1 `monitor/monitor_service.py` 구현
  - 2.1a `count_orders_by_status`
  - 2.1b `classify_stock`
- `pytest -v` 전체 통과 확인 후 **커밋 7b (GREEN)**

### Phase 3 — REVIEW

- 3.1 `verify` 스킬로 pytest/커버리지 재확인
- 3.2 `architecture-guardian` — `monitor`가 읽기 전용인지(update/delete 호출 없는지), `controller`를
  import하지 않는지, 재고 예약 모델과의 공식 정합성(위 "PRODUCING 제외" 규칙) 재확인
- 3.3 `code-review`/`simplify` — 반환 타입(딕셔너리 vs 전용 타입) 적절성, 중복 순회 등 검토
- 3.4 지적사항 반영 후 **커밋 7c (REVIEW)** (없으면 생략, 사유 보고)

## 검증

- Phase마다 `pytest -v` 실행 결과 확인
- `test_classify_stock_ignores_producing_order_quantity_in_shortage_calculation`이 실제로 DataMonitor
  원래 공식과 다른 지점을 커버하는지 중점 확인
- `git log --oneline`으로 7a/7b/7c 커밋 확인, push는 사용자 확인 후 진행
