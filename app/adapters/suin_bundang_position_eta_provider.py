import math
import os
import re
from datetime import datetime
from urllib.parse import quote

import requests


def _norm_station(name: str) -> str:
    s = (name or "").strip()
    if s.endswith("역"):
        s = s[:-1]
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"\s+", "", s)
    return s


def _parse_dt(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


# 수인분당선(왕십리 -> 인천) 역 순서(ETA 추정용)
SUIN_BUNDANG_ORDER = [
    "왕십리","서울숲","압구정로데오","강남구청","선정릉","선릉","한티","도곡","구룡",
    "개포동","대모산입구","수서","복정","가천대","태평","모란","야탑","이매",
    "서현","수내","정자","미금","오리","죽전","보정","구성","신갈","기흥",
    "상갈","청명","영통","망포","매탄권선","수원시청","매교","수원","고색",
    "오목천","어천","야목","사리","한대앞","중앙","고잔","초지","안산",
    "신길온천","정왕","오이도","달월","월곶","소래포구","인천논현","호구포",
    "남동인더스파크","원인재","연수","송도","인하대","숭의","신포","인천",
]
_IDX = {_norm_station(n): i for i, n in enumerate(SUIN_BUNDANG_ORDER)}


class SuinBundangPositionEtaProvider:
    """
    서울 realtimePosition(열차 위치)로 '특정 역까지 다음 열차 도착(분)'을 추정한다.
    - 정확한 ETA API가 없을 때 쓰는 우회로(추정치)
    """
    name = "seoul_subway_pos"

    def __init__(
        self,
        api_key: str | None = None,
        line_name: str = "수인분당선",
        toward_station: str = "청명",
        per_station_min: float = 2.0,
        dwell_min: float = 0.5,
        limit: int = 500,
        timeout_sec: int = 10,
        cache_ttl_sec: int = 20,
    ):
        key = api_key or os.environ.get("SEOUL_OPENAPI_KEY")
        if not key:
            raise ValueError("Missing SEOUL_OPENAPI_KEY")
        self._key = key.strip()
        self._line = line_name
        self._toward_idx = _IDX.get(_norm_station(toward_station))
        if self._toward_idx is None:
            raise ValueError(f"Unknown toward_station: {toward_station!r}")

        self._per_station = per_station_min
        self._dwell = dwell_min
        self._limit = limit
        self._timeout = timeout_sec
        self._ttl = cache_ttl_sec
        self._cache_at = 0.0
        self._cache_rows: list[dict] = []

    def _fetch_rows(self) -> list[dict]:
        now_ts = datetime.now().timestamp()
        if self._cache_rows and (now_ts - self._cache_at) <= self._ttl:
            return self._cache_rows

        url = (
            f"http://swopenAPI.seoul.go.kr/api/subway/{self._key}/json/"
            f"realtimePosition/0/{self._limit}/{quote(self._line)}"
        )
        r = requests.get(url, timeout=self._timeout)
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code} from realtimePosition: {r.text[:200]}")

        data = r.json()
        err = data.get("errorMessage") or {}
        if int(err.get("status", 200)) != 200:
            raise ValueError(f"Seoul realtimePosition API error: {err}")

        rows = data.get("realtimePositionList") or []
        self._cache_rows = rows
        self._cache_at = now_ts
        return rows

    def get_next_arrivals(self, stop: str, max_results: int = 3) -> list[int]:
        target = _norm_station(stop)
        t_idx = _IDX.get(target)
        if t_idx is None:
            return []

        now = datetime.now()
        rows = self._fetch_rows()

        etas: list[int] = []

        for x in rows:
            cur = _norm_station(x.get("statnNm", ""))
            cur_idx = _IDX.get(cur)
            if cur_idx is None:
                continue

            term = _norm_station(x.get("statnTnm", ""))  # 종착역
            term_idx = _IDX.get(term)
            if term_idx is None:
                continue

            # forward(왕십리->인천) 방향만, 그리고 청명까지 가는 열차만
            forward = term_idx >= cur_idx
            if not forward or term_idx < self._toward_idx:
                continue

            # 아직 target을 지나치지 않은 열차만
            if cur_idx > t_idx:
                continue

            steps = t_idx - cur_idx

            recpt = _parse_dt(x.get("recptnDt") or x.get("lastRecptnDt") or "")
            age_min = 0.0
            if recpt:
                age_min = max(0.0, (now - recpt).total_seconds() / 60.0)

            eta = steps * self._per_station + self._dwell
            eta = max(0.0, eta - age_min)

            etas.append(int(math.ceil(eta)))

        etas = sorted(set(etas))
        return etas[:max_results]

    def get_eta_minutes(self, stop: str, route: str) -> int | None:
        arr = self.get_next_arrivals(stop, max_results=1)
        return arr[0] if arr else None
