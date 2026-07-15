# 태스크 9 계획: 종단 시나리오 테스트 — Red-Green-Review

## Context

태스크 3~8(모델/저장소/컨트롤러/생산라인/모니터링/뷰+진입점)이 모두 끝났다는 전제로 진행한다.
개별 계층 단위테스트는 이미 갖춰져 있으므로, 이 태스크는 **전 계층을 실제로 조립한 상태에서
PRD.md §4 상태 흐름 중 가장 복잡한 경로(재고 부족 → 생산 → 완료)가 처음부터 끝까지 맞물려
동작하는지**를 검증하는 통합 테스트 1개(+필요 시 보조 테스트 소수)를 추가한다. `view`(콘솔 I/O)는
호출하지 않고, `controller`/`monitor`를 직접 조립해 호출한다 (콘솔 입출력 자체는 태스크8에서 수동
시나리오로 이미 확인됨).

이 태스크가 끝나면 `/verify` 스킬을 1차로 전체 호출해 pytest+coverage+main.py 스모크까지 종합
확인한다 (CLAUDE.md Harness 섹션).

## 확정 시나리오

`tests/test_end_to_end_scenario.py` 단일 파일, 실제 파일 시스템(`tmp_path`)에 3개 JSON 저장소를
두고 `SampleController`/`OrderController`/`ProductionController`/`MonitorService`를 실제 구현으로
조립한다 (fake 없음 — 태스크5/6에서 쓰인 테스트 더블은 여기서 전부 실제 구현으로 교체).

1. 시료 등록: `stock=5`인 시료 1건 등록
2. 주문 접수: 수량 12인 주문 1건 접수 (`RESERVED`)
3. 모니터링 확인: 부족 상태로 분류됨 (`stock(5) < reserved_quantity(12)`)
4. 승인: 재고 부족 → `shortage=7`, `sample.stock`이 즉시 0, 주문 `PRODUCING`, 생산 큐에 1건 enqueue
   (`actual_quantity = ceil(7/yield_rate)`, `total_minutes` 계산값 확인)
5. 모니터링 재확인: 이 시점에는 `RESERVED` 주문이 없으므로(방금 승인 처리됨) 부족 판정에 영향 없음 —
   `PRODUCING` 수량이 집계에서 빠지는 것 재확인 (태스크7 GREEN에서 이미 단위테스트로 커버했지만
   종단 흐름에서도 한 번 더 확인)
6. `[T] 시간 경과` 일부 진행: `total_minutes`보다 적은 분만큼 `advance_time` 호출 →
   `current_job().progress_ratio`가 0과 1 사이, 완료 목록은 빈 리스트
7. 나머지 분만큼 `advance_time` 호출해 완료시킴 → 완료된 job을 받아 `order_controller.
   complete_production(job)` 호출 → `sample.stock == shortage(7)`, 주문 `CONFIRMED`
8. 출고 처리: `order_controller.release(order_id)` → 주문 `RELEASE`
9. 최종 모니터링 확인: 상태별 주문 수 집계에 이 주문이 `RELEASE`로 카운트, `REJECTED`는 여전히
   집계 대상 아님(별도 거절 주문 1건을 추가로 만들어 재확인)

## Phase 세분화

### Phase 1 — RED

- 1.1 `tests/test_end_to_end_scenario.py`
  - `test_full_order_lifecycle_from_reservation_to_release_via_production_queue`
    (위 확정 시나리오 1~9단계를 하나의 함수로, 단계별로 주석 없이 assert 그룹으로 구분 — 시나리오
    자체가 문서 역할을 하므로 각 assert 직전에 무엇을 확인하는지는 변수명으로 표현)
  - `test_rejected_order_excluded_from_status_monitoring` (보조 테스트, 8번 항목 분리 검증)
- 아직 전 계층 조립 코드(특히 `main.py`/`view`의 조립 로직을 참고할 `controller` 생성자 시그니처
  변경 가능성)가 실제로 이 형태로 맞물리는지가 불확실하므로, 최초 실행 시 `ModuleNotFoundError`
  또는 시그니처 불일치로 실패하는 것을 "의도한 실패"로 확인 후 **커밋 9a (RED)**
  (주: 태스크3~7 GREEN이 이미 끝난 상태라 일부 어서션은 우연히 통과할 수도 있음 — 이 경우 RED 커밋
  기준을 "전체 시나리오 테스트가 아직 존재하지 않았다"는 사실 자체로 삼고, 실패하는 지점이 최소 하나
  이상 있는지 확인한다)

### Phase 2 — GREEN

- 2.1 시나리오 테스트가 통과하도록 필요한 최소 수정 (계층 간 시그니처 불일치, 조립 순서 등 — 새 기능
  추가가 아니라 기존 구현의 통합 지점 보정에 한정)
- `pytest -v` 전체 통과 확인 후 **커밋 9b (GREEN)**

### Phase 3 — REVIEW

- 3.1 `/verify` 스킬 1차 전체 호출 — pytest, `--cov`(전 계층 커버리지 목표 확인), `main.py` 스모크
  실행(입력 파이프 시나리오 포함), `data/` 파일 오염 여부 확인
- 3.2 `architecture-guardian` — 종단 테스트가 계층 의존 방향을 우회하지 않는지(예: 테스트가 직접
  JSON 파일을 조작하지 않고 repository API만 쓰는지) 검토
- 3.3 `code-review`/`simplify` — 시나리오 테스트 가독성, 중복 셋업 등 검토
- 3.4 지적사항 반영 후 **커밋 9c (REVIEW)** (없으면 생략, 사유 보고)

## 검증

- Phase마다 `pytest -v` 실행 결과 확인
- 이 태스크 종료 시점에 전체 테스트 스위트(`tests/` 전체)가 통과하는지, 커버리지가 CLAUDE.md/PRD.md
  §11에서 요구한 수준(전 계층 + 종단 시나리오 1개)을 충족하는지 `/verify`로 종합 확인
- `git log --oneline`으로 9a/9b/9c 커밋 확인, push는 사용자 확인 후 진행
