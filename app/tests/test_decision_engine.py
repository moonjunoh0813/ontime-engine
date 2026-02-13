import pytest
from app.services.decision_engine import (
    Board,
    Move,
    compute_departure_time,
    sum_travel_minutes,
)

# ---- Step2 tests ----
def test_sum_travel_minutes_normal():
    assert sum_travel_minutes([5, 10, 15]) == 30

def test_sum_travel_minutes_empty():
    assert sum_travel_minutes([]) == 0

def test_sum_travel_minutes_negative_raises():
    with pytest.raises(ValueError):
        sum_travel_minutes([5, -3, 10])

# ---- Step4/5 tests (reverse engine) ----
def test_compute_departure_time_moves_only():
    def never_called(*args, **kwargs):
        raise AssertionError("wait_provider should not be called")

    segments = [Move(10), Move(20)]
    assert compute_departure_time("10:00", segments, never_called) == "09:30"

def test_compute_departure_time_with_board_constant_wait():
    def wait_provider(stop: str, route: str, time_hhmm: str) -> int:
        return 7  # 언제 도착하든 7분 대기

    segments = [
        Move(5),
        Board(stop="이마트앞", route="51"),
        Move(20),
        Move(10),
    ]

    # 10:00 -10 -20 = 09:30 (탑승 마감)
    # arrival + 7 <= 09:30 => 가장 늦은 arrival 09:23
    # 버퍼 3분 차감 => 09:20
    # 도보 5분 차감 => 09:15
    assert compute_departure_time("10:00", segments, wait_provider, transfer_buffer_min=3) == "09:15"

def test_compute_departure_time_midnight_wrap():
    def never_called(*args, **kwargs):
        raise AssertionError("wait_provider should not be called")

    segments = [Move(30)]
    assert compute_departure_time("00:10", segments, never_called) == "23:40"

def test_compute_departure_time_wait_provider_negative_raises():
    def wait_provider(stop: str, route: str, time_hhmm: str) -> int:
        return -1

    with pytest.raises(ValueError):
        compute_departure_time("10:00", [Board(stop="X", route="51")], wait_provider)

def test_compute_departure_time_no_feasible_arrival_raises():
    def wait_provider(stop: str, route: str, time_hhmm: str) -> int:
        return 9999  # 어떤 시각에 도착해도 말도 안 되게 오래 기다린다고 가정

    with pytest.raises(ValueError):
        compute_departure_time(
            "10:00",
            [Board(stop="X", route="51")],
            wait_provider,
            max_wait_search_min=5,  # 5분만 뒤로 탐색
        )
