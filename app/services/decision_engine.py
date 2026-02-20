from dataclasses import dataclass
from datetime import datetime
from typing import Callable

TIME_FMT = "%H:%M"
MINUTES_PER_DAY = 24 * 60


def parse_hhmm(s: str) -> datetime:
    s = s.strip()
    return datetime.strptime(s, TIME_FMT)


def minutes_to_hhmm(total_minutes: int) -> str:
    m = total_minutes % MINUTES_PER_DAY
    h = m // 60
    mm = m % 60
    return f"{h:02d}:{mm:02d}"


def hhmm_to_minutes(s: str) -> int:
    dt = parse_hhmm(s)
    return dt.hour * 60 + dt.minute


@dataclass(frozen=True)
class Move:
    minutes: int


@dataclass(frozen=True)
class Board:
    stop: str
    route: str


WaitProvider = Callable[[str, str, str], int]


# Forward order (home -> school) for current MVP fixed route.
# Values align with the route diagram currently shown in frontend.
FIXED_ROUTE_SEGMENTS: list[Move | Board] = [
    Move(8),
    Board(stop="migeum_station", route="subway_suin"),
    Move(22),
    Move(10),
    Board(stop="stop_b", route="bus_5100"),
    Move(15),
    Move(5),
    Board(stop="stop_c", route="bus_51"),
    Move(15),
    Move(5),
]


def _latest_stop_arrival_time(
    board_deadline_min: int,
    stop: str,
    route: str,
    wait_provider: WaitProvider,
    max_search_min: int,
) -> int:
    if max_search_min < 0:
        raise ValueError("max_search_min must be >= 0")

    for delta in range(0, max_search_min + 1):
        arrival = board_deadline_min - delta
        arrival_hhmm = minutes_to_hhmm(arrival)

        wait_minutes = wait_provider(stop, route, arrival_hhmm)
        if wait_minutes < 0:
            raise ValueError(
                f"wait_provider returned negative minutes: {wait_minutes}"
            )

        if arrival + wait_minutes <= board_deadline_min:
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
    if transfer_buffer_min < 0:
        raise ValueError("transfer_buffer_min must be >= 0")

    t = hhmm_to_minutes(destination_time)

    for seg in reversed(segments):
        if isinstance(seg, Move):
            if seg.minutes < 0:
                raise ValueError(
                    f"Negative travel minutes not allowed: {seg.minutes}"
                )
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
