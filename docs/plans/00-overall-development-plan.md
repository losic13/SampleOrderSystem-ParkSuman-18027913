# 전체 개발 계획: SampleOrderSystem

> PRD.md(요구사항 명세), CLAUDE.md(진행 맥락·설계 결정 이력)의 내용을 "무엇을 어떤 순서로
> 만드는가" 관점으로 정리한 로드맵 문서. 태스크별 상세 계획은 `docs/plans/0N-xxx-plan.md`에
> 개별 작성한다 (이 문서는 그 목차 역할도 겸함).

## 1. 목표

4개 PoC 저장소(ConsoleMVC/DataPersistence/DataMonitor/DummyDataGenerator)에서 검증한 설계를
계승해, 반도체 시료 생산주문관리 시스템을 하나의 콘솔 애플리케이션으로 통합 구현한다. 코드는
복사하지 않고 설계만 새로 옮겨 적는다 (독립 저장소 요구사항).

## 2. 아키텍처 개요

```
view (콘솔 UI)
  ↓
controller (비즈니스 로직: SampleController / OrderController / ProductionController)
  ↓
repository (JSON 영속성) ──┐
monitor (조회 전용 집계)  ──┤→ model (순수 데이터: Sample / Order / OrderStatus / ProductionJob)
```

- 의존 방향은 항상 위→아래 한 방향 (`view → controller → repository/monitor → model`).
- `OrderController → ProductionController` 단방향 의존만 허용 (재고 부족 시 생산 큐에 enqueue
  요청). `ProductionController`는 `OrderController`를 모른다 (OCP).
- `model`은 다른 계층을 import하지 않는 순수 dataclass/Enum.
- repository는 ABC 인터페이스 + JSON 구현체를 같은 파일에 페어링 (`_json_store.py` 공통 헬퍼 사용).

## 3. 핵심 설계 결정 (되돌리지 말 것)

| 결정 | 이유 |
|---|---|
| 주문 ID = `ORD-{YYYYMMDD}-{hex4}` | 실제 승인/거절 로직을 갖고 있던 ConsoleMVC 포맷으로 통일 (형제 저장소 간 불일치 해소) |
| 시료 ID는 사용자가 직접 입력 | ConsoleMVC/DataPersistence 방식 계승, 자동 생성(DummyDataGenerator류)은 범위 밖 |
| **재고 예약 모델**: `PRODUCING` 전환 시 `sample.stock`을 즉시 0으로 차감, 생산 완료 시 `shortage`만큼 복원 후 `CONFIRMED` 전환 | ConsoleMVC의 단순 모델을 그대로 가져오면 잔여 재고가 "가용"으로 남아 이중 소비 버그 발생. 상세 근거는 CLAUDE.md 참고 |
| 모니터링 부족 판정은 `RESERVED` 주문 수량 합만 미해결 수요로 계산 (`PRODUCING` 제외) | 위 재고 예약 모델과 정합성 유지 (DataMonitor 원래 공식에서 조정) |
| 생산라인 시간 진행은 수동 tick (wall-clock 아님) | 결정적(deterministic) unit test, flaky 회피 |

## 4. 데이터 흐름 요약

```
RESERVED --(승인, 재고충분)--> CONFIRMED --(출고)--> RELEASE
RESERVED --(승인, 재고부족)--> PRODUCING --(생산완료: tick으로 elapsed>=total)--> CONFIRMED --(출고)--> RELEASE
RESERVED --(거절)--> REJECTED
```

실생산량 = `ceil(부족분 / 수율)`, 총 생산시간 = `평균생산시간 × 실생산량` (PRD.md §7).

## 5. 태스크 / 커밋 로드맵

단위테스트가 실제로 작성되는 태스크(3~7, 9번)는 Red-Green-Review 3커밋으로 세분화하고, RED
커밋 전 `docs/plans/0N-xxx-plan.md`를 먼저 작성해 별도 커밋으로 남긴다. 뷰/진입점(8번)과
문서 최종화(10번)는 코드 검증이 어렵거나 코드가 아니므로 1커밋으로 처리한다.

