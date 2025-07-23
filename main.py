from gridtime import gridtime as gt 
from datetime import date, datetime

if __name__ == "__main__":
    h = gt.MonthDecade(2025, 10, 1)      # ↑1st (noc cofnięcia czasu)
    print(h.shift(-3))
    print(h.shift(-2))
    print(h.shift(-1))  
    print(h.shift(0))  
    print(h.shift(1))  
    print(h.shift(2))  
    print(h.shift(3))  
    print(h.shift(4))  
    print(h.shift(5))  
    print(h.shift(6))  
