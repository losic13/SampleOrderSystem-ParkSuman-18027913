# SampleOrderSystem

가상 반도체 회사 "S-Semi"의 반도체 시료 생산주문관리 시스템. 콘솔 기반으로 시료 등록, 주문 접수/승인,
재고 부족 시 생산라인(FIFO 큐 + 수동 tick 시뮬레이션)을 거친 생산, 모니터링, 출고까지 전체 흐름을
처리한다.

4개 PoC 저장소(ConsoleMVC/DataPersistence/DataMonitor/DummyDataGenerator)에서 검증한 설계를 계승해
새로 작성한 최종 통합 시스템이다. 배경, 설계 결정과 그 근거는 `CLAUDE.md`, 기능/데이터 명세는
`PRD.md`를 참고한다.

## 실행

```bash
python main.py
```

Windows 콘솔에서 한글이 깨져 보이면 `PYTHONUTF8=1 python main.py`처럼 환경변수를 붙여 실행한다
(코드 문제가 아니라 터미널 codepage 이슈).

메뉴 구성: `[1]시료관리 [2]시료주문 [3]주문승인/거절 [4]모니터링 [5]생산라인조회(+[T]시간경과)
[6]출고처리 [0]종료`

## 테스트

```bash
python -m pytest -v     # 단위/종단 테스트
python -m pytest --cov  # 커버리지 리포트
```

`pytest-cov`가 없다면 먼저 설치한다: `pip install -r requirements-dev.txt`

## 아키텍처

```
view → controller → repository, monitor → model
```

- `model/`: 순수 데이터 클래스(`Sample`, `Order`, `OrderStatus`, `ProductionJob`)
- `repository/`: JSON 파일 기반 영속성 (ABC 인터페이스 + 구현체 페어링)
- `controller/`: 비즈니스 로직 (`SampleController`, `OrderController`, `ProductionController`)
- `monitor/`: 조회 전용 집계 (`MonitorService`)
- `view/`, `main.py`: 콘솔 UI + 의존성 조립

핵심 설계 결정(재고 예약 모델, 생산라인 tick 시뮬레이션 등)의 배경은 `CLAUDE.md`를 참고한다.

## 개발 과정

이 저장소는 태스크 단위 Red-Green-Review 커밋 규율로 개발됐다. 각 태스크의 계획 문서는
`docs/plans/0N-xxx-plan.md`, 진행 현황 스냅샷은 `docs/plans/TASKS.md`에 있다.
