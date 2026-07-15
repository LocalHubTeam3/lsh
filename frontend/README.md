# LocalHub Frontend

서울 관광 장소, 지도, 익명 커뮤니티, 데이터 기반 챗봇을 제공하는 Vue 3 SPA입니다. FastAPI 백엔드와 REST API로 연동합니다.

## 실행

백엔드를 먼저 실행합니다.

```powershell
cd C:\Users\SSAFY\Desktop\team_proj\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

새 터미널에서 프론트엔드를 실행합니다.

```powershell
cd C:\Users\SSAFY\Desktop\team_proj\frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`에 접속합니다.

## 환경변수

기본 API 주소는 `http://localhost:8000`입니다. 다른 백엔드를 사용하려면 `.env`를 만들고 다음 값을 설정합니다.

```dotenv
VITE_API_BASE_URL=https://api.example.com
```

## 주요 화면

- `/`: 서비스 소개와 추천 장소
- `/locations`: 장소 검색, 분류 필터, 페이지 이동
- `/locations/:id`: 장소 상세와 혼잡도
- `/map`: Leaflet 기반 장소 지도, spot 드래그앤드롭 여행 장바구니, 코스 저장
- `/courses`: 저장된 사용자 여행 코스 목록
- `/courses/:id`: 코스 상세, 장소 순서 변경, 수정 및 삭제
- `/community`: 익명 게시글 검색, 정렬, 목록
- `/community/write`: 게시글 작성
- `/community/:id`: 게시글 상세, 수정, 삭제
- 우측 하단 위젯: 백엔드 데이터 기반 여행 챗봇

지도에서는 마커를 클릭하면 장소 상세 패널이 열립니다. 상세 패널을 화면 아래로 드래그하면 하단 중앙에서 여행 장바구니가 올라오며, 그 위에 놓으면 코스에 추가됩니다. 장바구니는 평소 숨겨지고 상세 패널을 닫거나 하단의 장바구니 표시 버튼을 누르면 다시 열립니다. 장바구니 내부 드래그로 방문 순서를 변경할 수 있고, 모바일에서는 상세 패널의 `장바구니 담기` 버튼도 사용할 수 있습니다.

게시글 비밀번호는 교육용 익명 게시판 요구사항에 따라 수정과 삭제 확인에 사용됩니다. 실제 서비스에서는 인증 기반 구조로 교체해야 합니다.

## 빌드와 배포

```powershell
npm run build
```

결과물은 `dist/`에 생성됩니다. `netlify.toml`에는 Vue Router history 모드를 위한 SPA fallback이 포함돼 있습니다. Netlify에서는 `VITE_API_BASE_URL` 환경변수에 배포된 FastAPI 주소를 설정해야 합니다.

지도 타일은 OpenStreetMap을 사용하므로 인터넷 연결이 필요합니다. 관광 데이터 출처는 한국관광공사 TourAPI 4.0이며 공공누리 제3유형을 따릅니다.
