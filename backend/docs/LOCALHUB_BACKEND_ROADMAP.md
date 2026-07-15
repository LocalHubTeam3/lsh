# LocalHub 백엔드 개발 로드맵

이 문서는 LocalHub FastAPI 백엔드를 Codex와 단계적으로 구현하기 위한 실행 순서다. 한 번에 전체 백엔드를 요청하지 않고, 각 단계에서 구현, 검증, 커밋을 완료한 뒤 다음 단계로 이동한다.

## 0. 시작 전에 확인할 사항

### 프로젝트 범위

- FastAPI
- SQLAlchemy 2.x
- SQLite
- Pydantic v2
- pytest
- httpx
- 서울 지역 JSON 데이터
- 장소 조회 API
- 익명 게시글 CRUD
- 여행 코스 CRUD와 인기순 조회
- 서울시 실시간 인구 API 연동
- OpenAI 기반 `POST /api/chat`
- Render 배포

### 제외할 기능

2일 프로젝트에서는 다음 기능을 도입하지 않는다.

- Docker
- PostgreSQL, MySQL
- Redis
- Alembic
- 회원가입, 로그인, JWT
- 관리자 페이지
- WebSocket
- 벡터 데이터베이스
- 요청받지 않은 리팩터링

### 제공 데이터 현황

현재 원본 데이터는 backend 저장소의 `data/raw/서울/`에 있다.

| 콘텐츠 유형 | 파일 | 건수 |
|---|---|---:|
| 관광지 | `서울_관광지.json` | 783 |
| 문화시설 | `서울_문화시설.json` | 566 |
| 축제공연행사 | `서울_축제공연행사.json` | 201 |
| 여행코스 | `서울_여행코스.json` | 51 |
| 레포츠 | `서울_레포츠.json` | 126 |
| 숙박 | `서울_숙박.json` | 423 |
| 쇼핑 | `서울_쇼핑.json` | 4,368 |
| 합계 | 7개 JSON | 6,518 |

`SOURCE.md`에는 음식점 1,632건을 포함한 총 8,150건으로 적혀 있지만 실제 음식점 JSON은 없다. 없는 데이터를 만들거나 있다고 가정하지 말고, 기능 명세서에 이 차이를 기록한다.

원본 JSON은 수정하지 않는다. 적재 스크립트가 `data/raw/서울/*.json`을 읽도록 구현한다. 서비스와 문서에는 한국관광공사 TourAPI 4.0 및 공공누리 제3유형 출처를 표시한다.

### 정책 충돌

제공된 개발 의뢰서에는 Codex 사용 금지 조항이 있다. 현재 Codex를 사용하는 방식과 충돌하므로, 제출 전에 담당자에게 허용 여부를 확인해야 한다. 이 문제를 숨기거나 준수한 것으로 표시하지 않는다.

### 진행 원칙

1. 각 단계 시작 전에 `git status --short`를 확인한다.
2. Codex에는 해당 단계의 범위만 요청한다.
3. 관련 테스트를 먼저 실행한다.
4. 전체 테스트를 실행한다.
5. 서버나 API를 직접 확인한다.
6. 변경 파일을 검토한다.
7. 정상 동작할 때만 커밋한다.
8. 테스트가 실패한 상태로 다음 단계에 진입하지 않는다.

## 전체 진행표

| 단계 | 작업 | 핵심 결과물 | 완료 |
|---:|---|---|:---:|
| 1 | 저장소 분석 | 구조, API, DB 계획 | [ ] |
| 2 | FastAPI 기본 서버 | health API, 설정, CORS | [ ] |
| 3 | SQLAlchemy 연결 | 5개 테이블, SQLite 초기화 | [ ] |
| 4 | 서울 데이터 적재 | seed 스크립트, locations 데이터 | [ ] |
| 5 | 장소 조회 API | 검색, 필터, 페이지네이션 | [ ] |
| 6 | 익명 게시글 CRUD | 비밀번호 검증, 조회수 | [ ] |
| 7 | 여행 코스 CRUD | 장소 순서, 인기순, 트랜잭션 | [ ] |
| 8 | 실시간 혼잡도 | 매핑, 5분 캐시, 외부 API | [ ] |
| 9 | 챗봇 | DB 검색, Responses API | [ ] |
| 10 | 통합 및 배포 검사 | 전체 테스트, Render 설정 | [ ] |