| # | 태스크 | 산출물 | 커밋 방식 | 상태 |
|---|---|---|---|---|
| 1 | 문서/스캐폴딩 | `.gitignore`, `pyproject.toml`, `requirements-dev.txt`, `PRD.md`, `CLAUDE.md` | 1커밋 | ✅ |
| 2 | 개발 하네스 구축 | `architecture-guardian`/`verify` 프로젝트 스킬, Red-Green-Review 규율 확정 | 1커밋 | ✅ |
| 3 | 도메인 모델 (`model/`) | `sample.py`/`order.py`/`order_status.py`/`production_job.py` | plan → RED → GREEN → REVIEW | ⬜ 계획 문서 완료(`03-domain-model-plan.md`), 코드 착수 전 |
| 4 | JSON 저장소 계층 (`repository/`) | sample/order/production_job repository (ABC+Json 페어링) | plan → RED → GREEN → REVIEW | ⬜ |
| 5 | 시료/주문 컨트롤러 (`controller/sample_,order_`) | 등록/조회/검색, 주문 접수, 승인(재고 예약 모델)/거절 | plan → RED → GREEN → REVIEW | ⬜ |
| 6 | 생산 컨트롤러 (`controller/production_`) | FIFO 큐 enqueue/list_queue/current_job/advance_time | plan → RED → GREEN → REVIEW | ⬜ |
| 7 | 모니터링 서비스 (`monitor/`) | 상태별 주문량, 재고 상태(여유/부족/고갈) | plan → RED → GREEN → REVIEW | ⬜ |
| 8 | 콘솔 뷰 + 진입점 (`view/`, `main.py`) | 메뉴 [1]~[6]+[T]+[0], 의존성 조립, UTF-8 콘솔 설정 | 1커밋 + 수동 시나리오 검증 | ⬜ |
| 9 | 종단 시나리오 테스트 | 주문 접수→승인(재고부족)→tick→생산완료→출고 전 과정 통합 테스트 | plan → RED → GREEN → REVIEW + `/verify` 1차 호출 | ⬜ |
| 10 | 문서 최종화 | CLAUDE.md 전체 구현 반영, README.md 작성 | 1커밋 | ⬜ |

## 6. 품질 하네스

- **테스트**: `pytest` (계층별 단위테스트 + 종단 시나리오 테스트 1개), `pytest-cov`로 커버리지 측정
- **검증**: 프로젝트 전용 `/verify` 스킬 — pytest 실행(RED/GREEN 기대 결과 구분), 커버리지, `main.py`
  스모크 실행, 데이터 파일 오염 확인. GREEN 직전/REVIEW 직후/`main.py` 구현 시점/종단테스트 전후 호출
- **구조 검토**: `architecture-guardian` 스킬 — 레이어 의존 방향, repository ABC+구현체 페어링,
  컨트롤러 단방향 의존(OCP), 재고 예약 모델 불변식. REVIEW 단계에서 사용
- **일반 코드 품질**: 전역 `code-review`(버그/재사용/효율성)·`simplify`(단순화) 스킬 재사용,
  프로젝트 전용 스킬을 별도로 늘리지 않음
- CI/pre-commit은 이번 과제 범위 밖으로 합의됨

## 7. 진행 방식

계획 전체를 한 번에 실행하지 않고, **각 태스크(커밋) 단위로 사용자 검토 요청 → 승인 후 다음
단계 진행**. push는 매 커밋 후 사용자 확인을 거쳐 진행한다 (기존 4개 PoC 저장소와 동일 패턴).

## 8. 관련 문서

- `PRD.md` — 기능/데이터 명세 (요구사항 원본)
- `CLAUDE.md` — 진행 맥락, 설계 결정과 그 근거, 저장소 간 관계
- `CONVENTIONS.md` — 코드 스니펫 수준의 재사용 컨벤션
- `docs/plans/0N-xxx-plan.md` — 태스크별 Red-Green-Review 상세 계획 (현재 `03-domain-model-plan.md`만 존재)
