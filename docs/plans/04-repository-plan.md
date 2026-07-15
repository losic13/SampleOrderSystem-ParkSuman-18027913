# 태스크 4 계획: JSON 저장소 계층 (`repository/`) — Red-Green-Review

## Context

`model/` 계층(태스크3)이 끝났다는 전제로 진행한다. `repository/`는 `_json_store.py` 공통 헬퍼
(CONVENTIONS.md에 확정된 코드)를 사용해 각 모델을 JSON 파일로 CRUD하는 계층이다.
ConsoleMVC/DataPersistence 두 저장소에서 완전히 동일했던 ABC+구현체 페어링 패턴을 그대로
계승한다. `ProductionJobRepository`만 이 저장소가 새로 설계한다 (형제 저장소에 대응물 없음).

레이어 규칙: repository는 `model`만 import하고, `controller`/`view`를 import하지 않는다
(architecture-guardian 검토 대상).

## 확정 설계

- `repository/_json_store.py` — CONVENTIONS.md 그대로 (`ensure_file`/`read_json`/`write_json`)
- `repository/sample_repository.py`
  - `SampleRepository(ABC)`: `add`, `get_by_id`, `get_all`, `search_by_name(keyword)`, `update`, `delete`
  - `JsonSampleRepository`: `_to_dict`/`_from_dict`로 직렬화 (Sample은 Enum/datetime 필드가 없어 단순 변환)
  - `search_by_name`: 대소문자 무시, 부분일치 (`keyword.lower() in sample.name.lower()`)
- `repository/order_repository.py`
  - `OrderRepository(ABC)`: `add`, `get_by_id`, `get_all`, `get_by_status(status: OrderStatus)`, `update`, `delete`
  - `JsonOrderRepository`: `status`는 `.value`로 저장/`OrderStatus(...)`로 복원, `created_at`은
    `.isoformat()`으로 저장/`datetime.fromisoformat(...)`으로 복원
- `repository/production_job_repository.py` (신규 설계)
  - `ProductionJobRepository(ABC)`: `add(job)`, `get_by_order_id(order_id)`, `get_all() -> list[ProductionJob]`
    (FIFO 순서 = JSON dict 삽입 순서, CONVENTIONS.md 원칙 그대로), `update(job)`, `delete(order_id)`
  - dict 키는 `order_id` (모델 자체에 job 고유 ID가 없고 주문 1건당 생산 작업 1건이므로 자연스러운 키)
  - `elapsed_minutes`/`enqueued_at`도 Order와 동일한 직렬화 규칙 적용

## Phase 세분화

### Phase 1 — RED

- 1.1 `tests/conftest.py`에 `tmp_path` 기반 픽스처 추가: `sample_repo`, `order_repo`, `production_job_repo`
- 1.2 `tests/test_sample_repository.py`
  - `test_add_and_get_by_id_returns_saved_sample`
  - `test_get_all_returns_every_saved_sample`
  - `test_search_by_name_matches_case_insensitively_and_partially`
  - `test_update_persists_changed_fields`
  - `test_delete_removes_sample`
  - `test_get_by_id_returns_none_when_not_found`
- 1.3 `tests/test_order_repository.py` — 위와 동일한 CRUD 세트 + `test_get_by_status_filters_by_status`,
  `test_add_persists_enum_and_datetime_fields_across_reload` (새 repository 인스턴스로 재로드해 직렬화 왕복 확인)
- 1.4 `tests/test_production_job_repository.py`
  - `test_add_and_get_by_order_id_returns_saved_job`
  - `test_get_all_preserves_fifo_insertion_order`
  - `test_update_persists_elapsed_minutes`
  - `test_delete_removes_job`
  - `test_add_persists_enqueued_at_datetime_across_reload` (새 repository 인스턴스로 재로드해
    `enqueued_at` 직렬화 왕복 확인 — order_repository의 동일 테스트와 대칭)
- `repository/` 파일이 없으므로 전부 `ModuleNotFoundError`로 실패하는 것 확인 후 **커밋 4a (RED)**

### Phase 2 — GREEN

- 2.1 `repository/_json_store.py`
- 2.2 `repository/sample_repository.py`
- 2.3 `repository/order_repository.py`
- 2.4 `repository/production_job_repository.py`
- `pytest -v` 전체 통과 확인 후 **커밋 4b (GREEN)**

### Phase 3 — REVIEW

- 3.1 `verify` 스킬로 pytest/커버리지 재확인 (`pyproject.toml` coverage source에 `repository` 포함 확인)
- 3.2 `architecture-guardian` — repository가 model만 import하는지, ABC+구현체 페어링이 컨벤션대로인지 검토
- 3.3 `code-review`/`simplify` — 세 저장소 간 중복 코드(직렬화 보일러플레이트 등) 지적 여부 확인
- 3.4 지적사항 반영 후 **커밋 4c (REVIEW)** (없으면 생략, 사유 보고)

## 검증

- Phase마다 `pytest -v` 실행 결과 확인 (RED는 실패 이유, GREEN/REVIEW는 통과 여부)
- `git log --oneline`으로 4a/4b/4c 커밋 확인, push는 사용자 확인 후 진행
