# 태스크 3 계획: 도메인 모델 (`model/`) — Red-Green-Review

> 코드 작성 전 합의된 계획을 기록한 문서. 이후 태스크(4~7, 9번)도 같은 컨벤션으로
> `docs/plans/0N-xxx-plan.md`를 작성한다.

## Context

하네스(Red-Green-Review 커밋 규율 + `architecture-guardian`/`verify` 프로젝트 스킬) 구축이
끝났고, 이제 실제 도메인 코드 작성을 시작한다. CLAUDE.md 커밋 계획의 3번 태스크로, `model/`
계층(`sample.py`, `order.py`, `order_status.py`, `production_job.py`)을 4개 PoC 저장소의
검증된 필드 설계를 계승해 작성한다. 단위테스트가 딸린 태스크이므로 RED → GREEN → REVIEW
3커밋 규율을 적용하며, 각 단계를 파일 단위 하위 Phase로 세분화한다.

`model/`은 레이어드 아키텍처의 최하단이라 다른 계층을 import하지 않는 순수 데이터 클래스로만
구성한다 (`architecture-guardian`의 "레이어 의존 방향" 규칙 1항과 직결). 값 검증(수량 1 미만
거부 등)은 PRD.md §5 "[2] 시료 주문" 명세상 컨트롤러 책임이므로 이 태스크에서는 모델에 검증
로직을 넣지 않는다 — model은 순수 데이터 보관 역할만 한다.

Explore 에이전트로 ConsoleMVC/DataPersistence의 `model/`을 직접 확인한 결과, `Sample`/
`Order`/`OrderStatus`는 두 저장소에서 완전히 동일한 코드였고, 검증/직렬화 로직이 전혀 없는
순수 dataclass/Enum이었다. 이 저장소도 그대로 계승한다.

**테스트 범위 결정**: 형제 저장소는 `Sample`/`Order`에 대한 전용 단위테스트 없이 repository
테스트로 간접 검증하는 방식이었지만, 이 저장소는 Red-Green-Review 프로세스를 일관되게
보여주기 위해 **4개 클래스 모두에 대해 전용 테스트를 작성**하기로 했다. `Sample`/`Order`/
`OrderStatus`는 필드 저장/기본값 확인 수준의 간단한 테스트, `ProductionJob`은
`is_complete`/`progress_ratio` 실제 로직까지 검증한다.

## 확정 코드 (ConsoleMVC/DataPersistence와 동일하게 계승)

```python
# model/order_status.py
from enum import Enum


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"
```

```python
# model/sample.py
from dataclasses import dataclass


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = 0
```

```python
# model/order.py
from dataclasses import dataclass, field
from datetime import datetime

from model.order_status import OrderStatus


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
    created_at: datetime = field(default_factory=datetime.now)
```

`model/production_job.py`는 이 저장소가 새로 만드는 것 (형제 저장소에 참고할 코드 없음,
CLAUDE.md/PRD.md §6·§7 명세대로 직접 설계):

```python
# model/production_job.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    shortage: int
    actual_quantity: int
    total_minutes: int
    elapsed_minutes: int = 0
    enqueued_at: datetime = field(default_factory=datetime.now)

    @property
    def is_complete(self) -> bool:
        return self.elapsed_minutes >= self.total_minutes

    @property
    def progress_ratio(self) -> float:
        if self.total_minutes == 0:
            return 1.0
        return min(self.elapsed_minutes / self.total_minutes, 1.0)
```

직렬화(Enum→`.value`, datetime→`.isoformat()`)는 model이 아니라 다음 태스크인 repository
계층 책임 (CONVENTIONS.md 그대로, DataPersistence의 `_to_dict`/`_from_dict` 패턴 계승).

## Phase 세분화

### Phase 1 — RED (실패하는 단위테스트 작성)

테스트 명명은 형제 저장소 컨벤션(`test_<동작>_<기대결과>`)을 그대로 따른다.

- 1.1 `tests/test_order_status.py`
  - `test_order_status_has_five_members_with_matching_string_values`
- 1.2 `tests/test_sample.py`
  - `test_sample_stores_all_fields`
  - `test_sample_stock_defaults_to_zero_when_omitted`
- 1.3 `tests/test_order.py`
  - `test_order_stores_all_fields`
  - `test_order_status_defaults_to_reserved`
  - `test_order_created_at_defaults_to_datetime_now`
- 1.4 `tests/test_production_job.py`
  - `test_production_job_stores_all_fields`
  - `test_is_complete_true_when_elapsed_reaches_total_minutes`
  - `test_is_complete_false_while_elapsed_below_total_minutes`
  - `test_progress_ratio_returns_elapsed_over_total`
  - `test_progress_ratio_capped_at_one_when_elapsed_exceeds_total`
- `model/` 파일이 아직 없으므로 `pytest -v` 실행 시 `ModuleNotFoundError`로 전부 실패하는 것을
  "의도한 실패"로 확인 후 **커밋 3a (RED)**

### Phase 2 — GREEN (최소 구현)

- 2.1 `model/order_status.py` — `class OrderStatus(Enum)`
- 2.2 `model/sample.py` — `@dataclass class Sample`
- 2.3 `model/order.py` — `@dataclass class Order` (`order_status.py` import)
- 2.4 `model/production_job.py` — `@dataclass class ProductionJob` + 프로퍼티 2개
- `pytest -v` 전체 통과 확인 후 **커밋 3b (GREEN)**

### Phase 3 — REVIEW

- 3.1 `verify` 스킬로 `pytest -v`/`--cov` 재확인 (커버리지 `source`에 `model` 포함돼 있음 —
  `pyproject.toml` 기존 설정)
- 3.2 `architecture-guardian` 스킬 호출 — 레이어 의존 방향(1항: model이 다른 계층을 import하지
  않는지) 검토
- 3.3 `code-review`/`simplify` 스킬 호출 — 클린코드/중복/네이밍 관점 검토
- 3.4 지적사항이 있으면 반영해 리팩터링 후 **커밋 3c (REVIEW)** (지적사항 없으면 생략 가능,
  생략 시 사유를 사용자에게 보고)

## 검증

- 각 Phase 종료 시 `pytest -v` 실행 결과를 확인한다 (RED는 실패 이유, GREEN/REVIEW는 통과 여부).
- 최종적으로 `git log --oneline`으로 3a/3b/3c(또는 3a/3b) 커밋이 의도대로 쌓였는지 확인.
- push는 사용자 확인 후 진행.
