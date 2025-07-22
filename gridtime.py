# time_units.py
from datetime import datetime, timedelta, date, time
from calendar import monthrange
from abc import ABC, abstractmethod
from typing import List, Iterator
from utils import _GRIDTIME_REGISTRY, register_unit, _all_unit_keys, _is_reachable, is_duplicated_hour, is_duplicated_quarter, is_missing_hour, is_missing_quarter
from collections.abc import Sequence


class GridtimeLeaf(ABC):
    def _structure_name(self) -> str:
        return self.__class__.__name__

    def unit_key(self) -> str:
        return _GRIDTIME_REGISTRY[self.__class__]["unit_key"]

    @abstractmethod
    def __repr__(self) -> str:
        pass

    def _iter_children(self) -> Iterator["GridtimeLeaf"]:
        return iter(())

    def children_key(self) -> str | None:
        return _GRIDTIME_REGISTRY[self.__class__].get("children_key")

    def _validate_unit(self, unit: str) -> None:
        if unit not in _all_unit_keys():
            raise ValueError(
                f"Nieznana jednostka '{unit}'. Dostępne: {sorted(_all_unit_keys())}"
            )
        if not _is_reachable(self.__class__, unit):
            raise ValueError(
                f"Jednostka '{unit}' nie występuje w gałęzi drzewa z korzeniem "
                f"{self._structure_name()} ('{self.unit_key()}')."
            )
        
    def __iter__(self) -> Iterator["GridtimeLeaf"]:
        return self._iter_children()

    def __len__(self) -> int:
        return sum(1 for _ in self._iter_children())

    def __contains__(self, other: object) -> bool:
        if not isinstance(other, GridtimeLeaf):
            return False
        return any(node == other for node in self.walk(other.unit_key()))
    
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and getattr(self, "start_time", None) == getattr(other, "start_time", None)
            and getattr(self, "end_time", None)   == getattr(other, "end_time", None)
        )

    def __hash__(self) -> int:
        return hash((self.__class__, getattr(self, "start_time", None), getattr(self, "end_time", None)))

    def count(self, unit: str) -> int:
        self._validate_unit(unit)
        if self.unit_key() == unit:
            return 1
        if self.children_key() is None:
            return 0
        return sum(child.count(unit) for child in self._iter_children())

    def get(self, unit: str) -> List["GridtimeLeaf"]:
        self._validate_unit(unit)
        if self.unit_key() == unit:
            return [self]
        if self.children_key() is None:
            return []
        out: List["GridtimeLeaf"] = []
        for child in self._iter_children():
            out.extend(child.get(unit))
        return out

    def walk(self, unit: str) -> Iterator["GridtimeLeaf"]:
        self._validate_unit(unit)
        if self.unit_key() == unit:
            yield self
        elif self.children_key() is not None:
            for child in self._iter_children():
                yield from child.walk(unit)

    def tree(
        self,
        unit_stop: str | None = None,
        show_root: bool = True,
        _prefix: str = "",
        _is_last: bool = True,
    ) -> str:
        lines: list[str] = []
        if show_root:
            connector = "└── " if _is_last else "├── "
            lines.append(f"{_prefix}{connector}{repr(self)}")
            _prefix += "    " if _is_last else "│   "

        if (unit_stop is not None and self.unit_key() == unit_stop) \
           or self.children_key() is None:
            return "\n".join(lines)

        children = list(self._iter_children())
        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            lines.append(child.tree(unit_stop, True, _prefix, is_last))
        return "\n".join(lines)


    def print_tree(self, **kwargs): 
        print(self.tree(**kwargs))

class GridtimeStructure(GridtimeLeaf):
    def __init__(self):
        self._children: Sequence[GridtimeLeaf] | None = None

    @abstractmethod
    def _create_children(self) -> list[GridtimeLeaf]:
        ...

    def _iter_children(self) -> Iterator[GridtimeLeaf]:
        if self._children is None:
            self._children = self._create_children()
        return iter(self._children)
    
