---
name: localhub-release-check
description: Audit the LocalHub project before GitLab submission, demonstration, Netlify frontend deployment, or Render backend deployment. Use for final readiness checks covering required deliverables, supplied Seoul data integrity and attribution, API registration, security, tests, environment variables, SQLite packaging, OpenAPI, and deployment configuration. When explicitly asked, apply minimal fixes for failed checks; do not add unrelated product features.
---

# LocalHub 배포 및 제출 검사

## 운영 원칙

- 사용자가 검사만 요청하면 파일을 수정하지 않고 문제 목록을 먼저 보고한다.
- 수정을 요청하면 합의된 심각도와 범위의 문제만 최소한으로 수정한다.
- API 명세를 임의로 바꾸거나 새 선택 기능을 추가하지 않는다.
- 비밀값은 검색 결과나 보고서에 출력하지 않는다.
- 수정 후 관련 테스트와 전체 테스트를 다시 실행한다.

## 1. 기준 확인

백엔드 `AGENTS.md`, 저장소 루트의 개발 의뢰서, `data/서울/SCHEMA.md`, `data/서울/SOURCE.md`를 확인한다. PDF 텍스트 추출 도구가 없으면 사용자 제공 요구사항과 저장소 문서를 기준으로 검사하고 그 한계를 밝힌다.

의뢰서 기준 필수 범위는 익명 게시판 CRUD, JSON 기반 지역정보, `POST /api/chat`, Vue 3 SPA, FastAPI, SQLAlchemy ORM, SQLite, Netlify, Render, 초기 데이터가 포함된 SQLite DB, 기능 명세서, WBS, 발표 자료이다. 코스 생성, 혼잡도, 지도, 조회수 등은 구현을 약속했거나 실제 코드에 포함된 경우에만 검사한다.

## 2. 저장소와 데이터 검사

다음을 확인한다.

```bash
git status --short
git ls-files
```

- `.env`와 실제 비밀값이 추적되지 않는지 확인한다.
- `.gitignore`, `.env.example`, 의존성 파일, 실행 방법, DB 초기화 방법이 있는지 확인한다.
- 원본 JSON이 수정되지 않았고 출처·라이선스 표기가 문서와 UI에 반영됐는지 확인한다.
- JSON의 선언 건수와 `items` 실제 건수를 비교한다.
- 현재 제공 폴더의 7개 JSON 합계 6,518건과 `SOURCE.md`의 8,150건 사이 차이를 검사한다. 음식점 파일이 없으면 누락으로 명시하고 데이터를 조작해 맞추지 않는다.
- 제출용 SQLite 파일에 필요한 초기 데이터가 실제로 들어 있는지 확인한다.

## 3. 코드와 보안 검사

- 비밀번호가 응답 schema, 로그, 예외, 챗봇 context에 포함되지 않는지 확인한다.
- API 키와 인증 정보가 코드에 하드코딩되지 않았는지 확인한다.
- 모든 router가 FastAPI app에 등록됐는지 확인한다.
- CORS가 환경변수 기반 허용 origin으로 제한되는지 확인한다.
- SQLite URL, `connect_args`, 상대 경로, 데이터 디렉터리 생성이 실행 환경에 맞는지 확인한다.
- 외부 API timeout과 502/503 처리가 있는지 확인한다.
- 400, 403, 404, 422, 502, 503 사용이 일관적인지 확인한다.
- `mapx=longitude`, `mapy=latitude`인지 확인한다.
- 사용하지 않는 import와 명백한 dead code를 확인한다.

## 4. API와 테스트 검사

FastAPI OpenAPI schema에서 실제 등록 경로를 읽어 최소한 다음 동작을 확인한다.

```text
GET    /api/locations
GET    /api/locations/{location_id}
GET    /api/posts
GET    /api/posts/{post_id}
POST   /api/posts
PUT 또는 PATCH /api/posts/{post_id}
DELETE /api/posts/{post_id}
POST   /api/chat
```

`GET /api/health`는 Render 상태 확인용 권장 경로로 검사하되 의뢰서 필수 API라고 단정하지 않는다. 코스, 혼잡도, 댓글 등은 구현된 경우 OpenAPI와 테스트가 일치하는지 추가 검사한다.

다음을 실행한다.

```bash
pytest -v
python -m compileall app
```

프론트엔드가 같은 저장소에 있으면 해당 package script의 lint, test, build를 실행하고 Vue 3 SPA와 모바일 챗봇 UI 요구사항을 확인한다.

## 5. 배포와 산출물 검사

- Render 시작 명령이 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`와 동등한지 확인한다.
- Build Command와 필요한 환경변수 이름만 정리한다.
- Render에서 SQLite 파일 경로와 data 디렉터리가 유효한지 확인한다.
- 무료 또는 비영구 파일시스템에서 SQLite 변경 내용이 재배포·재시작 후 사라질 위험을 명시한다.
- Netlify 설정, 프론트엔드 API base URL, CORS origin이 서로 일치하는지 확인한다.
- GitLab 저장소 URL, Netlify URL, Render URL, 초기 데이터 DB, 기능 명세서, WBS, 발표 자료의 존재를 확인한다.
- 의뢰서가 Codex 사용을 금지하지만 이 저장소에 Codex Skill이 포함된다는 정책 충돌을 High로 보고하고 사람이 제출 전에 해결하도록 요구한다. 이를 숨기거나 준수했다고 표시하지 않는다.

## 6. 결과 형식

심각도 순서로 `High`, `Medium`, `Low` 문제를 먼저 제시하고 파일과 수정 여부를 적는다. 이어서 통과 항목, 실행한 명령과 테스트 성공/실패 수, Build/Start Command, 환경변수 이름, 남은 배포 위험, 사람이 직접 확인할 항목을 정리한다. 실패한 필수 검사가 있으면 배포 가능하다고 보고하지 않는다.
