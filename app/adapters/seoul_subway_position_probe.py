import os
from urllib.parse import quote

import requests

URL_FMT = "http://swopenAPI.seoul.go.kr/api/subway/{key}/json/realtimePosition/0/500/{line}"


def main() -> int:
    key = os.environ.get("SEOUL_OPENAPI_KEY", "").strip()
    if not key:
        raise SystemExit("Missing SEOUL_OPENAPI_KEY")

    line = "수인분당선"
    url = URL_FMT.format(key=key, line=quote(line))

    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    rows = data.get("realtimePositionList") or []
    stations = sorted({(x.get("statnNm") or "").strip() for x in rows if x.get("statnNm")})

    print("line:", line)
    print("train_count:", len(rows))
    print("has_migeum:", ("미금" in stations))
    print("has_cheongmyeong:", ("청명" in stations))
    print("sample_stations:", stations[:30])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
