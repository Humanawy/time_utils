# 🕒 Gridtime – struktury czasu z obsługą DST i drzewiastym API

`Gridtime` to zaawansowany system reprezentacji jednostek czasu w Pythonie – z obsługą zmian czasu (DST), strukturą drzewa (dzień → godziny → kwadranse) i wsparciem dla operacji takich jak iteracja, agregacja, przeszukiwanie.

## 🎯 Cel

Narzędzie zostało stworzone **z myślą o zastosowaniach w polskiej branży energetycznej**, w szczególności:

- przetwarzaniu danych dobowo-godzinowych oraz 15-minutowych (tzw. kwadransowych),
- zachowaniu pełnej zgodności ze specyfiką czasową PSE i OSD (zmiana czasu, powtarzające się i brakujące godziny),
- zapewnieniu **jednoznacznego przypisania każdego rekordu do przedziału czasowego**, nawet przy przesunięciu zegarowym.

## 🚀 Funkcje

- Strukturalne modelowanie czasu:
  - `Year`, `Quarter`, `Month`, `Week`, `Day`, `Hour`, `QuarterHour`
- Operacje na drzewie czasu:
  - `walk`, `get`, `count`, `tree()`, `print_tree()`
- Obsługa czasu letniego/zimowego (brakujące i podwójne godziny/kwadranse)
- Intuicyjne API: `len(day)`, `hour in day`, `for hour in day`

## 🏭 Zastosowanie w energetyce

System rozwiązuje typowe problemy branżowe:

✅ Czytelne modelowanie doby: `Day → Hour → QuarterHour`  
✅ Obsługa **braku 2:00–3:00** (wiosna) i **powtórzenia 2:00–3:00** (jesień)  
✅ Każdy przedział czasowy (`Hour`, `QuarterHour`) wie, czy:
- jest **duplikowany** (`is_duplicated=True`)
- reprezentuje **pierwsze** czy **drugie** wystąpienie (`is_backward`)

---

## 🧪 Przykład użycia

```python
from datetime import date, datetime
from gridtime import Day, Hour

# Dzień zmiany czasu z letniego na zimowy – 26 października 2025
dst_day = Day(date(2025, 10, 26))

# Wypisz wszystkie godziny w tej dobie
for hour in dst_day:
    print(hour)

# Weryfikacja zduplikowanych godzin
print("Liczba godzin:", len(dst_day))  # ➜ 25
duplicated_hours = [h for h in dst_day if h.is_duplicated]

# Sprawdź drzewo struktury
print("\nStruktura drzewa:")
dst_day.print_tree(unit_stop="hours")
```
## 🔍 Przykładowy output:
```
2025-10-26 00:00-01:00
2025-10-26 01:00-02:00
2025-10-26 02:00-03:00 [↑1st]
2025-10-26 02:00-03:00 [↓2nd]
2025-10-26 03:00-04:00
...
2025-10-26 23:00-00:00
Liczba godzin: 25

Struktura drzewa:
└── 2025-10-26
    ├── 2025-10-26 00:00-01:00
    ├── 2025-10-26 01:00-02:00
    ├── 2025-10-26 02:00-03:00 [↑1st]
    ├── 2025-10-26 02:00-03:00 [↓2nd]
    ├── 2025-10-26 03:00-04:00
    ...
```

