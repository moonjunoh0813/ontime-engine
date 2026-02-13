import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

from app.adapters.eta_provider import EtaQuery, EtaSample, EtaProvider
from app.adapters.dummy_eta_provider import DummyEtaProvider


CSV_FIELDS = ["collected_at", "stop", "route", "eta_min", "provider", "error"]


def collect_once(provider: EtaProvider, query: EtaQuery) -> EtaSample:
    now = datetime.now()
    try:
        eta = provider.get_eta_minutes(query.stop, query.route)
        if eta is not None and eta < 0:
            raise ValueError(f"eta_min must be >= 0, got {eta}")
        return EtaSample(
            collected_at=now,
            stop=query.stop,
            route=query.route,
            eta_min=eta,
            provider=provider.name,
            error=None,
        )
    except Exception as e:
        return EtaSample(
            collected_at=now,
            stop=query.stop,
            route=query.route,
            eta_min=None,
            provider=provider.name,
            error=f"{type(e).__name__}: {e}",
        )


def write_samples_csv(path: Path, samples: list[EtaSample], append: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()
    mode = "a" if append else "w"

    # Excel 호환을 위해 utf-8-sig 사용
    with path.open(mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not (append and file_exists):
            writer.writeheader()

        for s in samples:
            writer.writerow(
                {
                    "collected_at": s.collected_at.isoformat(timespec="seconds"),
                    "stop": s.stop,
                    "route": s.route,
                    "eta_min": "" if s.eta_min is None else s.eta_min,
                    "provider": s.provider,
                    "error": "" if s.error is None else s.error,
                }
            )
        f.flush()


def parse_targets(targets: list[str]) -> list[EtaQuery]:
    """
    --target "이마트앞,51" 형태를 파싱한다.
    """
    queries: list[EtaQuery] = []
    for t in targets:
        parts = [p.strip() for p in t.split(",", maxsplit=1)]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"Invalid --target format: {t!r}. Use \"STOP,ROUTE\".")
        queries.append(EtaQuery(stop=parts[0], route=parts[1]))
    return queries


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect ETA samples and write CSV.")
    parser.add_argument("--output", default="logs/eta_samples.csv", help="CSV output path")
    parser.add_argument("--count", type=int, default=10, help="How many rounds to collect")
    parser.add_argument("--interval-sec", type=float, default=60.0, help="Sleep between rounds")
    parser.add_argument(
        "--target",
        action="append",
        help="Repeatable. Format: \"STOP,ROUTE\"  (e.g., \"이마트앞,51\")",
    )
    parser.add_argument("--seed", type=int, default=0, help="Dummy provider random seed")
    parser.add_argument("--missing-rate", type=float, default=0.0, help="Dummy missing rate 0~1")

    args = parser.parse_args()

    if args.count <= 0:
        raise ValueError("--count must be > 0")
    if args.interval_sec < 0:
        raise ValueError("--interval-sec must be >= 0")

    # 기본 타겟(고정 경로 기반)
    if args.target:
        queries = parse_targets(args.target)
    else:
        queries = [
            EtaQuery(stop="이마트앞", route="51"),
            EtaQuery(stop="청명역 정류장", route="5100"),
            EtaQuery(stop="미금역", route="수인분당선"),
        ]

    provider: EtaProvider = DummyEtaProvider(seed=args.seed, missing_rate=args.missing_rate)
    out_path = Path(args.output)

    for i in range(args.count):
        batch: list[EtaSample] = []
        for q in queries:
            batch.append(collect_once(provider, q))

        write_samples_csv(out_path, batch, append=True)

        if i < args.count - 1 and args.interval_sec > 0:
            time.sleep(args.interval_sec)

    print(f"Saved CSV: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
