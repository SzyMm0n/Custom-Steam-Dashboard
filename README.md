# Custom-Steam-Dashboard

Interaktywny desktopowy dashboard (PySide6 + asyncio) do przeglądania aktywności gier Steam, nadchodzących premier i promocji, z filtrowaniem po tagach i zakresie liczby graczy.

- Szczegółowa dokumentacja techniczna (PL): `docs/TECHNICAL_DOCUMENTATION_PL.md`
- Dokumentacja warstwy UI (PL): `docs/UI_DOCUMENTATION_PL.md`
- Licencja: MIT (plik `LICENSE`)

## Spis treści
- Wprowadzenie i główny use-case
- Docelowy użytkownik
- Architektura (obecnie) i struktura repozytorium
- Biblioteki i wymagania
- Instalacja i uruchomienie (Linux/Windows/macOS)
- Konfiguracja i przechowywanie danych
- Jak korzystać (skrót)
- Plan rozwoju (client–server, AWS EC2 + RDS, wykresy i heatmapa)
- Bezpieczeństwo i prywatność
- Troubleshooting (częste problemy)
- Pakowanie aplikacji (opcjonalnie)
- Contributing (dev setup)
- Licencja

## Wprowadzenie i główny use-case
Aplikacja prezentuje w jednym miejscu:
- Live liczby graczy dla gier z Twojej watchlisty (z bazy lokalnej),
- Promocje („Best Deals”),
- Nadchodzące premiery („Best Upcoming Releases”),
- Podgląd biblioteki i czasu gry użytkownika (zakładka „Biblioteka gier”).

Główny use-case: szybki wgląd w to, „w co teraz grają” oraz co warto obserwować lub kupić — z możliwością filtrowania po tagach (gatunki/kategorie) i zakresie liczby graczy.

## Docelowy użytkownik
- Gracze PC korzystający ze Steama, chcący monitorować popularność i aktywność gier,
- Osoby śledzące promocje i premiery,
- Użytkownicy chcący przejrzeć własną bibliotekę i ostatnią aktywność bez otwierania klienta Steam.

## Architektura (obecnie) i struktura repozytorium
Obecny model to aplikacja desktopowa z lokalną bazą SQLite i asynchroniczną komunikacją HTTP do serwisów zewnętrznych.

Najważniejsze elementy:
- UI: PySide6 + qasync (most Qt ↔ asyncio),
- Dane lokalne: SQLite (przez warstwę `SyncDatabase`/`AsyncDatabase`),
- Serwisy HTTP: Steam Store API, Steam Web API (publiczne fallbacki gdy brak klucza), CheapShark (deale),
- Zadania wsadowe (retencja/seed): skrypty w `app/core/data/` i folderze `backend/` (z myślą o migracji do client–server).

Struktura (skrócona):
```
app/
  main.py             # bootstrap i uruchomienie GUI
  main_window.py      # główne okno + nawigacja (HomeView / LibraryView)
  ui/
    home_view.py      # lista „Live Games Count”, filtry, deale, premiery
    library_view.py   # zakładka „Biblioteka gier” (SteamID/vanity/URL)
    user_info_dialog.py # alternatywny dialog z danymi profilu
  core/
    services/
      steam_api.py    # klienci Steam Store/Web API (httpx, pydantic)
      deals_api.py    # klient CheapShark (promocje)
    data/
      db.py           # SQLite: schema + Sync/Async wrapper
      retention_job.py# seed watchlist, retencja próbek (cli)
backend/
  ...                 # kod zadań (np. player_count) pod przyszły serwer
common/
  _base_http.py       # bazowy klient HTTP (timeouty, retry itp.)
docs/
  TECHNICAL_DOCUMENTATION_PL.md
  UI_DOCUMENTATION_PL.md
```

## Biblioteki i wymagania
- Język i wersja: Python >= 3.11, < 3.13 (rekomendowane 3.12)
- Kluczowe zależności (patrz `requirements.txt` / `pyproject.toml`):
  - PySide6 (UI), qasync (integracja z asyncio),
  - httpx[http2] (HTTP), tenacity (retry/backoff),
  - pydantic (modele danych), rapidfuzz (dopasowania tytułów),
  - python-dotenv (wczytywanie .env), platformdirs (ścieżki użytkownika), loguru (logi).
- Opcjonalne (wizualizacje – planowane):
  - matplotlib lub pyqtgraph,
- Opcjonalne (dane/analityka): aiosqlite, pandas.

