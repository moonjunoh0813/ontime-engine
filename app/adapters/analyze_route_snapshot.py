import argparse
import csv
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MINUTES_PER_DAY = 24 * 60


def _to_int(s: str):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return int(s)
    except Exception:
        return None


def _to_hhmm_minutes(s: str):
    s = (s or "").strip()
    if s == "":
        return None
    try:
        t = datetime.strptime(s, "%H:%M")
        return t.hour * 60 + t.minute
    except Exception:
        return None


def _circular_diff_min(a: int, b: int) -> int:
    d = (a - b) % MINUTES_PER_DAY
    return min(d, MINUTES_PER_DAY - d)


@dataclass
class SeriesStats:
    name: str
    n: int
    missing: int
    change_events: int
    change_rate: float
    change_interval_median_sec: float | None
    jump_max: int | None
    jumps_ge_2: int
    jumps_ge_5: int


def compute_series_stats(name: str, times: list[datetime], values: list[int | None], circular: bool = False) -> SeriesStats:
    n = len(values)
    missing = sum(1 for v in values if v is None)

    change_times: list[datetime] = []
    for i in range(1, n):
        if values[i] != values[i - 1]:
            change_times.append(times[i])

    change_events = len(change_times)
    change_rate = (change_events / (n - 1)) if n > 1 else 0.0

    change_interval_median_sec = None
    if len(change_times) >= 2:
        intervals = [(change_times[i] - change_times[i - 1]).total_seconds() for i in range(1, len(change_times))]
        change_interval_median_sec = float(statistics.median(intervals))

    jumps = []
    for i in range(1, n):
        a = values[i]
        b = values[i - 1]
        if a is None or b is None:
            continue
        if circular:
            jumps.append(_circular_diff_min(a, b))
        else:
            jumps.append(abs(a - b))

    jump_max = max(jumps) if jumps else None
    jumps_ge_2 = sum(1 for j in jumps if j >= 2)
    jumps_ge_5 = sum(1 for j in jumps if j >= 5)

    return SeriesStats(
        name=name,
        n=n,
        missing=missing,
        change_events=change_events,
        change_rate=change_rate,
        change_interval_median_sec=change_interval_median_sec,
        jump_max=jump_max,
        jumps_ge_2=jumps_ge_2,
        jumps_ge_5=jumps_ge_5,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze day6_route_snapshot.csv")
    p.add_argument("--input", default="logs/day6_route_snapshot.csv")
    args = p.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise SystemExit("No rows in CSV")

    times = [datetime.fromisoformat(r["collected_at"]) for r in rows]
    n = len(times)

    intervals = [(times[i] - times[i - 1]).total_seconds() for i in range(1, n)]
    med_dt = statistics.median(intervals) if intervals else 0
    min_dt = min(intervals) if intervals else 0
    max_dt = max(intervals) if intervals else 0

    print(f"File: {path}")
    print(f"Rows: {n}")
    print(f"Time range: {times[0]}  ->  {times[-1]}")
    print(f"Sampling interval (sec): median={med_dt:.1f}, min={min_dt:.1f}, max={max_dt:.1f}")
    print()

    bus51 = [_to_int(r.get("bus51_eta_min", "")) for r in rows]
    bus5100 = [_to_int(r.get("bus5100_eta_min", "")) for r in rows]
    sub1 = [_to_int(r.get("subway_eta1_min", "")) for r in rows]
    dep = [_to_hhmm_minutes(r.get("recommended_departure_time", "")) for r in rows]

    bus_err = sum(1 for r in rows if (r.get("bus_error") or "").strip() != "")
    sub_err = sum(1 for r in rows if (r.get("subway_error") or "").strip() != "")
    eng_err = sum(1 for r in rows if (r.get("engine_error") or "").strip() != "")

    print(f"Errors: bus_error={bus_err}/{n}, subway_error={sub_err}/{n}, engine_error={eng_err}/{n}")
    print()

    stats = [
        compute_series_stats("bus51_eta_min", times, bus51),
        compute_series_stats("bus5100_eta_min", times, bus5100),
        compute_series_stats("subway_eta1_min", times, sub1),
        compute_series_stats("recommended_departure_time(min)", times, dep, circular=True),
    ]

    for s in stats:
        miss_pct = (s.missing / s.n) * 100.0
        print(f"[{s.name}]")
        print(f"  missing: {s.missing}/{s.n} ({miss_pct:.1f}%)")
        print(f"  change events: {s.change_events}  (change_rate={s.change_rate:.2f} per sample)")
        if s.change_interval_median_sec is None:
            print("  change interval median: (not enough changes)")
        else:
            print(f"  change interval median: {s.change_interval_median_sec:.1f} sec")
        print(f"  jump max: {s.jump_max if s.jump_max is not None else '(no jumps)'} min")
        print(f"  jumps >=2min: {s.jumps_ge_2}, jumps >=5min: {s.jumps_ge_5}")
        print()

    dep_vals = [v for v in dep if v is not None]
    if dep_vals:
        lo = min(dep_vals)
        hi = max(dep_vals)
        lo_hh = f"{lo//60:02d}:{lo%60:02d}"
        hi_hh = f"{hi//60:02d}:{hi%60:02d}"
        print(f"Departure range: {lo_hh} ~ {hi_hh} (span={_circular_diff_min(hi, lo)} min)")
    else:
        print("Departure range: (no departure values)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
