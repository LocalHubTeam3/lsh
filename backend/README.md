# LocalHub Backend

서울 관광 장소, 익명 게시판, 사용자 여행 코스, 서울 실시간 인구, DB 기반 챗봇을 제공하는 FastAPI API입니다.

## 처음 한 번 설치

### Git Bash

```bash
cd /c/Users/SSAFY/Desktop/team_proj/backend

python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# .env가 없을 때만 실행
cp -n .env.example .env

# 원본 JSON을 SQLite에 적재
python -m scripts.seed_locations
```

기존 `.venv`가 이전 경로를 참조해 실행되지 않으면 다음처럼 백업 후 다시 생성합니다.

```bash
deactivate 2>/dev/null || true
mv .venv .venv_old
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

정상 동작을 확인한 뒤 `.venv_old`는 삭제해도 됩니다.

### Windows PowerShell

```powershell
cd C:\Users\SSAFY\Desktop\team_proj\backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# .env가 없을 때만 복사
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

.\.venv\Scripts\python.exe -m scripts.seed_locations
```

## Backend 서버 실행

### Git Bash

```bash
cd /c/Users/SSAFY/Desktop/team_proj/backend
source .venv/Scripts/activate
python -m uvicorn app.main:app --reload
```

가상환경 활성화가 잘못된 경우에도 다음 명령으로 직접 실행할 수 있습니다.

```bash
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
cd C:\Users\SSAFY\Desktop\team_proj\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- API 문서: `http://127.0.0.1:8000/docs`
- 상태 확인: `http://127.0.0.1:8000/api/health`
- 독립 frontend: `http://localhost:5173/`
- 서버 종료: 터미널에서 `Ctrl+C`

## 테스트

Git Bash:

```bash
cd /c/Users/SSAFY/Desktop/team_proj/backend
./.venv/Scripts/python.exe -m pytest -v
```

PowerShell:

```powershell
cd C:\Users\SSAFY\Desktop\team_proj\backend
.\.venv\Scripts\python.exe -m pytest -v
```

외부 API를 사용할 때 `.env`에 `SEOUL_API_KEY`와 `OPENAI_API_KEY`를 설정합니다. AI 모델은 `OPENAI_MODEL`로 변경할 수 있으며 기본값은 `gpt-5-mini`입니다. 혼잡도는 서울시 공식 웹페이지가 사용하는 HTTPS API를 먼저 호출하고, 이 요청이 실패하면 `SEOUL_API_KEY`를 사용하는 8088 OpenAPI로 재시도합니다. 배포 시 시작 명령은 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`입니다. Render의 비영구 파일 시스템에서는 SQLite로 생성한 게시글과 코스가 재배포 시 사라질 수 있습니다.

키가 없는 상태에서도 장소 목록과 지도는 정상 동작합니다. 서울시 HTTPS API가 정상이라면 `SEOUL_API_KEY` 없이도 혼잡도가 표시됩니다. HTTPS API가 실패하고 fallback 키도 없을 때는 `서울시 API 키를 적어야 해요.`가 표시됩니다. 챗봇 키가 없으면 `OpenAI API 키를 적어야 해요.` 안내로 대체됩니다.

## 데이터

이 서비스는 한국관광공사 Tour API(TourAPI 4.0)의 데이터를 활용하였습니다.  
출처: 한국관광공사 (https://www.data.go.kr/data/15101578/openapi.do)  
라이선스: 공공누리 제3유형

제공된 원본은 `data/raw/서울`의 7개 JSON, 총 6,518건입니다. `SOURCE.md`에는 음식점 1,632건을 포함한 8,150건으로 기록되어 있으나 음식점 JSON은 제공되지 않았으므로 생성하지 않았습니다. 원본 JSON은 수정하지 않습니다.

지도에서 장소를 클릭하면 해당 장소의 TourAPI `title`을 그대로 서울시 HTTPS 혼잡도 API에 조회합니다. 정확히 일치하는 실시간 데이터가 있을 때만 혼잡도를 표시하며, 주변 핫스팟이나 수동 매핑 데이터로 대체하지 않습니다.

## 주요 API

- `GET /api/locations`, `GET /api/locations/{id}`, `GET /api/locations/{id}/crowd`
- `GET /api/map/locations`, `GET /api/map/search?query=경복`
- `GET|POST /api/posts`, `GET|PUT|DELETE /api/posts/{id}`
- `GET|POST /api/courses`, `GET|PUT|DELETE /api/courses/{id}`
- `POST /api/chat`
- `POST /api/ai/travel-basket-feedback` (`location_ids`와 선택적인 `request`로 여행 바구니 피드백 생성)

게시글과 코스의 편집 비밀번호는 교육용 명세에 따라 평문 저장하지만 API 응답, 로그, 챗봇 문맥에는 포함하지 않습니다.

## 독립 frontend 연결

frontend 코드는 형제 폴더 `../frontend`에 있습니다. `../frontend/config.js`의 `window.LOCALHUB_API_BASE_URL`이 이 backend 주소를 가리키며, 기본값은 `http://localhost:8000`입니다. 원본 JSON 파일을 브라우저에서 직접 읽지 않고 API를 통해 접근하므로 데이터 저장 방식이 바뀌어도 frontend 코드는 유지됩니다.

frontend는 `http://localhost:5173`에서 별도로 실행하며 backend의 `FRONTEND_ORIGINS`에 해당 origin이 허용되어 있습니다.

## 정책 확인 필요

개발 의뢰서는 AI 도구로 VSCode Copilot만 허용하고 Codex 사용을 금지합니다. 현재 작업 방식과 충돌하므로 제출 전 담당자에게 별도 확인해야 합니다.
