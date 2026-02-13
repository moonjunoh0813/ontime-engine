from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class EtaQuery:
    """
    '어느 정류장/어느 노선'의 ETA를 수집할지 지정하는 입력.
    """
    stop: str
    route: str


@dataclass(frozen=True)
class EtaSample:
    """
    수집된 한 줄 로그(= CSV 한 행).
    """
    collected_at: datetime
    stop: str
    route: str
    eta_min: int | None          # None이면 ETA를 못 얻은 것
    provider: str               # 어떤 provider(더미/실제API)에서 왔는지
    error: str | None = None    # 예외/오류가 있으면 기록


class EtaProvider(Protocol):
    """
    교통 ETA를 제공하는 어댑터 인터페이스.
    Day5에 실제 버스/지하철 API를 붙이면, 이 인터페이스를 구현하면 된다.
    """
    name: str

    def get_eta_minutes(self, stop: str, route: str) -> int | None:
        """
        '지금 시각 기준'으로 ETA(분)를 반환.
        - 정상: 0 이상의 int
        - 데이터 없음: None
        - 치명적 오류: 예외 발생(collector가 잡아서 CSV에 error로 기록)
        """
        ...