@register_unit("quarters15")
class QuarterHour(GridtimeLeaf):
    def __init__(self, start_time: datetime, *, is_backward: bool = False):
        super().__init__()
        self.start_time = start_time
        self.end_time = start_time + timedelta(minutes=15)

        if is_missing_quarter(self.start_time):
            raise ValueError(
                f"Nie można utworzyć kwadransu dla {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}")
        
        self.is_duplicated: bool = is_duplicated_quarter(self.start_time)
        self.is_backward:   bool = is_backward

        if self.is_backward and not self.is_duplicated:
            raise ValueError(
                f"Kwadrans {self.start_time:%Y-%m-%d %H:%M} nie jest duplikowany, "
                f"nie można utworzyć 'cofniętej' instancji (is_backward=True)."
            )
        
    def __repr__(self):
        base = f"{self.start_time:%Y-%m-%d %H:%M}-{self.end_time:%H:%M}"
        if self.is_duplicated:
            tag = "↓2nd" if self.is_backward else "↑1st"
            return f"{base} [{tag}]"
        return base

@register_unit("hours", children_key="quarters15")
class Hour(GridtimeStructure):
    def __init__(self, reference_time: datetime, *, is_backward: bool = False):
        super().__init__()
        self.end_time = reference_time
        self.start_time = self.end_time - timedelta(hours=1)

        if is_missing_hour(self.start_time):
            raise ValueError(f"Nie można utworzyć godziny dla {reference_time.strftime('%Y-%m-%d %H:%M')}")
        
        self.is_duplicated: bool = is_duplicated_hour(self.start_time)
        self.is_backward:   bool = is_backward

        if self.is_backward and not self.is_duplicated:
            raise ValueError(
                f"Godzina {self.start_time:%Y-%m-%d %H:%M}-{self.end_time:%H:%M} "
                f"nie jest duplikowana, nie można utworzyć 'cofniętej' instancji "
                f"(is_backward=True)."
            )
        
        self._children = self._create_children()
        
    def _create_children(self) -> list[GridtimeLeaf]:
        return create_quarter_hours(self.start_time) # type: ignore
    
    def strftime(self, format: str) -> str:
        return self.start_time.strftime(format)
    
    def __repr__(self):
        base = f"{self.start_time:%Y-%m-%d %H:%M}-{self.end_time:%H:%M}"
        if self.is_duplicated:
            tag = "↓2nd" if self.is_backward else "↑1st"
            return f"{base} [{tag}]"
        return base

@register_unit("days", children_key="hours")
class Day(GridtimeStructure):
    def __init__(self, day_date: date):
        super().__init__()
        self.date = day_date
        self._children = self._create_children()
        self.hours = self._create_children()

    def _create_children(self) -> list[GridtimeLeaf]:
        return create_hours(self.date) # type: ignore
    
    def strftime(self, format: str) -> str:
        return self.date.strftime(format)
    
    def __repr__(self):
        return f"{self.date.strftime('%Y-%m-%d')}"
        
@register_unit("months", children_key="days")
class Month(GridtimeStructure):
    def __init__(self, year: int, month: int):
        super().__init__()
        self.year = year
        self.month = month
        self._children = self._create_children()

    def _create_children(self) -> list[GridtimeLeaf]:
        return create_days(self.year, self.month) # type: ignore
    
    def __repr__(self):
        return f"{self.year}-{self.month:02}"

@register_unit("quarters", children_key="months")  
class Quarter(GridtimeStructure):
    def __init__(self, year: int, quarter: int):
        super().__init__()
        if quarter not in (1, 2, 3, 4):
            raise ValueError("Kwartał musi być liczbą 1–4")
        self.year = year
        self.quarter = quarter
        self._children = self._create_children()

    def _create_children(self) -> list[GridtimeLeaf]:
        return create_quarter_months(self.year, self.quarter) # type: ignore
    
    def __repr__(self):
        return f"{self.year}-Q{self.quarter}"
    
@register_unit("years", children_key="quarters")    
class Year(GridtimeStructure):
    def __init__(self, year: int):
        super().__init__()
        self.year = year
        self._children = self._create_children()

    def _create_children(self) -> list[GridtimeLeaf]:
        return create_quarters(self.year, quarters=range(1, 5))  #type: ignore
    
    def __repr__(self):
        return f"{self.year}"    
    
