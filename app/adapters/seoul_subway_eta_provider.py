import os
from urllib.parse import quote

import requests


class SeoulSubwayEtaProvider:
    name = "seoul_subway"

    LINE_ID_BY_ROUTE = {
        "수인분당선": "1075",
        "수의분당선": "1075",
        "분당선": "1075",
        "신분당선": "1077",
    }

    def __init__(self, api_key: str | None = None, limit: int = 20, timeout_sec: int = 10):
        key = api_key or os.environ.get("SEOUL_OPENAPI_KEY")
        if not key:
            raise ValueError("Missing SEOUL_OPENAPI_KEY (or pass api_key)")
        self._key = key.strip()
        self._limit = limit
        self._timeout = timeout_sec

    def get_eta_minutes(self, stop: str, route: str) -> int | None:
        statn = stop.strip()
        if statn.endswith("역"):
            statn = statn[:-1]

        url = (
            f"http://swopenAPI.seoul.go.kr/api/subway/{self._key}/json/"
            f"realtimeStationArrival/0/{self._limit}/{quote(statn)}"
        )

        r = requests.get(url, timeout=self._timeout)
        if r.status_code != 200:
            # 키가 URL에 포함되므로 url은 출력하지 않는다.
            raise ValueError(f"HTTP {r.status_code} from seoul subway API: {r.text[:200]}")

        data = r.json()
        err = data.get("errorMessage") or {}
        status = int(err.get("status", 200))
        if status != 200:
            raise ValueError(f"Seoul subway API error: {err}")

        rows = data.get("realtimeArrivalList") or []
        if not rows:
            return None

        route = (route or "").strip()
        if route:
            wanted_id = self.LINE_ID_BY_ROUTE.get(route)
            if wanted_id:
                rows = [x for x in rows if str(x.get("subwayId", "")).strip() == wanted_id]
            else:
                rows = [x for x in rows if route in str(x.get("trainLineNm", ""))]

        minutes_list: list[int] = []
        for x in rows:
            try:
                sec = int(x.get("barvlDt") or 0)
            except Exception:
                sec = 0
            if sec <= 0:
                continue
            minutes_list.append((sec + 59) // 60)

        return min(minutes_list) if minutes_list else None
