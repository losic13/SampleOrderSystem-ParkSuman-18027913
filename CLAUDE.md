# CLAUDE.md

이 문서는 이 저장소에서 작업을 이어갈 에이전트(또는 사람)를 위한 컨텍스트 요약이다.

## 과제 배경

가상 반도체 회사 "S-Semi"의 **반도체 시료 생산주문관리 시스템** 개인과제(mincoding, Sonnet/Effort:Medium 지정)의 마지막 저장소다.

| 저장소 | 역할 | 상태 |
|---|---|---|
| ConsoleMVC | PoC1 — MVC 스켈레톤 | 완료 |
| DataPersistence | PoC1 — 데이터 영속성 처리 (JSON 파일, CRUD) | 완료 |
| DataMonitor | PoC1 — 데이터 실시간 모니터링 콘솔 도구 | 완료 |
| DummyDataGenerator | PoC1 — 테스트용 더미 데이터 생성 | 완료 |
| **SampleOrderSystem** (이 저장소) | 미션2 — 4개 PoC 설계를 계승한 최종 통합 시스템 | **진행 중 — 현재 문서/스캐폴딩만 커밋됨, 구현 시작 전** |

과제 원본 명세: https://pro.mincoding.co.kr/public/upload/nzzlbz2baj.pdf
제품 요구사항 상세는 `PRD.md` 참고.

## 이번 저장소를 향한 사용자의 명시적 요구사항

- unit test + clean code 관점을 엄격히 지킬 것
- `PRD.md`, `CLAUDE.md` 등 문서 관리
- Harness 도입: **pytest + coverage + 프로젝트 전용 `/verify` 스킬** (CI, pre-commit은 범위 밖으로 합의됨)
- 태스크 단위로 자주 커밋 (아래 "커밋 계획" 참고), 매 태스크 완료 시 검토 요청받고 진행

**진행 방식(중요)**: 이번 저장소는 계획 전체를 한 번에 실행하지 않고, **각 태스크(커밋) 단위로 사용자에게
검토를 요청한 뒤 다음 단계로 진행**하기로 합의했다. 현재는 계획 승인 후 1번째 태스크(문서/스캐폴딩)만
완료된 상태이며, 사용자 검토 후 다음 태스크(모델 계층)로 진행할 예정이다.

## 다른 저장소와의 관계 (설계 계승, 코드 복사 아님)

- 각 저장소는 독립 코드베이스라는 과제 요구사항 때문에, 이전 저장소들의 코드를 import하지 않고
  **검증된 설계만 계승해 새로 작성**한다.
- `model/`, `repository/`(ABC+Json 페어링, `_json_store.py` 헬퍼): ConsoleMVC/DataPersistence 패턴 그대로.
- `monitor/`: DataMonitor의 재고 분류(여유/부족/고갈) 골격을 계승하되, 공식은 이 저장소의 재고 예약 모델에
  맞게 조정한다 (아래 참고).
- **이 저장소가 처음으로 구현하는 것**: 생산라인 FIFO 큐 + 시간 진행 시뮬레이션. 4개 PoC의 CLAUDE.md 모두
  "생산라인 시뮬레이션은 SampleOrderSystem에서 구현 예정"이라고 명시해뒀던 부분이다.

### 저장소 간 불일치 해소 (Explore 조사로 확인, 이 저장소에서 통일한 규칙)

- **주문 ID 포맷**: ConsoleMVC는 `ORD-{YYYYMMDD}-{hex4}`, DataPersistence/DummyDataGenerator는 `ORD-{hex8}`였다.
  실제 주문 승인/거절 로직을 갖고 있던 ConsoleMVC 포맷(`ORD-{YYYYMMDD}-{hex4}`)으로 통일한다.
- **시료 ID**: 사용자가 직접 입력하는 방식(ConsoleMVC/DataPersistence 방식)을 따른다. DummyDataGenerator류의
  자동 생성 로직은 이 저장소 범위 밖이다.

## 핵심 설계 결정: 생산라인 재고 예약 모델

**문제**: ConsoleMVC의 단순 모델(재고 부족 시 `PRODUCING`으로만 전환하고 재고는 건드리지 않음)을 그대로
가져오면, `PRODUCING` 전환 후에도 잔여 재고가 여전히 "가용"으로 남아있어 같은 시료의 다른 주문이 그
재고를 또 승인받아 이중 소비할 수 있는 버그가 생긴다.

