import os
from urllib.parse import unquote

import requests

from app.adapters.eta_provider import EtaProvider


ARRIVAL_LIST_URL = "https://apis.data.go.kr/6410000/busarrivalservice/v2/getBusArrivalListv2"
STATION_SEARCH_URL = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2"


def _norm_key(k: str) -> str:
    k = k.strip()
    return unquote(k) if "%" in k else k


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


class GbisBusEtaProvider:
    """
    GBIS(경기버스정보) 버스 ETA provider.
    - stop: stationId(권장) 또는 정류소명(모호하면 에러)
    - route: 버스 번호 문자열 (예: "51", "5100")
    """
    name = "gbis_bus"

    def __init__(self, service_key: str | None = None, timeout_sec: int = 10):
        key = service_key or os.environ.get("DATA_GO_KR_SERVICE_KEY")
        if not key:
            raise ValueError("Missing DATA_GO_KR_SERVICE_KEY (or pass service_key)")
        self._service_key = _norm_key(key)
        self._timeout = timeout_sec

    def _get_json(self, url: str, params: dict) -> dict:
        r = requests.get(url, params=params, timeout=self._timeout)
        r.raise_for_status()
        return r.json()

    def _ensure_ok(self, data: dict) -> dict:
        header = data.get("response", {}).get("msgHeader", {})
        code = int(header.get("resultCode", 0))
        if code != 0:
            raise ValueError(f"GBIS error: {header}")
        return data.get("response", {}).get("msgBody", {}) or {}

    def _resolve_station_id(self, keyword: str) -> str:
        params = {"serviceKey": self._service_key, "keyword": keyword, "format": "json"}
        data = self._get_json(STATION_SEARCH_URL, params)
        body = self._ensure_ok(data)
        stations = _as_list(body.get("busStationList"))

        if not stations:
            raise ValueError(f"No station found for keyword={keyword!r}")

        # 1개면 자동 선택
        if len(stations) == 1:
            return str(stations[0].get("stationId"))

        # 여러 개면 “선택”이 필요하므로, 후보를 보여주고 에러로 멈춘다
        lines = []
        for s in stations[:10]:
            lines.append(
                f"stationId={s.get('stationId')} name={s.get('stationName')} "
                f"region={s.get('regionName')} mobileNo={s.get('mobileNo')}"
            )
        raise ValueError(
            "Ambiguous station keyword. Use stationId directly.\n" + "\n".join(lines)
        )

    def get_eta_minutes(self, stop: str, route: str) -> int | None:
        station_id = stop.strip()
        if not station_id.isdigit():
            station_id = self._resolve_station_id(station_id)

        params = {"serviceKey": self._service_key, "stationId": station_id, "format": "json"}
        data = self._get_json(ARRIVAL_LIST_URL, params)
        body = self._ensure_ok(data)

        arrivals = _as_list(body.get("busArrivalList"))
        if not arrivals:
            return None

        # routeName이 "51"처럼 들어오는 항목을 찾는다
        candidates = []
        for a in arrivals:
            if str(a.get("routeName", "")).strip() != route.strip():
                continue

            t1 = a.get("predictTime1")
            t2 = a.get("predictTime2")

            for t in (t1, t2):
                try:
                    tt = int(t)
                    if tt >= 0:
                        candidates.append(tt)
                except Exception:
                    pass

        if not candidates:
            return None

        return min(candidates)
