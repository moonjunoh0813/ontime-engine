# Ontime Frontend

## Backend (FastAPI) 실행
루트 디렉터리(`ontime-engine`)에서:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend 실행
`frontend` 디렉터리에서:

```bash
npm install
npm run dev
```

기본 개발 URL은 `http://localhost:5173` 입니다.

## 환경 변수
프론트엔드는 아래 값을 사용합니다.

```js
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
```

`.env` 예시:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

프론트는 `POST ${API_BASE}/compute`로 `{"destination_time":"HH:MM"}`를 전송하고,
`{"recommended_departure_time":"HH:MM"}`를 받아 대시보드에 표시합니다.
