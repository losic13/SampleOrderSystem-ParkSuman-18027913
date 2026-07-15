# CONVENTIONS.md

이전 4개 저장소(ConsoleMVC/DataPersistence/DataMonitor/DummyDataGenerator)에서 일관되게 지켜진
코딩 컨벤션을 정리한 참고 문서다. 이 저장소에서도 그대로 따른다. (Explore 조사로 확인 완료 —
다시 조사할 필요 없음)

## 네이밍 / 스타일

- 함수·변수: `snake_case`, 클래스: `PascalCase`, 파일명은 클래스명의 snake_case (예: `sample_repository.py` → `SampleRepository`)
- 내부 전용 헬퍼/속성은 `_` 접두사 (`_json_store`, `_read_all`, `_classify`, `_to_dict`/`_from_dict`, `_generate_order_id`)
- 타입힌트: `Optional[X]` (`typing`에서 import, `X | None` 금지), 컬럼/리스트는 PEP 585 빌트인 제네릭
  `list[X]`, `dict[K, V]` 사용 (`List`/`Dict` import 안 함). void 메서드는 항상 `-> None` 명시
- 독스트링: 거의 안 씀. 클래스/인터페이스에 "왜"가 비자명할 때만 한 줄~두 줄 추가
  (예: ABC 인터페이스가 다른 저장소에서 교체 가능하도록 설계됐다는 설명). 평범한 메서드·dataclass에는 안 씀
- 인라인 `#` 주석: 코드가 무엇을 하는지 재설명하지 않고, 숨은 제약/이유만 남김
  (예: `MONITORED_STATUSES`가 REJECTED를 왜 빼는지, 랜덤 상태 배정이 실제 흐름을 안 따르는 이유)

## ABC 인터페이스 + 구현체 페어링

인터페이스와 구현체를 **같은 파일**에 둔다. 추상 메서드는 한 줄 `...` 바디.

```python
class SampleRepository(ABC):
    @abstractmethod
    def add(self, sample: Sample) -> None: ...

    @abstractmethod
    def get_by_id(self, sample_id: str) -> Optional[Sample]: ...

    @abstractmethod
    def get_all(self) -> list[Sample]: ...

    @abstractmethod
    def search_by_name(self, keyword: str) -> list[Sample]: ...

    @abstractmethod
    def update(self, sample: Sample) -> None: ...

    @abstractmethod
    def delete(self, sample_id: str) -> None: ...


class JsonSampleRepository(SampleRepository):
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        _json_store.ensure_file(self._file_path)
    # ... add/get_by_id/get_all/search_by_name/update/delete 구현
```

`OrderRepository`도 동일한 형태이되 `search_by_name` 대신 `get_by_status(status: OrderStatus) -> list[Order]`.

## `_json_store.py` (읽기+쓰기가 필요한 저장소 공통 헬퍼)

```python
import json
from pathlib import Path


def ensure_file(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        write_json(file_path, {})


def read_json(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(file_path: Path, data: dict) -> None:
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

dict의 키는 항상 엔티티의 ID(`sample_id`/`order_id`)이며, Python dict가 삽입 순서를 보존하므로
**FIFO 순서 = JSON 파일 내 저장 순서**로 자연스럽게 보장된다 (`production_job_repository.py`의
큐 순서도 동일 원리로 보장).

## 모델 직렬화 규칙

- `Enum` → `.value` (문자열)로 저장, 읽을 때 `OrderStatus(data["status"])`로 복원
- `datetime` → `.isoformat()`으로 저장, 읽을 때 `datetime.fromisoformat(...)`로 복원

## 주문 ID 생성 (ConsoleMVC의 `OrderController` 계승, 이 저장소에서 채택한 포맷)

```python
import uuid
from datetime import datetime

@staticmethod
def _generate_order_id() -> str:
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
```

## Windows UTF-8 콘솔 (모든 `main.py`의 첫 동작)

```python
import sys

def _use_utf8_console() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
```

`main()` 맨 처음에 호출한다. (참고: bash로 직접 실행해 검증할 때는 `PYTHONUTF8=1 python main.py`처럼
환경변수를 함께 주지 않으면 Git Bash 콘솔 codepage(CP949) 때문에 한글이 깨져 보일 수 있다 — 코드 문제가
아니라 터미널 표시 문제였다는 점을 ConsoleMVC 작업 때 확인함.)

## `pyproject.toml` (pytest 설정, 모든 저장소 공통)

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

이 저장소는 여기에 coverage 설정을 추가했다 (`[tool.coverage.run]`, `[tool.coverage.report]` — 실제
내용은 `pyproject.toml` 참고).

## `tests/conftest.py` 픽스처 스타일

```python
import pytest

from repository.sample_repository import JsonSampleRepository
# ...

@pytest.fixture
def sample_repo(tmp_path):
    return JsonSampleRepository(tmp_path / "samples.json")
```

- 파일 기반 저장소 테스트는 `tmp_path` 사용 (실제 파일 I/O를 타되 테스트마다 격리됨)
- 컨트롤러 픽스처는 저장소 픽스처를 인자로 받아 조립 (ConsoleMVC 패턴)
- 재현성이 필요한 곳(랜덤 생성 등)은 `autouse` 픽스처로 `random.seed(0)` 고정 (DummyDataGenerator 패턴 — 이 저장소는 랜덤 생성기가 없으므로 해당 없음)

## 테스트 명명

`test_<동작>_<기대결과>` 형태의 서술형 함수명 (예: `test_approve_order_with_insufficient_stock_moves_to_producing_without_deducting_stock`). 한글 docstring 대신 함수명 자체로 시나리오를 설명한다.
