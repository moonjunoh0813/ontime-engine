from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.decision_engine import (
    FIXED_ROUTE_SEGMENTS,
    compute_departure_time,
    parse_hhmm,
)

app = FastAPI(title="Ontime Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComputeRequest(BaseModel):
    destination_time: str


class ComputeResponse(BaseModel):
    recommended_departure_time: str


def wait_provider_stub(stop: str, route: str, time_hhmm: str) -> int:
    # Headway-based fallback to avoid zero-wait unrealistic results.
    headway_by_route = {
        "subway_suin": 8,
        "bus_5100": 12,
        "bus_51": 10,
    }
    headway = headway_by_route.get(route, 8)

    minutes = int(time_hhmm.split(":")[1])
    return (headway - (minutes % headway)) % headway


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compute", response_model=ComputeResponse)
def compute(req: ComputeRequest) -> ComputeResponse:
    try:
        parse_hhmm(req.destination_time)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="destination_time must be in HH:MM format (e.g., '10:00')",
        )

    try:
        departure = compute_departure_time(
            destination_time=req.destination_time,
            segments=FIXED_ROUTE_SEGMENTS,
            wait_provider=wait_provider_stub,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    return ComputeResponse(recommended_departure_time=departure)