---

## 1단계. 저장소 분석

### 목표

코드를 수정하기 전에 현재 상태, 누락 항목, API와 DB 설계를 확정한다.

### Codex 요청

```text
현재 저장소를 분석해줘.

아직 파일을 수정하지 마.

다음 내용을 작성해줘.

1. 현재 폴더 구조
2. 현재 구현된 기능
3. 누락된 파일
4. 명세를 만족하기 위한 API 목록
5. 데이터베이스 테이블 설계
6. 구현 순서
7. 2일 안에 구현할 때 제외해야 할 기능
8. 예상되는 기술적 위험

프로젝트 요구사항:

- FastAPI
- SQLAlchemy 2.x
- SQLite
- data/raw/서울 아래의 제공 JSON 7개
- 익명 게시글 CRUD
- 수정 및 삭제 시 비밀번호 확인
- 여행 코스 CRUD
- 코스 조회수와 인기 코스
- 서울시 실시간 인구 API
- POST /api/chat
- Render 배포

구조는 routers, services, models, schemas 수준으로 단순하게 유지해.
코드는 아직 수정하지 마.
```

계획이 과도하면 다음 요청으로 범위를 줄인다.

```text
현재 계획이 과제 범위보다 복잡하다.

다음을 제거해서 계획을 다시 작성해줘.

- Docker
- PostgreSQL
- Redis
- Alembic
- 회원 인증
- 관리자 페이지
- WebSocket
- 벡터 데이터베이스

FastAPI, SQLAlchemy, SQLite만 사용하는 단순한 구조로 다시 계획해.
코드는 아직 수정하지 마.
```

### 완료 조건

- [ ] API 목록이 확정됐다.
- [ ] `locations`, `posts`, `courses`, `course_places`, `crowd_cache` 역할이 정의됐다.
- [ ] 구현하지 않을 기능이 명확하다.
- [ ] 실제 데이터 7개 파일과 누락된 음식점 파일이 계획에 반영됐다.

---

## 2단계. FastAPI 기본 서버

### 작업 범위

```text
app/main.py
app/config.py
app/routers/health.py
app/__init__.py
app/routers/__init__.py
.env.example
.gitignore
README.md
requirements.txt 또는 pyproject.toml
```

### Codex 요청

```text
$localhub-feature FastAPI 기본 서버를 구현해줘.

이번 작업 범위:

- app/main.py
- app/config.py
- app/routers/health.py
- app/__init__.py
- app/routers/__init__.py
- .env.example
- .gitignore
- README.md
- 의존성 파일

요구사항:

1. GET /api/health를 구현한다.
2. 응답은 {"status": "ok"}이다.
3. pydantic-settings로 환경변수를 관리한다.
4. CORS origin은 FRONTEND_ORIGINS 환경변수에서 읽는다.
5. 아직 데이터베이스 모델은 만들지 않는다.
6. 아직 장소, 게시글, 코스, 챗봇 API를 만들지 않는다.
7. uvicorn 실행 방법을 README에 작성한다.
8. 구현 후 서버를 실행해 health API를 확인한다.
9. 변경 파일과 테스트 결과를 설명한다.
```

### 실행 및 확인

