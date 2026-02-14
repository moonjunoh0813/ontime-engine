from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.decision_engine import (
    FIXED_ROUTE_SEGMENTS,
    compute_departure_time,
    parse_hhmm,
)

from app.adapters.gbis_bus_eta_provider import GbisBusEtaProvider
from app.adapters.suin_bundang_position_eta_provider import SuinBundangPositionEtaProvider
from app.adapters.wait_provider_snapshot import build_wait_provider_snapshot

app = FastAPI(title="Ontime Engine API")


class ComputeRequest(BaseModel):
    destination_time: str  # "HH:MM"


class ComputeResponse(BaseModel):
    recommended_departure_time: str  # "HH:MM"


def dummy_wait_provider(stop: str, route: str, time_hhmm: str) -> int:
    max_wait = {"51": 15, "5100": 25, "수인분당선": 10}
    return max_wait.get(route, 0)


def build_wait_provider():
    """
    실시간 스냅샷 wait_provider를 만들고, 실패하면 더미로 fallback.
    """
    try:
        bus_provider = GbisBusEtaProvider()
        subway_provider = SuinBundangPositionEtaProvider(toward_station="청명")

        bus_stops = [
            ("206000043", "51"),      # 성남 이마트앞
            ("203000075", "5100"),    # 청명역 4번출구
        ]
        subway_stops = [
            ("미금", "수인분당선"),
        ]

        return build_wait_provider_snapshot(
            now=datetime.now(),
            bus_provider=bus_provider,
            subway_provider=subway_provider,
            bus_stops=bus_stops,
            subway_stops=subway_stops,
            max_wait_by_route={"51": 15, "5100": 25, "수인분당선": 10},
        )
    except Exception:
        return dummy_wait_provider


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compute", response_model=ComputeResponse)
def compute(req: ComputeRequest) -> ComputeResponse:
    # 입력 포맷 검증
    try:
        parse_hhmm(req.destination_time)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="destination_time must be in HH:MM format (e.g., '10:00')",
        )

    wait_provider = build_wait_provider()

    try:
        departure = compute_departure_time(
            destination_time=req.destination_time,
            segments=FIXED_ROUTE_SEGMENTS,
            wait_provider=wait_provider,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ComputeResponse(recommended_departure_time=departure)
