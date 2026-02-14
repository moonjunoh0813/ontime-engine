from dataclasses import dataclass
from datetime import datetime
from typing import Callable

TIME_FMT = "%H:%M"
MINUTES_PER_DAY = 24 * 60


def parse_hhmm(s: str) -> datetime:
    s = s.strip()
    return datetime.strptime(s, TIME_FMT)


def sum_travel_minutes(segments: list[int]) -> int:
    """
    이동시간(분) 리스트를 받아 총 이동시간(분)을 반환한다.

    규칙:
    - 입력은 분 단위 리스트
    - 음수 값이 하나라도 있으면 ValueError
    - 순수 계산 함수 (datetime / 외부 API 사용 금지)
    """
    total = 0
    for minutes in segments:
        if minutes < 0:
            raise ValueError(f"Negative travel minutes not allowed: {minutes}")
        total += minutes
    return total


def minutes_to_hhmm(total_minutes: int) -> str:
    """
    분 단위 정수를 HH:MM 문자열로 변환한다.
    total_minutes는 음수여도 된다(자정 넘어감). => 24시간으로 감아서 표시.
    """
    m = total_minutes % MINUTES_PER_DAY
    h = m // 60
    mm = m % 60
    return f"{h:02d}:{mm:02d}"


def hhmm_to_minutes(s: str) -> int:
    """
    HH:MM 문자열을 0~1439 범위의 '분'으로 변환한다.
    Step1의 parse_hhmm를 재사용해서 포맷 검증을 맡긴다.
    """
    dt = parse_hhmm(s)
    return dt.hour * 60 + dt.minute


@dataclass(frozen=True)
class Move:
    minutes: int


@dataclass(frozen=True)
class Board:
    stop: str
    route: str


# stop, route, "HH:MM(정류장 도착 시각)" -> wait minutes
WaitProvider = Callable[[str, str, str], int]


# Day2: fixed route (draft)
FIXED_ROUTE_SEGMENTS: list[Move | Board] = [
    Move(0),  # 집 -> 이마트앞 정류장 (도보)
    Board(stop="206000043", route="51"), 
    Move(0),  # 51번 버스 탑승 후 미금역 정류장 도착
    Move(0),  # 미금역 정류장 -> 미금역 (도보)
    Board(stop="미금", route="수인분당선"),
    Move(0),  # 수인분당선 탑승 후 청명역 도착
    Move(0),  # 청명역 -> 청명역 정류장 (도보)
    Board(stop="203000075", route="5100"), 
    Move(0),  # 5100번 버스 탑승 후 경희대 정문 도착
    Move(0),  # 경희대 정문 -> 학교 (도보)
]


def _latest_stop_arrival_time(
    board_deadline_min: int,
    stop: str,
    route: str,
    wait_provider: WaitProvider,
    max_search_min: int,
) -> int:
    """
    조건:
      arrival_time + wait(arrival_time) <= board_deadline_min

    가장 '늦은 arrival_time'을 찾기 위해,
    board_deadline부터 1분씩 거꾸로 내려가며 wait_provider를 호출한다.
    """
    if max_search_min < 0:
        raise ValueError("max_search_min must be >= 0")

    for delta in range(0, max_search_min + 1):
        arrival = board_deadline_min - delta
        arrival_hhmm = minutes_to_hhmm(arrival)

        w = wait_provider(stop, route, arrival_hhmm)
        if w < 0:
            raise ValueError(f"wait_provider returned negative minutes: {w}")

        if arrival + w <= board_deadline_min:
            return arrival

    raise ValueError(
        f"No feasible stop arrival time found within {max_search_min} minutes "
        f"for stop={stop!r}, route={route!r}"
    )


def compute_departure_time(
    destination_time: str,
    segments: list[Move | Board],
    wait_provider: WaitProvider,
    transfer_buffer_min: int = 3,
    max_wait_search_min: int = 180,
) -> str:
    """
    목표 도착시간(destination_time)으로부터 출발 시각을 '역산'한다.

    규칙(절대):
    - segments는 forward(집->학교) 순서로 주되,
      엔진은 반드시 reversed(뒤->앞)로 처리한다.
    - MOVE: 이동시간(minutes)만큼 단순 차감
    - BOARD:
        1) board_deadline(현재 t) 이전에 탈 수 있도록 정류장 도착 시각을 찾는다
           (wait_provider를 사용)
        2) 그 도착 시각에서 transfer_buffer_min 만큼 추가로 차감한다
           (환승/여유 버퍼)
    """
    if transfer_buffer_min < 0:
        raise ValueError("transfer_buffer_min must be >= 0")

    t = hhmm_to_minutes(destination_time)

    for seg in reversed(segments):
        if isinstance(seg, Move):
            if seg.minutes < 0:
                raise ValueError(f"Negative travel minutes not allowed: {seg.minutes}")
            t -= seg.minutes

        elif isinstance(seg, Board):
            arrival_at_stop = _latest_stop_arrival_time(
                board_deadline_min=t,
                stop=seg.stop,
                route=seg.route,
                wait_provider=wait_provider,
                max_search_min=max_wait_search_min,
            )
            t = arrival_at_stop - transfer_buffer_min

        else:
            raise TypeError(f"Unknown segment type: {type(seg)!r}")

    return minutes_to_hhmm(t)