```powershell
uvicorn app.main:app --reload
```

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`

### 완료 조건

- [ ] health 응답이 `{"status":"ok"}`이다.
- [ ] Swagger 문서가 열린다.
- [ ] CORS 설정이 `FRONTEND_ORIGINS`에서 로드된다.
- [ ] `.env`는 제외되고 `.env.example`만 추적된다.

### 커밋

```powershell
git add .
git commit -m "chore: initialize FastAPI backend"
```

---

## 3단계. SQLAlchemy와 테이블

### Codex 요청

```text
$localhub-feature 현재 FastAPI 프로젝트에 SQLAlchemy 2.x와 SQLite를 연결해줘.

이번 작업 범위:

- app/database.py
- app/models.py
- 필요한 경우 app/main.py 최소 수정
- 모델 테스트

다음 테이블을 구현해줘.

1. locations
2. posts
3. courses
4. course_places
5. crowd_cache

요구사항:

- SQLAlchemy 2.x typed declarative 문법을 사용한다.
- DATABASE_URL 환경변수를 사용한다.
- 기본값은 sqlite:///./data/localhub.db이다.
- SQLite connect_args 설정을 적용한다.
- data 디렉터리가 없으면 생성한다.
- Base.metadata.create_all로 테이블을 생성한다.
- posts와 courses에는 edit_password와 views가 있다.
- courses와 locations는 course_places를 통해 연결한다.
- course_places에는 sequence가 있다.
- course_id와 sequence 조합의 중복을 방지한다.
- 비밀번호는 응답에 노출하면 안 된다는 설명을 모델 근처에 짧게 남긴다.
- 기존 health API를 깨뜨리지 않는다.
- 테스트를 실행하고 결과를 설명한다.
```

### 권장 핵심 필드

| 테이블 | 핵심 필드 |
|---|---|
| `locations` | `id`, `content_id`, `title`, 주소, 좌표, 이미지, 콘텐츠 유형, 카테고리, 혼잡도 매핑 |
| `posts` | `id`, `category`, `title`, `content`, `edit_password`, `views`, 생성·수정 시각 |
| `courses` | `id`, `title`, `description`, `edit_password`, `views`, 생성·수정 시각 |
| `course_places` | `course_id`, `location_id`, `sequence` |
| `crowd_cache` | 장소 또는 area code, 혼잡도 값, API 기준 시각, 캐시 저장 시각 |

### 완료 조건

- [ ] 앱 시작 시 SQLite 파일과 테이블이 생성된다.
- [ ] 모든 관계와 unique 제약이 의도대로 동작한다.
- [ ] health API가 계속 통과한다.
- [ ] 모델 테스트가 통과한다.

### 커밋

```powershell
git add .
git commit -m "feat: add database models"
```

---

## 4단계. 서울 JSON 데이터 적재

### 데이터 경로 결정

현재 데이터는 단일 `seoul_locations.json`이 아니라 `data/raw/서울/` 아래 7개 파일이다. 원본을 합치거나 덮어쓰지 않고, seed 스크립트가 7개 파일을 순회하게 한다.

백엔드만 별도 저장소로 분리할 경우 원본 파일을 `backend/data/raw/서울/`로 그대로 복사하고 출처 문서도 함께 보존한다. 파일 내용을 수정하지 않는다.

### Codex 요청

```text
$localhub-feature 저장소의 data/raw/서울 아래 JSON 파일 7개를 SQLite locations 테이블에 적재하는 scripts/seed_locations.py를 구현해줘.

사용할 JSON 필드:

- contentid
- title
- addr1
- addr2
- mapx
- mapy
- firstimage
- contenttypeid
- cat1
- cat2
- cat3

매핑:

- contentid -> content_id
- addr1 -> address
- addr2 -> address_detail
- mapx -> longitude
- mapy -> latitude
- firstimage -> image_url
- contenttypeid -> content_type_id

요구사항:

