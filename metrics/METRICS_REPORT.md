# METRICS REPORT — Custom-Steam-Dashboard

Generated: 2025-12-18 12:59:01

## Zakres analizy (pokrycie plików)
- Katalogi: `server/` (backend), `app/` (frontend)
- Wykryte pliki Python (*.py) w tych katalogach: 39
- Radon CC (złożoność): przeanalizowano podzbiór plików Python (31/39); brakujące: 8 (nie wypisujemy)
- Radon MI (maintainability): przeanalizowano wszystkie pliki Python (39/39)
- Radon RAW (surowe metryki): przeanalizowano wszystkie pliki Python (39/39)
- Wyjaśnienie CC: `radon cc` raportuje tylko pliki, w których wykryje funkcje/metody/klasy. Pliki typu `__init__.py` bez definicji zwykle nie pojawiają się w JSON, mimo że były przetworzone.
- Lista plików nieobecnych w kluczach `radon_cc.json` została zapisana do: `metrics/radon_cc_missing_files.txt` (liczba: 8)

## Narzędzia
- `cloc` — LOC (kod/komentarze/puste linie)
- `radon` — złożoność cyklomatyczna (CC), Maintainability Index (MI), metryki surowe/strukturalne

## Linie kodu (LOC)
- Cała aplikacja (server + app): code=6454, comment=3079, blank=2053, files=32
- Backend (server): code=2308, comment=1111, blank=762, files=12
- Frontend (app): code=4146, comment=1968, blank=1291, files=20
- Pokrycie LOC: `cloc` policzył 32/39 plików `*.py`; pominięte: 7 (najczęściej puste `__init__.py`).
- Listy pomocnicze: `metrics/cloc_counted.txt` (policzone) oraz `metrics/cloc_ignored.txt` (zignorowane + powód).
- Komentarz: interpretuj powyższe jako wielkość projektu (mały/średni) w kontekście Semgrepa.

## Złożoność cyklomatyczna (CC)
- Średnia CC backend: 3.47
- Średnia CC frontend: 3.27
- 3–5 najbardziej złożonych jednostek:
  - D:\github\Custom-Steam-Dashboard\app\ui\components_server.py: GameDetailPanel._load_from_server | CC=26 | rank=D
  - D:\github\Custom-Steam-Dashboard\app\ui\components_server.py: GameDetailPanel._load_steam_store_details | CC=22 | rank=D
  - D:\github\Custom-Steam-Dashboard\app\ui\home_view_server.py: HomeView._fetch_upcoming | CC=21 | rank=D
  - D:\github\Custom-Steam-Dashboard\server\services\deals_service.py: IsThereAnyDealClient.search_deals | CC=20 | rank=C
  - D:\github\Custom-Steam-Dashboard\server\app.py: get_best_deals | CC=18 | rank=C
- Funkcje o rank D/E/F: TAK

## Maintainability Index (MI)
- Średni MI backend: 69.83
- Średni MI frontend: 66.29
- Najniższy MI: D:\github\Custom-Steam-Dashboard\app\ui\components_server.py | MI=14.05 | rank=B
- Interpretacja: >85 bardzo dobra, 65–85 poprawna, <65 trudna w utrzymaniu.

## Metryki obiektowe (strukturalne)
- Liczba klas: 45
- Liczba funkcji (top-level): 65
- Liczba metod: 298
- Komentarz: liczby są wyliczane best-effort z danych `radon cc`, więc dotyczą tego samego zakresu plików co sekcja CC.

## CFG – interpretacja
- Nie generujemy pełnych grafów CFG dla całej aplikacji (Python dynamiczny, słaba skalowalność narzędzi).
- CC (`radon cc`) jest liczona na podstawie CFG, więc traktujemy ją jako pośrednią metrykę CFG.
- Wygenerowane przykładowe wizualizacje CFG (2 funkcje z `server/security.py`):
  - verify_request_signature: DOT=`metrics/cfg/security__verify_request_signature.dot`, PNG=`metrics/cfg/security__verify_request_signature.png`
  - verify_jwt: DOT=`metrics/cfg/security__verify_jwt.dot`, PNG=`metrics/cfg/security__verify_jwt.png`

## Wnioski końcowe
- Uzupełnij krótką interpretację w kontekście wyników Semgrepa (czy metryki wspierają niską liczbę findings).
