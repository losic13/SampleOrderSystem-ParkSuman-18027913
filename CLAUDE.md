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
제품 요구사항 상세는 `PRD.md`, 코딩 컨벤션(재사용 가능한 코드 스니펫)은 `CONVENTIONS.md` 참고.

### 과제 진행 유의사항 (PDF 3페이지, 중요 — 절대 위반하지 말 것)

- 안내된 모델만 사용: **Sonnet, Effort: Medium**. Opus 사용 이력이 있거나 모델 사용 이력이 없으면 부정행위로 간주됨
- 과제 종료 시 Claude Code에서 `/logout` 실행 필요 (이건 사람이 직접 해야 하는 행위이므로 에이전트가 대신할 수 없음 — 사용자에게 상기시킬 것)

### 참고: 형제 저장소 절대 경로 및 git 상태

로컬에 이미 clone/init되어 있으며 각각 완료 상태다. 코드를 import하지는 않지만, 설계를 다시 확인하고
싶을 때 아래 경로에서 직접 읽으면 된다 (재조사용 Explore 에이전트를 새로 띄울 필요 없음 — 이미 한 번
전수조사했고 결과는 이 문서와 `CONVENTIONS.md`에 반영돼 있음).

- `C:\reviewer\work\project\ConsoleMVC` — https://github.com/losic13/ConsoleMVC-ParkSuman-18027913
- `C:\reviewer\work\project\DataPersistence` — https://github.com/losic13/DataPersistence-ParkSuman-18027913
- `C:\reviewer\work\project\DataMonitor` — https://github.com/losic13/DataMonitor-ParkSuman-18027913
- `C:\reviewer\work\project\DummyDataGenerator` — https://github.com/losic13/DummyDataGenerator-ParkSuman-18027913
- 이 저장소(`SampleOrderSystem`)의 origin: https://github.com/losic13/SampleOrderSystem-ParkSuman-18027913
  (이미 `git remote add`로 연결되어 있었음 — 새로 만들 필요 없음). 기본 브랜치는 `master`.

## 이번 저장소를 향한 사용자의 명시적 요구사항

- unit test + clean code 관점을 엄격히 지킬 것
- `PRD.md`, `CLAUDE.md` 등 문서 관리
- Harness 도입: **pytest + coverage + 프로젝트 전용 `/verify` 스킬** (CI, pre-commit은 범위 밖으로 합의됨)
- 태스크 단위로 자주 커밋 (아래 "커밋 계획" 참고), 매 태스크 완료 시 검토 요청받고 진행

**진행 방식(중요)**: 이번 저장소는 계획 전체를 한 번에 실행하지 않고, **각 태스크(커밋) 단위로 사용자에게
검토를 요청한 뒤 다음 단계로 진행**하기로 합의했다. 도메인 코드를 작성하기 전에, "unit test + clean
code를 엄격히 지킨다"는 요구사항을 프로세스로 강제하기 위해 **개발 하네스(Red-Green-Review 커밋 규율 +
`architecture-guardian` 프로젝트 스킬)를 먼저 구축**하기로 했다 (아래 "Harness" 섹션 참고). 현재는
문서/스캐폴딩(1번)과 하네스 구축(2번)까지 완료된 상태이며, 사용자 검토 후 다음 태스크(모델 계층,
Red-Green-Review 사이클 시작)로 진행할 예정이다.

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

단위테스트가 실제로 작성되는 태스크(3~7, 9번)는 **Red-Green-Review 3커밋**으로 세분화한다
(아래 "Harness" 섹션 참고). 콘솔 I/O 배선(7번)과 문서 작업(9번)은 테스트로 검증하기 어렵거나
코드가 아니므로 기존처럼 1커밋을 유지한다.

1. ✅ **문서/스캐폴딩** — `.gitignore`, `pyproject.toml`(pytest+coverage), `requirements-dev.txt`, `PRD.md`, `CLAUDE.md`
2. ✅ **개발 하네스 구축** — `architecture-guardian` 프로젝트 스킬, Red-Green-Review 커밋 규율 확정 (이 커밋)
3. ⬜ 도메인 모델 (`model/`)
   - 3a. RED (실패하는 단위테스트 작성)
   - 3b. GREEN (테스트를 통과시키는 최소 구현)
   - 3c. REVIEW (`architecture-guardian` + `code-review`/`simplify` 검토 반영 리팩터링 — 변경 없으면 생략 가능)
4. ⬜ JSON 저장소 계층 (`repository/` — sample/order/production job) — RED/GREEN/REVIEW
5. ⬜ 시료/주문 컨트롤러 (`controller/sample_,order_` — 재고부족시 재고 즉시 0 차감 포함) — RED/GREEN/REVIEW
6. ⬜ 생산 컨트롤러 (`controller/production_` — FIFO tick 시뮬레이션) — RED/GREEN/REVIEW
7. ⬜ 모니터링 서비스 (`monitor/`) — RED/GREEN/REVIEW
8. ⬜ 콘솔 뷰 + 진입점 (`view/`, `main.py`) + 수동 시나리오 검증 (1커밋)
9. ⬜ 종단 시나리오 테스트 — RED/GREEN/REVIEW + `/verify` 스킬 1차 호출
10. ⬜ CLAUDE.md 최종화(전체 구현 반영) + README.md (1커밋)

각 커밋 전 `pytest -v` 통과를 확인한다 (RED 커밋은 예외 — 의도적으로 실패하는 테스트를 커밋).
push는 매번 사용자 확인 후 진행 (기존 4개 저장소와 동일 패턴).

