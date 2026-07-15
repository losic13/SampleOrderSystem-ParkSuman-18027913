---
name: verify
description: >
  이 저장소(SampleOrderSystem)에서 코드 변경 후 실제로 동작하는지 실행 검증할 때 사용한다.
  "테스트 돌려줘", "커버리지 확인", "verify", "GREEN 커밋 전에 검증", "main.py 스모크 테스트",
  "종단 시나리오 확인" 같은 요청에 반응한다. 전역 `verify` 스킬이 이 저장소에서 자동
  부트스트랩하려는 프로젝트 전용 스킬을 미리 구체화해 둔 것 — 구조/원칙 검토는 이 스킬의
  범위가 아니다 (`architecture-guardian`, `code-review`, `simplify` 사용).
tools: Bash, Read, Glob, Grep
---

# verify (SampleOrderSystem 전용)

## Overview

이 스킬은 **코드가 실제로 동작하는지 실행해서 확인**하는 것이 목적이다. 정적 검토(구조,
원칙, 클린코드)는 `architecture-guardian`/`code-review`/`simplify`의 영역이므로 여기서는
다루지 않는다. Red-Green-Review 사이클에서 GREEN 커밋 직전, REVIEW 커밋 직후, 그리고
`main.py`가 만들어진 뒤의 수동 시나리오 검증에 사용한다.

## 실행 환경 주의사항

- Windows Git Bash에서 직접 실행할 때는 CP949 콘솔 codepage 때문에 한글 출력이 깨질 수 있다
  (코드 문제 아님 — ConsoleMVC 작업 때 확인된 터미널 표시 이슈). 반드시 `PYTHONUTF8=1`
  환경변수를 붙여서 실행한다.
- `pytest-cov`는 이 저장소에서 처음 쓰는 의존성이므로, 최초 실행 전 `pip show pytest-cov`로
  설치 여부를 확인하고 없으면 `pip install -r requirements-dev.txt`를 먼저 실행한다.

## 검증 절차

### 1. 단위/종단 테스트

```bash
PYTHONUTF8=1 python -m pytest -v
```

- **RED 커밋 검증**: 지금 막 작성한 테스트가 **의도한 이유로 실패**하는지 확인하는 것이 목적이다
  (전체 초록을 기대하지 않음 — `AssertionError`/`AttributeError` 등 의도한 실패 유형인지, 무관한
  이유(import 에러, 오타)로 실패하는 건 아닌지 확인).
- **GREEN/REVIEW 커밋 검증**: 전체 테스트가 통과해야 한다. 하나라도 실패하면 커밋하지 않는다.

### 2. 커버리지

```bash
PYTHONUTF8=1 python -m pytest --cov
```

`pyproject.toml`의 `[tool.coverage.run] source = ["model", "repository", "controller", "monitor", "view"]`
범위에서 새로 추가한 코드가 커버되고 있는지 `show_missing` 출력으로 확인한다.

### 3. 콘솔 앱 스모크 (view/main.py 구현 이후부터 적용)

`main.py`가 구현되기 전까지는 이 단계를 건너뛴다. 구현된 이후에는 실제 메뉴 흐름을 최소 1개
직접 실행해본다 (예: 시료 등록 → 주문 접수 → 승인(재고부족 분기 유도) → `[T]` 시간 경과로
생산 완료시키기 → 출고 처리). 입력 시퀀스를 미리 만들어 파이프로 흘려보낸다:

```bash
printf '1\n...\n0\n' | PYTHONUTF8=1 python main.py
```

메뉴 번호/입력 순서는 그 시점의 `view/console_view.py` 메뉴 구성에 맞춰 작성한다 (PRD.md §5
메뉴 명세 참고: `[1]시료관리 [2]시료주문 [3]주문승인/거절 [4]모니터링 [5]생산라인조회(+[T]시간경과)
[6]출고처리 [0]종료`).

### 4. 데이터 파일 오염 확인

`data/`는 `.gitignore` 대상이다. 스모크 실행 후 `git status`로 `data/*.json`이 스테이징되거나
저장소에 실수로 포함되지 않았는지 확인한다.

## 체크리스트

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 단위테스트 (RED) | `PYTHONUTF8=1 python -m pytest -v` | 새 테스트가 의도한 이유로 실패 |
| 단위테스트 (GREEN/REVIEW) | `PYTHONUTF8=1 python -m pytest -v` | 전체 통과 |
| 커버리지 | `PYTHONUTF8=1 python -m pytest --cov` | 새 코드 라인이 미커버로 남지 않음 |
| 콘솔 스모크 (7번 태스크 이후) | `printf ... \| PYTHONUTF8=1 python main.py` | 메뉴 흐름 1개가 에러 없이 끝까지 진행 |
| 데이터 오염 | `git status` | `data/*.json`이 커밋 대상에 없음 |

## 호출 시점

- 각 **GREEN** 커밋 직전 (전체 테스트 통과 확인)
- 각 **REVIEW** 커밋 직후 (리팩터링이 테스트를 깨지 않았는지)
- `view/main.py` 구현 완료 시점 (콘솔 스모크 최초 실행)
- 종단 시나리오 테스트(9번 태스크) 전후, 그리고 최종 문서화(10번) 직전 한 번 더