1. 각 JSON의 최상위 items 배열을 읽는다.
2. content_id는 unique이다.
3. 빈 문자열은 None으로 변환한다.
4. mapx는 longitude, mapy는 latitude로 float 변환한다.
5. 좌표 변환에 실패한 항목은 건너뛰고 오류로 집계한다.
6. 기존 content_id는 중복 저장하지 않는다.
7. 전체, 신규, 중복, 오류 건수를 출력한다.
8. 파일별 집계와 전체 합계를 출력한다.
9. python -m scripts.seed_locations로 실행 가능하게 한다.
10. 실제 스크립트를 실행하고 결과를 보여준다.
11. 테스트용 JSON fixture와 pytest를 작성한다.
12. 원본 JSON은 수정하지 않는다.
13. SOURCE.md의 8,150건과 실제 6,518건 차이를 README 또는 결과에 기록한다.
```

### 실행

```powershell
python -m scripts.seed_locations
python -m scripts.seed_locations
```

두 번째 실행에서는 신규 저장이 0이고 기존 항목이 모두 중복 처리되어야 한다.

### 기대 결과

```text
전체: 6518
신규 저장: 6518
중복: 0
오류: 실제 검증 결과
```

정확한 신규·오류 수는 실제 데이터 검증 결과를 따른다. 예시 숫자에 맞추려고 데이터를 조작하지 않는다.

### 완료 조건

- [ ] 스크립트가 7개 파일을 모두 읽는다.
- [ ] 중복 실행해도 row가 늘어나지 않는다.
- [ ] `content_id`가 unique다.
- [ ] 경도와 위도가 바뀌지 않았다.
- [ ] fixture 테스트와 실제 적재가 모두 성공했다.

### 커밋

```powershell
git add .
git commit -m "feat: seed Seoul location data"
```

---

## 5단계. 장소 조회 API

### Codex 요청

```text
$localhub-feature 장소 조회 API를 구현해줘.

엔드포인트:

- GET /api/locations
- GET /api/locations/{location_id}

목록 query parameter:

- search
- category
- page, 기본값 1
- size, 기본값 20, 최대 100

요구사항:

1. search는 title과 address를 검색한다.
2. category는 category1, category2, category3에서 검색한다.
3. 목록 응답은 items, page, size, total 구조이다.
4. 상세 장소가 없으면 404를 반환한다.
5. latitude와 longitude를 명확하게 구분한다.
6. ORM 객체를 그대로 반환하지 않는다.
7. Pydantic v2 response schema를 사용한다.
8. router, service, schema를 분리한다.
9. 안정적인 페이지네이션을 위해 정렬 기준과 보조 키를 둔다.
10. pytest TestClient 테스트를 작성한다.
11. pytest를 실행하고 실패하면 수정한다.
```

### 테스트

```powershell
pytest tests/test_locations.py -v
pytest -v
```

### 완료 조건

- [ ] 검색과 카테고리 필터가 동작한다.
- [ ] `page`, `size`, `total`이 정확하다.
- [ ] `size > 100`이 검증된다.
- [ ] 없는 장소는 404다.
- [ ] 응답 좌표가 올바르다.

### 커밋

```powershell
git add .
git commit -m "feat: add location APIs"
```

---

## 6단계. 익명 게시글 CRUD

### Codex 요청

```text
$localhub-feature 익명 게시글 CRUD API를 구현해줘.

엔드포인트:

- GET /api/posts
- GET /api/posts/{post_id}
- POST /api/posts
- PUT /api/posts/{post_id}
- DELETE /api/posts/{post_id}

작성 요청:

- category
- title
- content
- password

요구사항:

1. password는 DB의 edit_password에 평문으로 저장한다.
2. edit_password는 어떤 API 응답에도 포함하지 않는다.
3. 비밀번호를 로그, 예외, 챗봇 context에 출력하지 않는다.
4. 수정과 삭제 요청의 password를 저장된 edit_password와 비교한다.
5. 틀린 비밀번호는 403이다.
6. 없는 게시글은 404이다.
7. 상세 조회 성공 시 views를 1 증가한다.
8. 목록에서 search를 지원한다.
9. sort=latest와 sort=views를 지원한다.
10. page와 size 페이지네이션을 지원한다.
11. 생성 성공은 201이다.
12. 삭제 성공은 body 없는 204이다.
13. router, service, schema를 분리한다.
14. 테스트를 작성하고 모두 통과할 때까지 수정한다.