**해결**:
1. 승인 시 재고 부족 분기: `shortage = order.quantity - sample.stock` 계산 후 **`sample.stock`을 즉시 0으로
   차감**한다 (CONFIRMED 분기가 항상 재고를 즉시 차감하는 것과 동일한 원칙 — "승인된 주문은 그 순간 재고를
   확정 소비한다"). 이후 `ProductionJob`을 생성해 큐에 등록하고 주문 상태를 `PRODUCING`으로 바꾼다.
2. 생산 완료 시(tick으로 `elapsed_minutes >= total_minutes`가 되면): `sample.stock += job.shortage`, 주문
   상태를 `PRODUCING → CONFIRMED`로 바꾼다.
3. 이 덕분에 같은 시료에 여러 주문이 동시에 `PRODUCING` 상태여도 이중 소비 없이 순차적으로 정산된다
   (생산라인이 하나뿐이라 FIFO로 한 번에 하나씩만 진행되는 것과도 일치).

**이 결정을 되돌리지 말 것**: 만약 나중에 누군가 "ConsoleMVC와 똑같이 재고를 건드리지 않도록" 되돌리면
위 이중 예약 버그가 재발한다. 수정하려면 이 설명을 먼저 이해할 것.

**모니터링 재고 판정 공식도 이에 맞춰 조정**: DataMonitor는 `RESERVED`+`PRODUCING` 주문을 모두 미해결
수요로 계산했지만, 이 저장소는 `PRODUCING` 전환 시 재고를 이미 0으로 예약 처리하므로 **`RESERVED`만
미해결 수요**로 계산한다. (부족 = `재고 < RESERVED 주문 수량 합`, 고갈 = `재고 0`)

## 생산라인 시간 진행 방식

실제 시계(wall-clock)가 아닌 **수동 tick 기반**이다. 사용자가 "[T] 시간 경과" 메뉴에서 분(minute) 값을
직접 입력하면 그만큼 현재 처리 중인 생산 작업의 `elapsed_minutes`가 증가하고, `total_minutes`에 도달하면
자동으로 완료 처리된다. 이유: 결정적(deterministic)이라 unit-test로 검증하기 쉽고, 실제 타이머/스레드로
인한 플레이키(flaky) 테스트를 피할 수 있다. (사용자 확인 완료 사항)

## 계획된 아키텍처 (구현 예정, 아래 "다음 태스크" 참고)

```
model/
  sample.py, order.py, order_status.py     # 기존 저장소들과 동일 필드/Enum
  production_job.py                          # 신규: order_id, sample_id, shortage, actual_quantity,
                                               total_minutes, elapsed_minutes, enqueued_at,
                                               is_complete/progress_ratio 프로퍼티
repository/
  _json_store.py                              # DataPersistence와 동일
  sample_repository.py, order_repository.py   # DataPersistence와 동일 (CRUD)
  production_job_repository.py                # 신규: order_id를 dict 키로 사용 (FIFO = insertion order)
controller/
  sample_controller.py                        # ConsoleMVC와 동일
  order_controller.py                         # ConsoleMVC 계승 + 재고부족 분기에서 ProductionController.enqueue
                                               호출 (생성자 주입, 단방향 의존 — ProductionController는
                                               OrderController를 모른다)
  production_controller.py                    # 신규: enqueue/list_queue/current_job/advance_time(minutes)
monitor/
  monitor_service.py                           # DataMonitor 계승, 공식은 위 결정대로 조정
view/
  console_view.py                              # PDF 예시 메뉴: [1]시료관리 [2]시료주문 [3]주문승인/거절
                                               [4]모니터링 [5]생산라인조회(+[T]시간경과) [6]출고처리 [0]종료
main.py                                        # 의존성 조립 + Windows UTF-8 콘솔 강제 설정
data/                                          # samples.json/orders.json/production_jobs.json (gitignore 대상)
tests/                                          # conftest.py + 계층별 테스트 + 종단 시나리오 테스트 1개
```

## 커밋 계획 (태스크 단위, 매 태스크 후 사용자 검토)

1. ✅ **문서/스캐폴딩** — `.gitignore`, `pyproject.toml`(pytest+coverage), `requirements-dev.txt`, `PRD.md`, `CLAUDE.md` (이 커밋)
2. ⬜ 도메인 모델 (`model/`) + 단위테스트
3. ⬜ JSON 저장소 계층 (`repository/` — sample/order/production job) + 단위테스트
4. ⬜ 시료/주문 컨트롤러 (`controller/sample_,order_` — 재고부족시 재고 즉시 0 차감 포함) + 단위테스트
5. ⬜ 생산 컨트롤러 (`controller/production_` — FIFO tick 시뮬레이션) + 단위테스트
6. ⬜ 모니터링 서비스 (`monitor/`) + 단위테스트
7. ⬜ 콘솔 뷰 + 진입점 (`view/`, `main.py`) + 수동 시나리오 검증
8. ⬜ 종단 시나리오 테스트 + `/verify` 스킬 1차 호출
9. ⬜ CLAUDE.md 최종화(전체 구현 반영) + README.md

각 커밋 전 `pytest -v` 통과를 확인한다. push는 매번 사용자 확인 후 진행 (기존 4개 저장소와 동일 패턴).

## Harness

- `pytest`(단위/종단 테스트) + `pytest-cov`(커버리지, `pyproject.toml`의 `[tool.coverage.*]` 설정 참고)
- 프로젝트 전용 verify 스킬은 새로 작성하지 않고, 전역 `/verify` 스킬을 이 저장소에서 처음 호출할 때
  자동으로 부트스트랩되는 프로젝트 전용 스킬을 활용한다 (pytest 실행 + `main.py` 스모크 실행). 8번 태스크
  전후, 그리고 마지막에 한 번씩 호출 예정.

## 실행 / 검증 방법 (구현 완료 후)

```bash
python main.py             # 콘솔 앱 실행 (아직 미구현)
python -m pytest -v         # 단위/종단 테스트
python -m pytest --cov      # 커버리지 리포트
```

Windows 콘솔 codepage(CP949) 한글 깨짐 이슈는 다른 저장소와 동일하게 `main.py`의
`sys.stdout/stdin.reconfigure(encoding="utf-8")`로 처리할 예정이다.
