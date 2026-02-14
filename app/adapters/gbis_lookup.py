import argparse
import os
from urllib.parse import unquote

import requests


STATION_SEARCH_URL = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2"


def _norm_key(k: str) -> str:
    k = k.strip()
    return unquote(k) if "%" in k else k


def main() -> int:
    parser = argparse.ArgumentParser(description="GBIS station lookup (keyword -> stationId list)")
    parser.add_argument("--keyword", required=True, help="정류소명/번호 키워드 (예: 이마트앞)")
    parser.add_argument("--service-key", default=None, help="data.go.kr serviceKey (없으면 env DATA_GO_KR_SERVICE_KEY)")
    parser.add_argument("--limit", type=int, default=10, help="출력 개수")
    args = parser.parse_args()

    key = args.service_key or os.environ.get("DATA_GO_KR_SERVICE_KEY")
    if not key:
        raise SystemExit("Missing service key. Set DATA_GO_KR_SERVICE_KEY or pass --service-key")
    key = _norm_key(key)

    params = {"serviceKey": key, "keyword": args.keyword, "format": "json"}
    r = requests.get(STATION_SEARCH_URL, params=params, timeout=10)
    if r.status_code != 200:
        # URL(키 포함) 대신 응답 내용만 일부 출력
        raise SystemExit(f"HTTP {r.status_code} from GBIS. Response: {r.text[:200]}")
    data = r.json()

    header = data.get("response", {}).get("msgHeader", {})
    result_code = int(header.get("resultCode", 0))
    if result_code != 0:
        raise SystemExit(f"GBIS error: {header}")

    body = data.get("response", {}).get("msgBody", {})
    stations = body.get("busStationList") or []
    if isinstance(stations, dict):
        stations = [stations]

    print(f"Found {len(stations)} stations for keyword={args.keyword!r}")
    for s in stations[: args.limit]:
        station_id = s.get("stationId")
        name = s.get("stationName")
        region = s.get("regionName")
        mobile_no = s.get("mobileNo")
        print(f"- stationId={station_id} | name={name} | region={region} | mobileNo={mobile_no}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
