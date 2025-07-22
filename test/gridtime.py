# test/test_time_units.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timedelta
import gridtime as gt

def test_valid_quarter():
    dt = datetime(2025, 3, 30, 1, 0)
    q = gt.QuarterHour(dt)
    assert q.start_time == dt
    assert q.end_time == dt + timedelta(minutes=15)

def test_missing_quarter():
    dt = datetime(2025, 3, 30, 2, 0)
    with pytest.raises(ValueError):
        gt.QuarterHour(dt)

def test_duplicated_hour_true():
    dt = datetime(2025, 10, 26, 2, 0)
    assert gt.is_duplicated_hour(dt) is True

def test_duplicated_hour_false_day_after():
    dt = datetime(2025, 10, 27, 2, 0)
    assert gt.is_duplicated_hour(dt) is False

def test_duplicated_quarter_true():
    dt = datetime(2025, 10, 26, 2, 30)
    assert gt.is_duplicated_quarter(dt) is True

def test_duplicated_quarter_false():
    dt = datetime(2025, 10, 26, 3, 0)
    assert gt.is_duplicated_quarter(dt) is False

def test_days_in_february_leap_year():
    days = gt.create_days(2024, 2)
    assert len(days) == 29, "Luty 2024 powinien mieć 29 dni"

def test_days_in_february_non_leap_year():
    days = gt.create_days(2023, 2)
    assert len(days) == 28, "Luty 2023 powinien mieć 28 dni"

def test_days_in_january():
    days = gt.create_days(2025, 1)
    assert len(days) == 31, "Styczeń 2025 powinien mieć 31 dni"

def test_days_in_april():
    days = gt.create_days(2025, 4)
    assert len(days) == 30, "Kwiecień 2025 powinien mieć 30 dni"

def test_days_in_october():
    days = gt.create_days(2025, 10)
    assert len(days) == 31, "Październik 2025 powinien mieć 31 dni"

def test_count_hours_in_2025():
    year = gt.Year(2025)
    assert year.count("hours")  == 8760

def test_count_hours_in_2024():
    year = gt.Year(2024)
    assert year.count("hours")  == 8784

def test_hours_in_october():
    month = gt.Month(2025, 10)
    assert month.count("hours") == 745, "Październik 2025 powinien mieć 745 dni. 31 dni * 24 godziny + 1 godzina (cofnięta) = 745 godzin"

def test_hours_in_march():
    month = gt.Month(2025, 3)
    assert month.count("hours") == 743, "Marzec 2025 powinien mieć 743 dni. 31 dni * 24 godziny - 1 godzina (cofnięta) = 743 godzin"