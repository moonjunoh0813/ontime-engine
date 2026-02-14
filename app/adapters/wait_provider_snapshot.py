from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from app.adapters.gbis_bus_eta_provider import GbisBusEtaProvider
from app.adapters.suin_bundang_position_eta_provider import SuinBundangPositionEtaProvider

MINUTES_PER_DAY = 24 * 60
TIME_FMT = "%H:%M"


def _hhmm_to_minutes(s: str) -> int:
    t = datetime.strptime(s.strip(), TIME_FMT)
    return t.hour * 60 + t.minute


def _now_minutes(now: datetime) -> int:
    return now.hour * 60 + now.minute


def _delta_from_now(now_min: int, target_hhmm: str) -> int:
    target = _hhmm_to_minutes(target_hhmm)
    return (target - now_min) % MINUTES_PER_DAY


def _norm_stop(stop: str) -> str:
    s = stop.strip()
    if s.isdigit():
        return s
    if s.endswith("역"):
        s = s[:-1]
    return s.replace(" ", "")


WaitProvider = Callable[[str, str, str], int]


@dataclass(frozen=True)
class WaitSnapshot:
    now: datetime
    arrivals_after_now: dict[tuple[str, str], list[int]]  # key=(stop,route) -> [etaMin1, etaMin2,...]
    max_wait_by_route: dict[str, int]

    def wait(self, stop: str, route: str, time_hhmm: str) -> int:
        key = (_norm_stop(stop), route.strip())
        etas = self.arrivals_after_now.get(key, [])
        now_min = _now_minutes(self.now)
        delta = _delta_from_now(now_min, time_hhmm)

        # delta 시각에 도착했을 때, 아직 안 지난 열차(eta >= delta)가 있으면 그 차이가 wait
        candidates = [eta - delta for eta in etas if eta >= delta]
        if candidates:
            return min(candidates)

        # 없으면: 아직 배차/열차 정보를 모름(또는 운행 종료) -> 보수적으로 max_wait
        return self.max_wait_by_route.get(route.strip(), 0)


def build_wait_provider_snapshot(
    now: datetime,
    bus_provider: GbisBusEtaProvider | None,
    subway_provider: SuinBundangPositionEtaProvider | None,
    bus_stops: list[tuple[str, str]],
    subway_stops: list[tuple[str, str]],
    max_wait_by_route: dict[str, int],
) -> WaitProvider:
    arrivals: dict[tuple[str, str], list[int]] = {}

    # 버스: (정류장ID, 노선)별 "다음 도착" 1개만 스냅샷
    if bus_provider:
        for stop, route in bus_stops:
            eta = bus_provider.get_eta_minutes(stop, route)
            if eta is not None:
                arrivals[(_norm_stop(stop), route.strip())] = [int(eta)]

    # 지하철(수인분당선): 위치기반으로 next 3개까지 스냅샷
    if subway_provider:
        for stop, route in subway_stops:
            etas = subway_provider.get_next_arrivals(stop, max_results=3)
            if etas:
                arrivals[(_norm_stop(stop), route.strip())] = [int(x) for x in etas]

    snap = WaitSnapshot(now=now, arrivals_after_now=arrivals, max_wait_by_route=max_wait_by_route)
    return snap.wait
