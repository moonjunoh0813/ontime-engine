from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.decision_engine import (
    compute_departure_time,
    FIXED_ROUTE_SEGMENTS,
    parse_hhmm,
)

app = FastAPI(title="Ontime Engine API")


# Step1) 입력/출력 스키마(계약)
class ComputeRequest(BaseModel):
    destination_time: str  # "HH:MM"


class ComputeResponse(BaseModel):
    recommended_departure_time: str  # "HH:MM"


# Step3) Day3용 임시 wait_provider (실시간 ETA 붙이기 전)
def dummy_wait_provider(stop: str, route: str, time_hhmm: str) -> int:
    # Day3: 아직 실시간 API가 없으므로 route별 max_wait로 대기시간을 가정한다.
    # (안전 출발시간 쪽으로 보수적으로 계산됨)
    max_wait = {
        "51": 15,
        "5100": 25,
        "수인분당선": 6,  # 임시값(나중에 실제 지하철 API/정책으로 교체)
    }
    return max_wait.get(route, 0)


@app.get("/health")
def health():
    return {"status": "ok"}


# Step2) 엔드포인트 생성 + Step4) 에러 처리
@app.post("/compute", response_model=ComputeResponse)
def compute(req: ComputeRequest) -> ComputeResponse:
    # 입력 시간 포맷 검증(HH:MM)
    try:
        parse_hhmm(req.destination_time)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="destination_time must be in HH:MM format (e.g., '10:00')",
        )

    # 엔진 호출
    try:
        departure = compute_departure_time(
            destination_time=req.destination_time,
            segments=FIXED_ROUTE_SEGMENTS,
            wait_provider=dummy_wait_provider,
        )
    except ValueError as e:
        # 엔진이 '불가능/데이터 문제'라고 판단한 케이스
        raise HTTPException(status_code=400, detail=str(e))

    return ComputeResponse(recommended_departure_time=departure)