단위테스트가 딸린 태스크(3~7, 9번)는 RED 커밋 전에 `docs/plans/0N-xxx-plan.md` 형태로 코드
작성 계획을 먼저 문서화하고 별도 커밋으로 남긴다 (harness engineering으로 개발 과정을 통제하는
흐름을 git history에서 그대로 확인할 수 있도록 하기 위함 — 예: `docs/plans/03-domain-model-plan.md`).

## Harness

- `pytest`(단위/종단 테스트) + `pytest-cov`(커버리지, `pyproject.toml`의 `[tool.coverage.*]` 설정 참고)
- 프로젝트 전용 `verify` 스킬을 자동 부트스트랩에 맡기지 않고, 저장소 안에 직접 구체화해서 작성해
  두었다 (`.claude/skills/verify/SKILL.md`) — pytest 실행(RED/GREEN 단계별 기대 결과 구분),
  커버리지, `main.py` 스모크 실행(입력 파이프 예시 포함), 데이터 파일 오염 확인까지 체크리스트로
  명시. GREEN 커밋 직전/REVIEW 커밋 직후/`main.py` 구현 시점/종단테스트(9번) 전후에 호출한다.

### 코드 품질 검토 스킬 (신규 1개 + 기존 2개 재사용)

시행착오 끝에 신규 스킬은 **`architecture-guardian` 1개만** 만들기로 했다. clean code 검토와
OCP 등 원칙 검토를 별도 스킬로 나누는 안도 검토했으나, 전역 `code-review`(버그+재사용/단순화/효율성)와
`simplify`(재사용/단순화/효율/altitude)가 이미 clean code 관점을 상당 부분 커버하므로 중복 스킬을
또 만들 필요가 없다고 판단했다. 이 저장소에서 기존 전역 스킬이 다루지 못하는 진짜 프로젝트 고유의
관심사(OCP/SOLID + MVC 레이어링 + 재고 예약 모델 불변식)만 신규 스킬로 좁혔다.

- **`architecture-guardian`** (신규, 저장소 내 `.claude/skills/architecture-guardian/SKILL.md`):
  레이어 의존 방향(`view → controller → repository/monitor → model`), repository ABC+구현체
  페어링, `ProductionController`/`OrderController` 단방향 의존(OCP), 재고 예약 모델 불변식을
  검토한다. Red-Green-Review의 REVIEW 단계에서 사용.
- **`code-review`/`simplify`** (기존 전역 스킬 재사용): 버그, 재사용/중복, 효율성, 단순화 관점은
  이 두 스킬로 커버하고 별도 스킬을 만들지 않는다.

"요구사항대로 개발하는 역할"과 "계획대로 진행되는지 체크하는 역할"도 별도 스킬로 만들지 않기로 했다:
전자는 Red-Green-Review의 Green 단계를 수행하는 메인 에이전트의 기본 역할이고, 후자는 네이티브
`TaskCreate`/`TaskUpdate`로 태스크를 추적하면서 위 "커밋 계획" 체크리스트와 대조하는 것으로 충분하다.
새 스킬을 계속 늘리는 것 자체가 이 프로젝트가 지향하는 "불필요한 추상화 금지" clean code 원칙에
어긋나기 때문이다.

### Red-Green-Review 사이클

단위테스트가 실제로 작성되는 태스크(위 "커밋 계획"의 3~7, 9번)에 한해 3커밋 규율을 적용한다.
콘솔 뷰/진입점(8번, I/O 배선이라 테스트 검증이 어려움)과 문서 최종화(10번, 코드가 아님)는 적용하지
않고 기존처럼 1커밋으로 처리한다.

1. **RED**: 실패하는 단위테스트를 먼저 작성하고 커밋한다 (`pytest -v`가 실패하는 상태 그대로 커밋 —
   테스트가 의도대로 실패하는지 확인 후 커밋).
2. **GREEN**: 테스트를 통과시키는 최소 구현을 작성하고 커밋한다 (`pytest -v` 통과 확인 후 커밋).
3. **REVIEW**: `architecture-guardian` + `code-review`/`simplify` 스킬로 검토받고, 지적된 사항을
   반영한 리팩터링을 커밋한다 (지적 사항이 없으면 이 커밋은 생략 가능 — 빈 커밋을 만들지 않는다).

## 실행 / 검증 방법 (구현 완료 후)

```bash
python main.py             # 콘솔 앱 실행 (아직 미구현)
python -m pytest -v         # 단위/종단 테스트
python -m pytest --cov      # 커버리지 리포트
```

Windows 콘솔 codepage(CP949) 한글 깨짐 이슈는 다른 저장소와 동일하게 `main.py`의
`sys.stdout/stdin.reconfigure(encoding="utf-8")`로 처리할 예정이다. Bash 도구로 직접 실행해 검증할 때는
`PYTHONUTF8=1 python main.py` / `PYTHONUTF8=1 python -m pytest -v`처럼 환경변수를 붙여야 출력이 안
깨진다 (코드 문제 아님, ConsoleMVC 작업 때 확인된 터미널 표시 이슈).

## 개발 환경 메모

- Windows 11, Python 3.14.6/3.14.4 (둘 다 PATH에 있음, `python`/`python3` 확인해서 일관되게 사용)
- `pytest` 9.1.1이 전역에 이미 설치되어 있어 별도 venv 없이 바로 `pytest` 실행 가능 (4개 PoC에서도 그렇게 진행함).
  `pytest-cov`는 이 저장소에서 처음 쓰므로 실행 전 설치 여부 확인 필요 (`pip show pytest-cov`, 없으면 `pip install -r requirements-dev.txt`)
- 이 저장소는 아직 `model/`/`repository/`/`controller/`/`monitor/`/`view/`/`main.py`/`tests/`가 전혀 없다
  (문서/스캐폴딩만 커밋 1개). `CONVENTIONS.md`의 코드 스니펫을 그대로 재사용해 작성 시작하면 된다.