테스트 항목:

- 생성 성공
- 목록 조회와 페이지네이션
- 검색
- 상세 조회와 조회수 증가
- 틀린 비밀번호 수정 실패
- 올바른 비밀번호 수정 성공
- 틀린 비밀번호 삭제 실패
- 올바른 비밀번호 삭제 성공
- 모든 응답에 edit_password가 없는지 확인
```

### 테스트

```powershell
pytest tests/test_posts.py -v
pytest -v
```

### 완료 조건

- [ ] CRUD 상태 코드가 명세와 일치한다.
- [ ] 조회수가 상세 조회마다 증가한다.
- [ ] 비밀번호가 어떤 응답에도 없다.
- [ ] 검색, 정렬, 페이지네이션이 통과한다.

### 커밋

```powershell
git add .
git commit -m "feat: add anonymous post CRUD"
```

---

## 7단계. 여행 코스 CRUD

제공 JSON의 `contentTypeId=25` 여행코스와 사용자가 작성하는 코스를 구분한다. 이 단계의 `courses`는 사용자가 장소를 조합해 만드는 코스다.

### Codex 요청

```text
$localhub-feature 사용자 여행 코스 CRUD를 구현해줘.

엔드포인트:

- GET /api/courses
- GET /api/courses/{course_id}
- POST /api/courses
- PUT /api/courses/{course_id}
- DELETE /api/courses/{course_id}

생성 요청:

- title
- description
- password
- location_ids

요구사항:

1. location_ids는 최소 2개이다.
2. 중복 location_id가 있으면 400이다.
3. 존재하지 않는 location_id가 있으면 400이다.
4. 입력 장소 순서를 course_places.sequence에 저장한다.
5. 상세 응답에서도 같은 순서로 반환한다.
6. 상세 조회 성공 시 views를 1 증가한다.
7. sort=latest와 sort=popular을 지원한다.
8. popular은 views 내림차순이다.
9. views가 같으면 created_at 내림차순이다.
10. 수정 및 삭제 시 비밀번호를 확인한다.
11. 코스 수정 시 기존 course_places를 새 순서로 교체한다.
12. 코스와 course_places 수정 전체를 하나의 transaction으로 처리한다.
13. 처리 실패 시 rollback한다.
14. 비밀번호는 응답에 포함하지 않는다.
15. router, service, schema를 분리한다.
16. 테스트를 작성하고 실행한다.
```

### 요청 예시

```json
{
  "title": "성수 반나절 코스",
  "description": "서울숲과 성수 쇼핑 코스",
  "password": "1234",
  "location_ids": [15, 31, 8]
}
```

프론트엔드는 지도에서 선택한 장소 ID 배열을 순서 그대로 전달한다.

### 테스트

```powershell
pytest tests/test_courses.py -v
pytest -v
```

### 완료 조건

- [ ] 최소 장소 수, 중복, 없는 장소가 검증된다.
- [ ] 생성 및 수정 후 장소 순서가 보존된다.
- [ ] popular 정렬과 동률 정렬이 정확하다.
- [ ] 수정 실패 시 기존 코스와 장소 순서가 보존된다.
- [ ] 비밀번호가 응답에 없다.

### 커밋

```powershell
git add .
git commit -m "feat: add travel course CRUD"
```

---

## 8단계. 서울시 실시간 혼잡도

### 구현 전 확인

서울시 실시간 인구 API는 서울 주요 장소만 지원한다. 일반 관광지 전체에 자동 대응하지 않으므로 `locations`에 `crowd_area_code`, `crowd_area_name`을 명시적으로 매핑해야 한다.

| 관광 장소 | 혼잡도 API 기준 장소 |
|---|---|
| 무신사 스탠다드 성수 | 성수카페거리 |
| 덕수궁 | 광화문·덕수궁 |
| 경복궁 | 경복궁 |
| 서울숲 | 서울숲공원 |
| 매핑 불가능한 장소 | 혼잡도 정보 없음 |

실제 API 매뉴얼, 이용 약관, 라이선스, 정확한 URL과 응답 schema를 구현 전에 확인한다. 추정 인구라는 안내를 UI와 API 응답에 포함한다.

### Codex 요청

```text
$localhub-feature 서울시 실시간 인구 API 연동을 구현해줘.

