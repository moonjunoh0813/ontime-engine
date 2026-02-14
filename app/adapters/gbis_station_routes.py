import argparse
import os
from urllib.parse import unquote

import requests

URL = "https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationViaRouteListv2"


def _norm_key(k: str) -> str:
    k = k.strip()
    return unquote(k) if "%" in k else k


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def main() -> int:
    p = argparse.ArgumentParser(description="GBIS: list routes that pass a stationId")
    p.add_argument("--station-id", required=True)
    p.add_argument("--route", default="", help="Optional: check if routeName exists (e.g., 5100)")
    args = p.parse_args()

    key = os.environ.get("DATA_GO_KR_SERVICE_KEY")
    if not key:
        raise SystemExit("Missing DATA_GO_KR_SERVICE_KEY")
    key = _norm_key(key)

    r = requests.get(URL, params={"serviceKey": key, "stationId": args.station_id, "format": "json"}, timeout=10)
    if r.status_code != 200:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:200]}")

    data = r.json()
    header = data.get("response", {}).get("msgHeader", {})
    if int(header.get("resultCode", 0)) != 0:
        raise SystemExit(f"GBIS error: {header}")

    body = data.get("response", {}).get("msgBody", {}) or {}
    routes = _as_list(body.get("busRouteList"))
    names = sorted({str(x.get("routeName", "")).strip() for x in routes if x.get("routeName")})

    target = args.route.strip()
    if target:
        print(f"stationId={args.station_id} has route {target}? -> {target in names}")

    print("routes (sample):", ", ".join(names[:50]))
    if len(names) > 50:
        print(f"... (+{len(names)-50} more)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
