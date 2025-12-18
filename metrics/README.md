# Metrics — Custom-Steam-Dashboard

Ten katalog zawiera automatyzację do poboru i analizy metryk z pliku `analiza/METRYKI_KODU_INSTRUKCJA.md`.

## Wymagania

- Python (w repo jest już `.venv`)
- `radon` (instalowane przez `pip install -r requirements.txt` albo ręcznie `pip install radon`)
- `cloc` (narzędzie zewnętrzne, musi być dostępne w `PATH`)
- (opcjonalnie) Graphviz (`dot`) — tylko jeśli chcesz PNG z wizualizacji CFG

## Instalacja `cloc` na Windows

Najprościej (jeśli masz):

- **winget**: `winget install -e --id AlDanial.CLOC`
- **winget (poprawne ID)**: `winget install -e --id AlDanial.Cloc`
- **chocolatey**: `choco install cloc`
- **scoop**: `scoop install cloc`

Jeśli nie masz żadnego z powyższych, zainstaluj `cloc` wg oficjalnych instrukcji (Perl / binarka) i upewnij się, że polecenie `cloc` działa w terminalu.

Uwaga: jeśli instalujesz `cloc` przez `winget`, bywa że `cloc` nie trafia od razu do `PATH`. Skrypt `metrics/run_metrics.py` i tak potrafi go wykryć w typowej lokalizacji winget.

## Uruchomienie (pobór + analiza + raport)

Z katalogu głównego repo:

- `python metrics/run_metrics.py`

Skrypt wygeneruje:

- `metrics/cloc_metrics.csv` (jeśli `cloc` jest dostępny)
- `metrics/radon_cc.json`
- `metrics/radon_mi.json`
- `metrics/radon_raw.json`
- `metrics/radon_cc_missing_files.txt` (lista plików `.py` nieobecnych jako klucze w `radon_cc.json`; zwykle puste `__init__.py`)
- `metrics/METRICS_REPORT.md`

Dodatkowo (CFG – ilustracja dla 2 funkcji z `server/security.py`):

- `metrics/cfg/security__verify_request_signature.dot`
- `metrics/cfg/security__verify_request_signature.png` (jeśli jest Graphviz)
- `metrics/cfg/security__verify_jwt.dot`
- `metrics/cfg/security__verify_jwt.png` (jeśli jest Graphviz)

## Instalacja Graphviz (PNG CFG) na Windows

Jeśli chcesz mieć PNG (a nie tylko DOT), potrzebujesz `dot`.

- **winget**: `winget install -e --id Graphviz.Graphviz`
- **chocolatey**: `choco install graphviz`
- **scoop**: `scoop install graphviz`

Uwaga: czasem `dot` nie trafia od razu do `PATH`. Skrypt `metrics/run_metrics.py` potrafi go wykryć w typowych lokalizacjach (np. `C:\Program Files\Graphviz\bin\dot.exe`).

## Taski VS Code

W repo są taski w `.vscode/tasks.json`:

- `Metrics: Run (radon + cloc + report)`
- `Metrics: Install cloc (auto)`
- `Metrics: Install Graphviz (dot) (auto)`

## Uwaga o LOC

Jeśli `cloc` nie jest zainstalowany, raport nadal powstanie, ale sekcja LOC będzie miała `n/a`.
