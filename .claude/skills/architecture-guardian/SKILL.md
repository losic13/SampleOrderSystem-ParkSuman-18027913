---
name: architecture-guardian
description: >
  이 저장소(SampleOrderSystem)의 Red-Green-Review 사이클 중 REVIEW 단계에서, 또는
  model/repository/controller/monitor 계층 코드가 새로 작성되거나 변경됐을 때 사용한다.
  "OCP 지켜지나요", "레이어 구조 안 무너졌나요", "MVC 원칙 검토", "재고 예약 모델 불변식
  확인", "architecture review", "SOLID 위반 확인" 같은 요청에 반응한다. 버그 탐지나
  변수명/중복 코드 같은 일반적인 클린코드 정리는 이 스킬의 범위가 아니다 (전역 `code-review`,
  `simplify` 스킬을 사용할 것) — 이 스킬은 오직 **구조·의존 방향·SOLID 원칙·이 프로젝트
  고유의 설계 불변식**만 검토한다.
tools: Read, Glob, Grep, Bash
---

# architecture-guardian

## Overview

이 스킬은 SampleOrderSystem 저장소 전용이다. CLAUDE.md/PRD.md에 기록된 아키텍처 결정이
구현 과정에서 조금씩 무너지는 것을 막는 게 목적이다. 버그 탐지, 재사용/중복 제거, 효율성
개선은 전역 `code-review`/`simplify` 스킬의 영역이므로 이 스킬에서는 다루지 않는다. 이
스킬이 다루는 것은 오직 아래 네 가지뿐이다.

1. 레이어 의존 방향
2. Repository ABC + 구현체 페어링
3. Controller 간 단방향 의존 (OCP 관점 포함)
4. 재고 예약 모델 불변식

각 항목은 "왜 이 규칙이 존재하는지"를 알아야 오탐/누락을 줄일 수 있으므로, 아래 근거를
먼저 이해하고 코드를 읽는다.

## 이 저장소의 아키텍처 규칙

### 1. 레이어 의존 방향

```
view → controller → repository, monitor → model
```

- `model/`은 어떤 계층도 import하지 않는다 (순수 데이터 클래스 + Enum).
- `repository/`는 `model/`만 참조한다. `controller/`나 `view/`를 참조하면 위반.
- `controller/`는 `repository/`, `model/`, (production_controller의 경우) 다른
  controller를 참조할 수 있으나 `view/`를 참조하면 위반 (역방향 의존 — view가 controller를
  호출해야지 그 반대는 안 됨).
- `monitor/`는 `repository/`, `model/`만 참조한다. `controller/`를 참조하면 위반
  (모니터링은 조회 전용 집계이지, 주문/생산 로직에 개입하지 않는다).

**점검 방법**: 각 계층 디렉터리의 import 문을 grep해서 위 방향을 거스르는 import가
있는지 확인한다.

```
grep -rn "^from \|^import " model/       # repository/controller/view/monitor import 있으면 위반
grep -rn "^from \|^import " repository/  # controller/view import 있으면 위반
grep -rn "^from \|^import " monitor/     # controller/view import 있으면 위반
grep -rn "from view\|import view" controller/  # 있으면 위반
```

### 2. Repository ABC + 구현체 페어링

CONVENTIONS.md 규칙: `SampleRepository(ABC)`와 `JsonSampleRepository` 같은 **한 파일**에
정의한다. 인터페이스와 구현체가 분리된 파일에 있거나, 구현체가 ABC를 상속하지 않고 그냥
duck-typing으로만 맞춰져 있으면 위반.

**점검 방법**: `repository/*.py` 각 파일을 열어 `class XxxRepository(ABC)`와
`class JsonXxxRepository(XxxRepository)`가 같은 파일에 있는지 확인.

### 3. Controller 간 단방향 의존 (OCP 포함)

- `ProductionController`는 `OrderController`를 알아서는 안 된다 (import도, 타입 힌트도
  없어야 함). 반대로 `OrderController`가 재고 부족 분기에서 `ProductionController.enqueue(...)`를
  호출하는 것(생성자 주입)은 허용된다.
- 이 규칙이 깨지면 두 컨트롤러가 서로를 참조하는 순환 의존이 생기고, 향후 생산라인 로직만
  독립적으로 교체/확장(OCP)하기 어려워진다.
- OCP 관점에서 추가로 확인할 것: `repository/`가 ABC 인터페이스에 의존해 주입되는지 (구현체
  JsonXxxRepository를 controller가 직접 `new` 하지 않고, 생성자 인자로 받는지). 이래야 향후
  JSON→DB 전환 시 controller 코드를 안 고쳐도 된다.

**점검 방법**: `controller/production_controller.py`에서 `order_controller`/`OrderController`
문자열을 grep — 매치되면 위반. `controller/order_controller.py` 생성자에서
`ProductionController`를 인자로 받는지(주입) 확인.

### 4. 재고 예약 모델 불변식 (가장 중요 — CLAUDE.md "핵심 설계 결정" 참고)