## Instalacja i uruchomienie (Linux/Windows/macOS)
1) Utwórz i aktywuj wirtualne środowisko:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```
2) Zainstaluj zależności:
```bash
pip install -r requirements.txt
```
3) Uruchom aplikację GUI:
```bash
python -m app.main
```
4) (Opcjonalnie) Narzędzia/CLI do seed/retencji:
```bash
python -m app.core.data.retention_job --help
```

## Konfiguracja i przechowywanie danych
- Klucz Steam Web API jest opcjonalny. Jeśli go podasz (zmienna środowiskowa `STEAM_API_KEY` lub plik `.env`), część zapytań użyje oficjalnego API. W przeciwnym razie wykorzystywane są publiczne fallbacki (HTML/XML) – zakres danych może być węższy.
- Identyfikator użytkownika Steam do przykładowych skryptów można ustawić przez `STEAM_ID` (również wspierane przez `.env`).
- Baza lokalna: SQLite w katalogu użytkownika (platformdirs). Domyślna ścieżka (Linux):
  - `~/.local/share/Custom-Steam-Dashboard/dashboard.sqlite`
- Watchlista, tagi (gatunki/kategorie) i próbki aktywności są wersjonowane w tej bazie.

## Jak korzystać (skrót)
- Zakładka „Home” (HomeView):
  - Lista „Live Games Count” dla gier z watchlisty,
  - Filtry: suwaki/pola dla zakresu liczby graczy oraz lista tagów (gatunki/kategorie),
  - Dolne sekcje: „Best Deals” i „Best Upcoming Releases”.
- Zakładka „Biblioteka gier” (LibraryView):
  - Wpisz SteamID64, vanity lub URL profilu i kliknij „Pobierz”,
  - Zobaczysz tabelę z łączną liczbą godzin i aktywnością z ostatnich 2 tygodni; nagłówek pokazuje avatar i nazwę profilu.
- Przycisk „Odśwież” w pasku narzędzi odświeża bieżący widok (asynchronicznie, bez blokowania UI). Dane na Home odświeżają się automatycznie co 5 min.

## Plan rozwoju
Najbliższe kroki skupiają się na bezpieczeństwie i skalowalności — przejście na architekturę klient–serwer i rozszerzenia wizualne.

1) Architektura klient–serwer (w toku):
- Uruchomiona jednostka AWS EC2, która będzie wykonywać:
  - player_count_job (zbieranie próbek liczby graczy),
  - retencję/rollupy danych.
- Dane przechowywane w AWS RDS, dostępne wyłącznie z EC2 (RDS nie jest bezpośrednio dostępne z Internetu).
- Aplikacja kliencka (ten dashboard) będzie pobierać zagregowane dane przez endpointy na EC2.
- Korzyści: lepsze bezpieczeństwo (brak bezpośrednich połączeń DB z klienta), mniejszy ruch do API Steama z urządzeń końcowych, łatwiejsze aktualizacje.

2) Wizualizacje i analityka klienta:
- Wykresy aktywności graczy (np. dzienne/godzinowe) dla poszczególnych gier,
- Heatmapa własnej aktywności w grach (np. siatka dzień/godzina),
- Technicznie: rozważamy `pyqtgraph` (lekki i szybki) lub `matplotlib` (bogatszy, szerszy ekosystem).

3) Dalsze usprawnienia:
- Ustawienia aplikacji (reguły odświeżania, przechowywanie klucza API, preferencje lokalizacji),
- Zarządzanie watchlistą z UI,
- Lepsze cache’owanie wyników HTTP i odporność na błędy sieciowe,
- Pakiety instalacyjne dla systemów desktopowych (PyInstaller),
- Telemetria: domyślnie wyłączona, opt-in.


## Troubleshooting (częste problemy)
- „Qt platform plugin”/problemy z uruchomieniem PySide6:
  - Zaktualizuj sterowniki/środowisko graficzne; na Linuksie spróbuj uruchomić na X11 zamiast Wayland (lub odwrotnie).
- Problemy sieciowe/HTTP:
  - Sprawdź połączenie i proxy; brak klucza `STEAM_API_KEY` ogranicza część danych Web API.
- Brak danych na liście „Live Games Count”:
  - Upewnij się, że watchlista została zasilona (uruchomienie aplikacji wykona seed top gier; ewentualnie CLI z `retention_job.py`).

## Licencja
MIT — zob. `LICENSE`.