@register_unit("weeks", children_key="days")    
class Week(GridtimeStructure):
    def __init__(self, iso_year: int, iso_week: int):
        super().__init__()
        self.iso_year = iso_year
        self.iso_week = iso_week
        self._children = self._create_children()

    def _create_children(self) -> list[GridtimeLeaf]:
        return create_week_days(self.iso_year, self.iso_week)  #type: ignore

    def __repr__(self):
        return f"W-{self.iso_week}-{self.iso_year}"
    
@register_unit("seasons", children_key="quarters")      
class Season(GridtimeStructure):
    def __init__(self, year: int, type_: str):
        super().__init__()
        if type_ not in ("W", "S"):
            raise ValueError("Sezon musi być 'W' lub 'S'")

        self.year = year
        self.type = type_
        self._children = self._create_children()

    def _create_children(self) -> list[GridtimeLeaf]:
        return create_season_quarters(self.year, self.type) #type: ignore
    
    def __repr__(self):
        display_year = f"{self.year}/{self.year + 1}" if self.type == "W" else str(self.year)
        return f"S-{self.type}-{display_year}"

def create_days(year: int, month: int, day_range=None) -> list[Day]:
    num_days = monthrange(year, month)[1]
    if day_range is None:
        day_range = range(1, num_days + 1)

    return [Day(date(year, month, d)) for d in day_range]

def create_months(year: int, months: list[int]) -> list[Month]:
    return [Month(year, m) for m in months]

def create_quarters(year: int, quarters=range(1, 5)) -> list[Quarter]:
    return [Quarter(year, q) for q in quarters]

def create_season_quarters(year: int, type_: str) -> list[Quarter]:
    if type_ not in ("W", "S"):
        raise ValueError("Sezon musi być 'W' (zimowy) lub 'S' (letni)")

    if type_ == "W":
        # Zimowy sezon np. 2024 = Q4/2024 + Q1/2025
        return [Quarter(year, 4), Quarter(year + 1, 1)]
    else:  # type_ == "S"
        # Letni sezon np. 2024 = Q2 + Q3 roku 2024
        return [Quarter(year, 2), Quarter(year, 3)]

def create_week_days(iso_year: int, iso_week: int) -> list[Day]:
    return [Day(date.fromisocalendar(iso_year, iso_week, i)) for i in range(1, 8)]

def create_hours(date_: date, hour_range=range(1, 25)) -> list[Hour]:
    hours: list[Hour] = []

    for hour in hour_range:
        dt_end = datetime.combine(date_, time(0)) + timedelta(hours=hour)
        start_time = dt_end - timedelta(hours=1)

        # brakująca (wiosenna) godzina – pomijamy
        if is_missing_hour(start_time):
            continue

        # podwójna godzina przy cofnięciu czasu
        if is_duplicated_hour(start_time):
            hours.append(Hour(dt_end, is_backward=False))  # 1. przed cofnięciem
            hours.append(Hour(dt_end, is_backward=True))   # 2. po cofnięciu
        else:
            hours.append(Hour(dt_end))

    return hours

def create_quarter_months(year: int, quarter: int) -> list[Month]:
    start_month = 1 + (quarter - 1) * 3
    return create_months(year, list(range(start_month, start_month + 3)))

def create_quarter_hours(start_time: datetime) -> list[QuarterHour]:
    quarters: list[QuarterHour] = []

    for i in range(4):
        dt = start_time + timedelta(minutes=15 * i)

        if is_missing_quarter(dt):
            continue

        if is_duplicated_quarter(dt):
            quarters.append(QuarterHour(dt, is_backward=False))
            quarters.append(QuarterHour(dt, is_backward=True))
        else:
            quarters.append(QuarterHour(dt))

    return quarters

if __name__ == "__main__":
    # Test the structure tree printing
    nov_3 = Day(date(2025, 11, 3))
    h23 = Hour(datetime(2025, 11, 3, 22, 0))

    print(nov_3) 
    print(h23) 
    print(h23 in nov_3)