엔드포인트:

GET /api/locations/{location_id}/crowd

처리 순서:

1. location을 조회한다.
2. location이 없으면 404이다.
3. crowd_area_code와 crowd_area_name이 없으면 available=false를 반환한다.
4. crowd_cache를 확인한다.
5. 캐시가 5분 이내면 외부 API를 호출하지 않는다.
6. 캐시가 없거나 오래됐으면 서울시 API를 호출한다.
7. API 결과를 방어적으로 파싱해 crowd_cache에 저장한다.
8. 프론트용 응답으로 반환한다.

응답 필드:

- available
- location_id
- area_code
- area_name
- congestion_level
- population_min
- population_max
- population_estimate
- updated_at
- notice

요구사항:

- SEOUL_API_KEY 환경변수를 사용한다.
- httpx.AsyncClient를 사용한다.
- 명시적 timeout을 설정한다.
- 외부 API 오류는 502로 반환한다.
- API 키가 없으면 503으로 반환한다.
- API 키를 로그나 오류 응답에 출력하지 않는다.
- 응답 필드가 없어도 KeyError로 종료되지 않게 한다.
- population_estimate는 최솟값과 최댓값의 중간값이다.
- notice에 추정 데이터라는 내용을 포함한다.
- 외부 API 테스트는 mock을 사용한다.
- 캐시 적중 시 외부 API가 호출되지 않는지 테스트한다.
- 실제 URL과 필드명은 제공된 서울시 API 매뉴얼을 근거로 작성한다.
```

### 응답 예시

```json
{
  "available": true,
  "location_id": 15,
  "area_code": "POI123",
  "area_name": "성수카페거리",
  "congestion_level": "붐빔",
  "population_min": 12000,
  "population_max": 14000,
  "population_estimate": 13000,
  "updated_at": "2026-07-14T16:30:00+09:00",
  "notice": "통신 데이터를 기반으로 한 추정값이며 실제 인구와 다를 수 있습니다."
}
```

### 테스트

```powershell
pytest tests/test_crowd.py -v
pytest -v
```

### 완료 조건

- [ ] 없는 장소는 404다.
- [ ] 매핑이 없으면 정상 응답과 `available=false`를 반환한다.
- [ ] 5분 캐시가 동작한다.
- [ ] API 키 누락은 503, 외부 장애는 502다.
- [ ] 외부 응답 누락 필드가 안전하게 처리된다.

### 커밋

```powershell
git add .
git commit -m "feat: add Seoul crowd API"
```

---

## 9단계. 챗봇

### 처리 구조

```text
사용자 질문
  -> SQLite에서 관련 장소, 코스, 게시글 검색
  -> 종류별 최대 5개 결과 추출
  -> 비밀번호와 내부 필드 제거
  -> 최소 context를 OpenAI Responses API에 전달
  -> answer와 references 반환
```

JSON 전체나 전체 테이블을 OpenAI API에 전달하지 않는다. 모델 이름은 코드에 고정하지 않고 `OPENAI_MODEL`로 관리한다.

### Codex 요청

```text
$localhub-feature POST /api/chat을 구현해줘.

요청 형식:

{
  "message": "성수에서 쇼핑할 장소 추천해줘",
  "history": []
}

처리 순서:

