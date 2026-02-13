import random
from app.adapters.eta_provider import EtaProvider


class DummyEtaProvider:
    """
    Day4용 더미 provider.
    - route별 기본 ETA를 주고, 약간의 랜덤 흔들림(jitter)을 준다.
    - Day5에 실제 API 붙이면 이 파일은 교체/삭제해도 됨.
    """
    name = "dummy"

    def __init__(self, seed: int = 0, missing_rate: float = 0.0):
        self._rng = random.Random(seed)
        self._missing_rate = missing_rate

    def get_eta_minutes(self, stop: str, route: str) -> int | None:
        # 가끔 데이터가 없다고 가정(누락률 시뮬레이션)
        if self._missing_rate > 0 and self._rng.random() < self._missing_rate:
            return None

        base = {
            "51": 8,
            "5100": 12,
            "수인분당선": 4,
        }.get(route)

        if base is None:
            return None

        jitter = self._rng.randint(-1, 1)  # -1,0,1
        return max(0, base + jitter)
