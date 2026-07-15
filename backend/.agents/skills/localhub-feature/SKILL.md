---
name: localhub-feature
description: Implement or modify LocalHub features using FastAPI, SQLAlchemy 2.x, SQLite, Pydantic v2, pytest, httpx, and the supplied Seoul TourAPI JSON data. Use when adding or changing LocalHub location APIs, anonymous post CRUD, source or user-created travel courses, crowd integrations, chatbot behavior, database models, schemas, services, routers, import logic, or tests. Do not use for deployment-only or submission-only checks.
---

# LocalHub 기능 구현

## 작업 순서

1. 백엔드의 `AGENTS.md`를 읽는다.
2. 기존 router, model, schema, service, test, `.env.example`을 확인한다.
3. 데이터 기능이면 저장소 루트의 `data/서울/SCHEMA.md`, `data/서울/SOURCE.md`, 관련 JSON 표본을 확인한다.
4. 수정 파일, API 변화, DB 변화, 테스트 항목, 예상 오류를 짧게 제시한다. 사용자가 즉시 구현을 요청했으면 이어서 구현한다.
5. 요청한 범위만 구현하고 관련 테스트를 작성한다.
6. 관련 pytest를 먼저 실행하고 전체 pytest를 실행한다. 실패 원인을 최소 범위로 수정해 다시 실행한다.
7. 변경 파일, API 사용법, 테스트 결과, 남은 제약을 보고한다.

현재 코드가 없거나 구조가 불완전하면 의뢰서의 필수 기능을 만족하는 가장 작은 구조를 만든다. 요청하지 않은 선택 기능을 함께 만들지 않는다.

## 공통 구현 규칙

- FastAPI router, service, SQLAlchemy model, Pydantic schema의 책임을 분리한다.
- SQLAlchemy 2.x 스타일과 Pydantic v2를 사용한다.
- SQLite만 사용하고 마이그레이션 도구를 새로 도입하지 않는다.
- ORM 객체를 무검증 상태로 그대로 응답하지 않는다.
- 페이지네이션 입력에 경계를 두고 안정적인 보조 정렬 키를 사용한다.
- 여러 쓰기가 하나의 작업이면 한 트랜잭션으로 처리하고 실패 시 rollback을 검증한다.
- 외부 비동기 API는 `httpx.AsyncClient`와 명시적 timeout을 사용한다.
- 비밀값은 환경변수에서 읽고 `.env.example`에는 이름과 설명만 기록한다.

## 서울 데이터 규칙

- 원본 JSON 파일을 수정하지 않는다. 데이터베이스 초기화 또는 import의 입력으로만 사용한다.
- 최상위 `items`를 읽고 `contentid`를 원본 식별자로 보존한다.
- `mapx`는 longitude, `mapy`는 latitude이다. 문자열 좌표를 검증한 뒤 숫자로 변환한다.
- 빈 주소, 전화번호, 좌표, 이미지 URL을 임의로 채우지 않는다.
- `firstimage`가 비어 있으면 이미지가 없는 것으로 처리한다.
- 콘텐츠 유형 ID `12`, `14`, `15`, `25`, `28`, `32`, `38`을 제공 파일과 일치시킨다.
- 현재 제공 파일은 6,518건이다. `SOURCE.md`에 적힌 음식점 1,632건 파일이 없으므로 음식점 데이터를 생성하거나 있다고 가정하지 않는다.
- 화면과 문서에 한국관광공사, TourAPI 4.0, 공공누리 제3유형 출처를 표시할 수 있도록 출처 정보를 보존한다.

## 기능별 규칙

### 장소

- 검색, 콘텐츠 유형 필터, 페이지네이션을 지원한다.
- 목록 응답은 필요한 필드만 반환하고 상세 응답과 구분한다.
- 잘못된 좌표는 import 전체를 중단할지 해당 값을 null로 둘지 기존 정책에 맞춰 명시적으로 처리한다.

### 익명 게시글

- 목록, 상세, 작성, 수정, 삭제를 지원한다.
- 작성 시 제목, 내용, 수정용 비밀번호를 받는다.
- 수정과 삭제 시 저장된 `edit_password`와 요청 비밀번호를 비교한다.
- 의뢰서에 따라 비밀번호는 평문 저장하되 응답, 로그, 예외, 챗봇 context에는 절대 포함하지 않는다.
- 비밀번호 불일치는 403, 없는 게시글은 404를 반환한다.
- 조회수·검색 등 선택 기능은 요청받았을 때만 추가한다.

### 여행 코스와 혼잡도

- 제공 JSON의 콘텐츠 유형 `25` 여행코스와 사용자가 만드는 코스를 구분한다.
- 사용자 코스를 요청받으면 장소 순서를 `sequence`로 보존하고, 중복 ID와 없는 장소를 검증하며, 수정은 한 트랜잭션으로 처리한다.
- 혼잡도는 의뢰서의 필수 기능이 아니다. 요청받은 경우에만 외부 데이터의 라이선스와 사용 범위를 먼저 확인한다.
- 혼잡도 매핑이 없으면 `available=false`, 외부 장애는 502, 필수 API 키 누락은 503으로 처리하고 응답을 방어적으로 파싱한다.

### 챗봇

- 먼저 SQLite에서 관련 장소와 게시글을 검색한다.
- 전체 JSON이나 전체 테이블을 OpenAI API에 보내지 않고 최소한의 관련 context만 전달한다.
- 비밀번호, API 키, 내부 설정을 context에 포함하지 않는다.
- API 키 누락은 503, 외부 API 장애는 502로 처리한다.
- 외부 API를 테스트에서는 mock하고 오류, timeout, 빈 검색 결과를 검증한다.

## 테스트 기준

최소한 정상 요청, 없는 리소스, 잘못된 입력, 잘못된 비밀번호, 비밀번호 비노출, 필터·정렬·페이지네이션을 검증한다. 외부 API는 mock하고, 다중 DB 쓰기는 rollback을 검증한다. 관련 테스트 후 전체 `pytest -v`를 실행하며 실패한 상태로 완료 보고하지 않는다.