1. message를 검증한다.
2. locations에서 관련 장소를 검색한다.
3. courses에서 관련 코스를 검색한다.
4. posts에서 관련 게시글을 검색한다.
5. 종류별 검색 결과를 최대 5개로 제한한다.
6. edit_password 등 민감 필드를 제거한다.
7. 검색 결과를 짧은 context로 구성한다.
8. OpenAI Responses API를 호출한다.
9. answer와 references를 반환한다.

요구사항:

- OPENAI_API_KEY 환경변수를 사용한다.
- OPENAI_MODEL 환경변수를 사용한다.
- openai.AsyncOpenAI를 사용한다.
- 전체 JSON 파일이나 전체 DB를 프롬프트에 포함하지 않는다.
- 검색 결과가 없으면 데이터가 부족하다고 답변한다.
- 제공된 데이터 밖의 사실을 만들지 않도록 instructions를 작성한다.
- history는 최근 6개 메시지만 사용한다.
- message와 history 각 메시지 길이에 제한을 둔다.
- API 키가 없으면 503이다.
- OpenAI API 오류는 502이다.
- 내부 오류 상세나 API 키를 사용자에게 노출하지 않는다.
- 게시글과 코스 비밀번호를 context에 포함하지 않는다.
- OpenAI 호출 테스트는 mock 처리한다.
- OpenAI SDK의 현재 Responses API 사용법을 공식 문서에서 확인한다.
```

### 응답 예시

```json
{
  "answer": "성수 지역 쇼핑 장소로 무신사 스탠다드 성수를 추천합니다.",
  "references": [
    {
      "type": "location",
      "id": 15,
      "title": "무신사 스탠다드 성수"
    }
  ]
}
```

### 테스트

```powershell
pytest tests/test_chat.py -v
pytest -v
```

### 완료 조건

- [ ] DB 검색 결과만 context에 들어간다.
- [ ] 결과 개수와 history 길이가 제한된다.
- [ ] 민감 정보가 prompt와 응답에 없다.
- [ ] API 키 누락은 503, OpenAI 장애는 502다.
- [ ] OpenAI 호출 없이 mock 테스트가 통과한다.

### 커밋

```powershell
git add .
git commit -m "feat: add LocalHub chatbot"
```

---

## 10단계. 환경변수, 통합 테스트, 배포 검사

### `.env`

실제 값은 로컬 `.env`와 Render 환경변수에만 저장한다.

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./data/localhub.db
FRONTEND_ORIGINS=http://localhost:5173
OPENAI_API_KEY=실제_API_KEY
OPENAI_MODEL=팀에서_사용할_모델명
SEOUL_API_KEY=서울시_API_KEY
```

### `.env.example`

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./data/localhub.db
FRONTEND_ORIGINS=http://localhost:5173
OPENAI_API_KEY=
OPENAI_MODEL=
SEOUL_API_KEY=
```

### `.gitignore`

```gitignore
.venv/
__pycache__/
.pytest_cache/
.coverage
.env
*.pyc
*.log
```

SQLite DB는 의뢰서에서 제출을 요구한다. 개발 중에는 Git에서 제외하더라도 최종 제출 방식은 팀이 명시적으로 결정해야 한다.

- 별도 산출물로 `.db` 파일 제출
- 제출 전용 브랜치에 초기 데이터 DB 포함
- 재현 가능한 seed 명령과 원본 JSON을 함께 제공

어떤 방식을 선택하든 `.env`는 반드시 제외한다.

### 최종 Codex 요청

```text
$localhub-release-check 현재 LocalHub 프로젝트를 검사해줘.

문제를 바로 수정하지 말고 먼저 High, Medium, Low 순서로 목록만 보여줘.

검사 범위:

