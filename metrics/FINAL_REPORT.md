# FINAL REPORT — Metryki kodu (Custom-Steam-Dashboard)

Data stworzenia raportu: 2025-12-18

## 1. Zakres i metodologia

**Zakres projektu:**
- Backend: `server/`
- Frontend (GUI): `app/`
- Raport obejmuje: całą aplikację (zbiorczo) oraz porównanie backend vs frontend.

**Uwaga o pokryciu plików:**
- W katalogach `server/` + `app/` wykryto łącznie **39** plików `*.py`.
- `radon mi` oraz `radon raw` raportują wyniki **dla wszystkich 39/39** plików.
- `radon cc` w praktyce raportuje tylko pliki, w których znajduje jednostki do policzenia (funkcje/metody/klasy). Stąd w kluczach `radon_cc.json` widocznych jest **31/39** plików; brakujące to zwykle puste `__init__.py`.
  - Lista tych plików jest zapisana w `metrics/radon_cc_missing_files.txt`.
- `cloc` policzył LOC dla **32/39** plików `*.py` (typowo pomija puste `__init__.py`).
  - Listy pomocnicze: `metrics/cloc_counted.txt` oraz `metrics/cloc_ignored.txt`.

---

## 2. Narzędzia

**Użyte narzędzia:**
- **cloc** — metryka LOC (linie kodu / komentarzy / puste linie). Uzasadnienie: standardowe, porównywalne wyniki dla projektów.
- **radon** — metryki jakości i złożoności dla Pythona:
  - CC (Cyclomatic Complexity)
  - MI (Maintainability Index)
  - metryki surowe/strukturalne oraz dane do wyprowadzenia metryk OO (liczba klas/metod/funkcji)

**Dodatkowo:**
- CFG wygenerowano w formacie DOT oraz PNG dla 2 funkcji z `server/security.py` (szczegóły w sekcji 7).

---

## 3. Linie kodu (LOC)

**Czym jest LOC?**
LOC (Lines of Code) to ilościowa metryka rozmiaru projektu. `cloc` rozróżnia linie kodu, komentarze oraz puste linie, co ułatwia interpretację “realnej” wielkości kodu.

**Wyniki (cloc):**
- **Cała aplikacja (server + app):**
  - code=6454, comment=3079, blank=2053
- **Backend (`server/`):**
  - code=2308, comment=1111, blank=762
- **Frontend (`app/`):**
  - code=4146, comment=1968, blank=1291

**Komentarz:**
- Projekt jest **mały/średni** pod względem ilości kodu, a rozkład LOC wskazuje, że większa część implementacji znajduje się po stronie frontendu (GUI).

---

## 4. Złożoność cyklomatyczna (CC)

**Czym jest CC?**
Złożoność cyklomatyczna (Cyclomatic Complexity) mierzy liczbę niezależnych ścieżek wykonania w kodzie. W praktyce: im więcej warunków/gałęzi (if/elif/try/except/loops), tym większa CC. CC jest też używana jako **pośrednia metryka CFG**, bo wynika ze struktury grafu przepływu sterowania.

**Wyniki (średnie CC):**
- **Backend:** 3.47
- **Frontend:** 3.27

**Najbardziej złożone funkcje/metody:**
- `app/ui/components_server.py` — `GameDetailPanel._load_from_server` | CC=26 | rank=D
- `app/ui/components_server.py` — `GameDetailPanel._load_steam_store_details` | CC=22 | rank=D
- `app/ui/home_view_server.py` — `HomeView._fetch_upcoming` | CC=21 | rank=D
- `server/services/deals_service.py` — `IsThereAnyDealClient.search_deals` | CC=20 | rank=C
- `server/app.py` — `get_best_deals` | CC=18 | rank=C

**Czy występują funkcje klasy D/E/F?**
- Tak: występują jednostki o rank **D**.