- 주문 승인 시 재고가 부족하면: `shortage = order.quantity - sample.stock` 계산 →
  **`sample.stock`을 즉시 0으로 차감** → `ProductionJob` 생성 후 큐 등록 → 주문 상태
  `PRODUCING`.
- 생산 완료 시(tick으로 `elapsed_minutes >= total_minutes` 도달): `sample.stock += job.shortage`
  → 주문 상태 `PRODUCING → CONFIRMED`.
- 이 두 지점 중 하나라도 빠지면 이중 소비 버그(같은 재고를 여러 주문이 동시에 승인받는 문제)가
  재발한다. 특히 "부족 분기에서 재고를 건드리지 않고 그냥 PRODUCING으로만 바꾸는" 예전 ConsoleMVC
  방식으로 되돌아가 있지 않은지 반드시 확인한다.

**점검 방법**: `controller/order_controller.py`의 승인 로직과
`controller/production_controller.py`의 tick 처리 로직을 직접 읽고, 위 두 단계가 정확히
구현돼 있는지 확인한다 (grep으로는 판정하기 어려운 항목 — 반드시 코드를 읽을 것).

## 위반 예시 (Before/After)

grep만으로는 놓치기 쉬운 패턴이므로, 아래 구체적인 코드 형태를 기준으로 판정한다.

### 1. 레이어 의존 방향 위반

```python
# ❌ model/sample.py — model이 repository를 알면 안 됨
from repository.sample_repository import JsonSampleRepository

# ✅ model/sample.py — dataclass만, 외부 계층 import 없음
from dataclasses import dataclass
```

### 2. ABC+구현체 페어링 위반

```python
# ❌ repository/sample_repository_interface.py 와
#    repository/json_sample_repository.py 로 파일이 분리됨

# ✅ repository/sample_repository.py 한 파일에 둘 다 정의
class SampleRepository(ABC): ...
class JsonSampleRepository(SampleRepository): ...
```

### 3. Controller 단방향 의존 위반

```python
# ❌ controller/production_controller.py
class ProductionController:
    def __init__(self, order_controller: "OrderController") -> None:  # 역방향 의존
        self._order_controller = order_controller

# ✅ controller/order_controller.py — 이 방향만 허용
class OrderController:
    def __init__(self, order_repo, sample_repo, production_controller: "ProductionController") -> None:
        self._production_controller = production_controller
```

### 4. 재고 예약 모델 불변식 위반 (가장 흔한 회귀 패턴 — ConsoleMVC 방식으로 되돌아간 경우)

```python
# ❌ 재고를 건드리지 않고 상태만 바꿈 — 이중 소비 버그 재발
if sample.stock < order.quantity:
    order.status = OrderStatus.PRODUCING
    self._production_controller.enqueue(order, sample)

# ✅ shortage 계산 후 즉시 0 차감, 생산 완료 시에만 shortage만큼 정산
if sample.stock < order.quantity:
    shortage = order.quantity - sample.stock
    sample.stock = 0
    self._sample_repo.update(sample)
    self._production_controller.enqueue(order, sample, shortage)
    order.status = OrderStatus.PRODUCING
```

## 체크리스트

| # | 항목 | Pass 기준 | Fail 시 |
|---|---|---|---|
| 1 | 레이어 의존 방향 | `model`이 어떤 계층도 import 안 함, `repository`/`monitor`가 `controller`/`view` import 안 함, `controller`가 `view` import 안 함 | 역방향 import 지점을 파일:라인으로 보고 |
| 2 | ABC+구현체 페어링 | 각 repository 파일에 ABC와 Json 구현체가 공존 | 분리돼 있거나 ABC 미상속인 파일 보고 |
| 3 | Controller 단방향 의존 | `ProductionController`가 `OrderController`를 모름, repository는 ABC 타입으로 주입받음 | 위반 지점과 왜 OCP를 해치는지 설명 |
| 4 | 재고 예약 불변식 | 승인 시 즉시 0 차감 + 큐 등록, 완료 시 shortage만큼 정산 | 어느 단계가 누락/오류인지 구체적으로 지적 |

## 출력 형식

각 위반 사항은 다음 형식으로 보고한다 (위반이 없으면 "위반 없음"만 짧게 보고하고 끝낸다 — 억지로
지적거리를 만들지 않는다):

```
[규칙 번호] file:line — 위반 내용 한 줄 요약
  왜: 이 규칙이 왜 존재하는지 (위 "이 저장소의 아키텍처 규칙" 근거 인용)
  제안: 구체적으로 어떻게 고치면 되는지 (Before/After 예시 형태)
```

## 사용 시점

Red-Green-Review 사이클의 **REVIEW 단계**에서 호출한다. 이 단계에서는 전역
`code-review`/`simplify`(버그·중복·효율성 관점)와 이 스킬(구조·원칙 관점)을 함께 사용하는
것을 권장하되, 순서는 상관없다. 발견한 위반 사항은 고치지 않고 보고만 한다 — 실제 리팩터링
반영과 커밋은 REVIEW 단계의 메인 작업으로 사용자와 함께 진행한다.