- 필수 API와 OpenAPI 등록 경로
- 전체 pytest
- Python compileall
- 비밀번호와 API 키 노출
- .env Git 포함 여부
- 서울 데이터 건수와 출처 표기
- 제출용 SQLite 초기 데이터
- Render 시작 명령과 환경변수
- CORS와 프론트엔드 API URL
- README 실행 방법
- 의뢰서 산출물
- Codex 사용 정책 충돌
```

목록을 검토한 뒤 수정 범위를 지정한다.

```text
$localhub-release-check 앞서 발견한 High와 Medium 문제만 최소한으로 수정해줘.
새 기능은 추가하지 마.
수정 후 관련 테스트와 전체 테스트를 실행해줘.
```

### 최종 검증 명령

```powershell
pytest -v
python -m compileall app
python -m scripts.seed_locations
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

확인할 URL:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

### Render 설정

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render 환경변수 이름:

- `APP_ENV`
- `DATABASE_URL`
- `FRONTEND_ORIGINS`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `SEOUL_API_KEY`

Render의 비영구 파일시스템에서는 SQLite에 추가된 게시글과 코스가 재배포 또는 재시작 후 사라질 수 있다. 발표 전에 초기 DB 존재 여부와 재시작 후 동작을 직접 확인한다.

### 완료 조건

- [ ] 전체 pytest가 통과한다.
- [ ] `compileall`이 성공한다.
- [ ] OpenAPI에 필수 경로가 모두 등록됐다.
- [ ] `.env`와 실제 키가 Git에 없다.
- [ ] 초기 데이터가 포함된 SQLite 제출 방식을 확정했다.
- [ ] Netlify URL, Render URL, CORS 설정이 일치한다.
- [ ] 기능 명세서에 데이터 출처와 라이선스가 있다.
- [ ] 정책 충돌을 담당자와 확인했다.
- [ ] README, 기능 명세서, WBS, 발표 자료가 준비됐다.

### 최종 커밋

```powershell
git status --short
git add .
git commit -m "chore: prepare LocalHub release"
```

---

## 2일 권장 일정

### 1일차

| 시간대 | 작업 |
|---|---|
| 오전 | 1단계 분석, 2단계 기본 서버, 3단계 DB |
| 오후 초반 | 4단계 데이터 적재, 5단계 장소 API |
| 오후 후반 | 6단계 게시글 CRUD와 테스트 |

### 2일차

| 시간대 | 작업 |
|---|---|
| 오전 | 7단계 여행 코스 CRUD |
| 오전 후반 | 8단계 혼잡도 |
| 오후 초반 | 9단계 챗봇 |
| 오후 | 10단계 통합 테스트, 배포, 문서, 발표 점검 |

시간이 부족하면 필수 제출물을 우선한다. 혼잡도와 사용자 여행 코스가 수업 또는 팀 합의상 필수가 아니라면, 게시글·지역정보·챗봇·배포의 안정성을 먼저 확보한다.

## 단계별 완료 보고 형식

각 Codex 작업이 끝나면 다음 형식으로 보고하도록 요청한다.

```text
1. 생성한 파일
2. 수정한 파일
3. 구현한 API
4. DB 변경 사항
5. 요청 및 응답 예시
6. 실행한 테스트와 결과
7. 직접 확인한 실행 결과
8. 남아 있는 제약과 위험
9. 다음 단계로 진행 가능한지
```

## 최종 Definition of Done

- [ ] 익명 게시글 CRUD와 비밀번호 검증이 동작한다.
- [ ] 장소 검색, 필터, 상세 조회가 동작한다.
- [ ] 코스 장소 순서와 인기순 정렬이 동작한다.
- [ ] 혼잡도 매핑, 캐시, 오류 처리가 동작한다.
- [ ] 챗봇이 SQLite 검색 결과만 사용한다.
- [ ] 응답, 로그, prompt에 비밀번호와 API 키가 없다.
- [ ] 전체 테스트가 통과한다.
- [ ] 초기 데이터 DB를 제출할 수 있다.
- [ ] Netlify와 Render URL이 실제로 동작한다.
- [ ] 데이터 출처와 라이선스가 문서화됐다.
- [ ] 사람이 직접 확인해야 하는 정책 및 배포 위험이 정리됐다.