**Komentarz:**
- Średnie CC dla obu części jest niskie (rzędu ~3), co sugeruje, że większość kodu ma prostą logikę.
- Jednocześnie w UI występują pojedyncze metody o rank D, co jest typowe dla kodu “orchestrującego” kilka kroków (pobranie danych, walidacje, obsługa błędów, aktualizacja UI).

---

## 5. Maintainability Index (MI)

**Czym jest MI?**
Maintainability Index to syntetyczny wskaźnik “łatwości utrzymania” kodu (czytelność, złożoność, rozmiar). W uproszczeniu: im wyższy MI, tym kod łatwiejszy w utrzymaniu.

**Wyniki (średni MI):**
- **Backend:** 69.83
- **Frontend:** 66.29

**Najniższy MI (plik):**
- `app/ui/components_server.py` | MI=14.05 | rank=B

**Interpretacja:**
- **>85** – bardzo dobra
- **65–85** – poprawna
- **<65** – trudna w utrzymaniu

**Komentarz:**
- Średnie MI w obu częściach jest w zakresie **“poprawna”** (ok. 66–70).
- Najniższy wynik (14.05) wskazuje na pojedynczy problematyczny plik — spójne z obserwacją wysokich CC w metodach z `components_server.py`.

---

## 6. Metryki obiektowe (OO)

**Co mierzymy?**
W ujęciu raportowym liczymy podstawowe wskaźniki struktury obiektowej: liczbę klas, metod i funkcji. To pozwala scharakteryzować styl architektury (bardziej proceduralny vs obiektowy) oraz “gęstość” API wewnętrznego.

**Wyniki (na podstawie danych `radon cc`):**
- Liczba klas: **45**
- Liczba funkcji (top-level): **65**
- Liczba metod: **298**

**Komentarz:**
- Struktura wskazuje na **istotny komponent obiektowy** (wiele metod względem funkcji top-level), co jest spójne z architekturą GUI + serwisy po stronie backendu.

---

## 7. CFG – interpretacja

**Dlaczego CC traktujemy jako metrykę CFG?**
- CC wynika z liczby rozgałęzień w przepływie sterowania (grafie CFG). W uproszczeniu: im więcej węzłów decyzyjnych/gałęzi w CFG, tym większa CC.

**Dlaczego nie generujemy pełnych grafów CFG dla całej aplikacji?**
- Python jest językiem dynamicznym, a pełny CFG całego projektu jest trudny do rzetelnego wyznaczenia i mało skalowalny narzędziowo.

**Wizualizacja (ilustracja, 2 funkcje):**
- `verify_request_signature`:
  - DOT: `metrics/cfg/security__verify_request_signature.dot`
  - PNG: `metrics/cfg/security__verify_request_signature.png`
- `verify_jwt`:
  - DOT: `metrics/cfg/security__verify_jwt.dot`
  - PNG: `metrics/cfg/security__verify_jwt.png`

**Komentarz:**
- Te dwa przykłady pokazują typową strukturę kontroli przepływu w module bezpieczeństwa (warunki, wyjątki), co uzasadnia korzystanie z CC jako metryki “CFG pośrednio”.

---

## 8. Wnioski końcowe

- Metryki wskazują na projekt **mały/średni** (ok. 6.5k linii kodu) z większym udziałem kodu po stronie UI.
- Średnia złożoność (CC) jest **niska** w obu częściach; jednocześnie istnieją pojedyncze jednostki o rank D (głównie w UI), które są naturalnymi kandydatami do ewentualnego uproszczenia w przyszłości.
- MI średnio jest **poprawny** (65–85) dla backendu i frontendu, ale jeden plik (`app/ui/components_server.py`) znacząco odstaje w dół.

**Powiązanie z analizą Semgrep:**
- Przy takim rozmiarze i przeciętnej złożoności kodu, “niska liczba findings” z Semgrepa jest spójna z obrazem projektu o umiarkowanej komplikacji.
- Najwięcej ryzyka koncentracji złożoności jest w nielicznych modułach UI; to dobra informacja do uzasadnienia, że wyniki Semgrepa nie są zaniżone przez ogromną bazę kodu o wysokiej złożoności.
