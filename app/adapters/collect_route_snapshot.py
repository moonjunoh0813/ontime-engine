import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

from app.adapters.gbis_bus_eta_provider import GbisBusEtaProvider
from app.adapters.suin_bundang_position_eta_provider import SuinBundangPositionEtaProvider
from app.adapters.wait_provider_snapshot import build_wait_provider_snapshot
from app.services.decision_engine import FIXED_ROUTE_SEGMENTS, compute_departure_time

CSV_FIELDS = [
    "collected_at",
    "bus51_stop", "bus51_eta_min",
    "bus5100_stop", "bus5100_eta_min",
    "subway_stop", "subway_route",
    "subway_eta1_min", "subway_eta2_min", "subway_eta3_min",
    "destination_time", "recommended_departure_time",
    "bus_error", "subway_error", "engine_error",
]


def _as_str(x) -> str:
    return "" if x is None else str(x)


def main() -> int:
    p = argparse.ArgumentParser(description="Collect route snapshot into one CSV.")
    p.add_argument("--output", default="logs/day6_route_snapshot.csv")
    p.add_argument("--count", type=int, default=60)
    p.add_argument("--interval-sec", type=float, default=60.0)
    p.add_argument("--destination-time", default="10:00")
    args = p.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    bus51_stop = "206000043"     # 성남 이마트앞
    bus5100_stop = "203000075"   # 청명역 4번출구
    subway_stop = "미금"
    subway_route = "수인분당선"

    bus = GbisBusEtaProvider()
    subway = SuinBundangPositionEtaProvider(toward_station="청명")

    file_exists = out.exists()
    with out.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            w.writeheader()

        for i in range(args.count):
            now = datetime.now()

            bus_err = ""
            subway_err = ""
            engine_err = ""

            bus51_eta = None
            bus5100_eta = None
            sub_etas = []

            # 1) 버스 ETA
            try:
                bus51_eta = bus.get_eta_minutes(bus51_stop, "51")
                bus5100_eta = bus.get_eta_minutes(bus5100_stop, "5100")
            except Exception as e:
                bus_err = f"{type(e).__name__}: {e}"

            # 2) 지하철(next 3)
            try:
                sub_etas = subway.get_next_arrivals(subway_stop, max_results=3)
            except Exception as e:
                subway_err = f"{type(e).__name__}: {e}"
                sub_etas = []

            # 3) 엔진 출력(스냅샷 wait_provider로 1회 계산)
            dep = None
            try:
                wait_provider = build_wait_provider_snapshot(
                    now=now,
                    bus_provider=bus,
                    subway_provider=subway,
                    bus_stops=[(bus51_stop, "51"), (bus5100_stop, "5100")],
                    subway_stops=[(subway_stop, subway_route)],
                    max_wait_by_route={"51": 15, "5100": 25, "수인분당선": 10},
                )
                dep = compute_departure_time(
                    destination_time=args.destination_time,
                    segments=FIXED_ROUTE_SEGMENTS,
                    wait_provider=wait_provider,
                )
            except Exception as e:
                engine_err = f"{type(e).__name__}: {e}"

            row = {
                "collected_at": now.isoformat(timespec="seconds"),
                "bus51_stop": bus51_stop,
                "bus51_eta_min": _as_str(bus51_eta),
                "bus5100_stop": bus5100_stop,
                "bus5100_eta_min": _as_str(bus5100_eta),
                "subway_stop": subway_stop,
                "subway_route": subway_route,
                "subway_eta1_min": _as_str(sub_etas[0] if len(sub_etas) > 0 else None),
                "subway_eta2_min": _as_str(sub_etas[1] if len(sub_etas) > 1 else None),
                "subway_eta3_min": _as_str(sub_etas[2] if len(sub_etas) > 2 else None),
                "destination_time": args.destination_time,
                "recommended_departure_time": _as_str(dep),
                "bus_error": bus_err,
                "subway_error": subway_err,
                "engine_error": engine_err,
            }

            w.writerow(row)
            f.flush()

            if i < args.count - 1 and args.interval_sec > 0:
                time.sleep(args.interval_sec)

    print(f"Saved CSV: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
