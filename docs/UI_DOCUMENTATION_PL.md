# Custom-Steam-Dashboard — Dokumentacja warstwy UI (aktualna)

Ten dokument skupia się wyłącznie na warstwie UI: widokach, dialogach, przepływach i interakcjach. Zawiera porównanie do poprzedniej wersji, opis klas i metod (co robią, po co, argumenty), a także krótkie przykłady użycia.

Spis treści:
- 1) Co się zmieniło względem poprzedniej wersji
- 2) Przegląd UI i przepływ
- 3) Klasy i metody
  - 3.1 MainWindow
  - 3.2 HomeView
  - 3.3 LibraryView (NOWE)
  - 3.4 SteamUserInfoDialog
  - 3.5 Pomocnicze: NumberValidator, GameDetailDialog (NOWE)
- 4) Edge-case'y i uwagi projektowe dla UI
- 5) Mini-przykłady


## 1) Co się zmieniło względem poprzedniej wersji

Najważniejsze różnice w UI w stosunku do wcześniejszej dokumentacji:

- MainWindow
  - ZMIANA: Konstruktor `MainWindow` przyjmuje teraz instancję bazy danych `AsyncDatabase` i przekazuje ją do `HomeView`.
  - ZMIANA: Dodano nową zakładkę/stronę `LibraryView` oraz akcję paska narzędzi „Biblioteka gier”.
  - ZMIANA: `refresh_current_view()` wywołuje metodę `refresh_data()` na bieżącym widżecie (wcześniej spodziewał się metody `refresh()`).

- HomeView
  - ZMIANA: Zrezygnowano z stałej `TOP_GAME_APP_IDS`; źródłem listy gier jest teraz watchlista z lokalnej bazy (`AsyncDatabase.get_watchlist_appids`).
  - ZMIANA: Przebudowa interfejsu — dwukolumnowy układ: po lewej lista „Live Games Count”, po prawej panel filtrów (zakres graczy, tagi gatunków/kategorii z bazy).
  - ZMIANA: Metoda publiczna to `refresh_data()` (async, uruchamiana przez `QTimer` co 5 min i ręcznie), a nie `refresh()` + `_load_data_async()`.
  - NOWE: Pobieranie i aktualizacja tagów (gatunki/kategorie) na podstawie `get_app_details`, oraz zapisywanie do bazy (`upsert_watchlist_tags`).
  - NOWE: `GameDetailDialog` z obrazem nagłówka i krótkim opisem gry z Store API, wywoływany po kliknięciu na listę.
  - NOWE: Lokalizacja formatowania liczb (PL) przy prezentacji liczby graczy.

- LibraryView (NOWE)
  - NOWA zakładka integrująca funkcjonalność przeglądu biblioteki użytkownika bezpośrednio w głównym oknie (wcześniej był do tego oddzielny dialog `SteamUserInfoDialog`).
  - Rozwiązywanie SteamID z vanity/URL, pobieranie podsumowania i gier z `SteamWebApiClient`, prezentacja w tabeli.

- SteamUserInfoDialog
  - Pozostaje dostępny i funkcjonalny, ale nie jest głównym punktem dostępu w UI (jego uproszczona wersja została wbudowana w `LibraryView`).


## 2) Przegląd UI i przepływ

- Aplikacja startuje `MainWindow`, które utrzymuje `QStackedWidget` z dwiema stronami: `HomeView` i `LibraryView`.
- `HomeView`:
  - Co 5 minut (QTimer) oraz na żądanie (przycisk „Odśwież”) odświeża liczby graczy online dla gier z watchlisty.
  - Po kliknięciu pozycji otwiera szczegóły gry (dialog z obrazem i opisem).
  - Prawy panel umożliwia filtrowanie po zakresie liczby graczy i po tagach (gatunki/kategorie) zsynchronizowanych z bazą.
  - Sekcje dolne: „Best Deals” (CheapShark), „Best Upcoming Releases” (Store API) — ładowane asynchronicznie.
- `LibraryView`:
  - Użytkownik podaje SteamID/vanity/URL profilu i pobiera bibliotekę gier oraz ostatnio grane tytuły; prezentacja w tabeli, z nagłówkiem profilu.


## 3) Klasy i metody

### 3.1 app/main_window.py — MainWindow(QMainWindow)

Cel: Główne okno z paskiem narzędzi i stosowanymi stronami UI.

- __init__(self, db: Database)
  - Co robi: Konfiguruje okno (rozmiar, tytuł), tworzy `QStackedWidget`, dodaje `HomeView(db)` i `LibraryView`, inicjalizuje toolbar.
  - Dlaczego: Centralizacja nawigacji, przekazanie zależności (DB) do widoków, łatwa rozbudowa.
  - Argumenty: `db` — instancja `AsyncDatabase` używana przez `HomeView` do pobierania watchlisty/tagów.
  - Przykład: tworzenie w `app/main.py` po bootstrapie bazy i przekazanie do okna.

- _init_toolbar(self)
  - Co robi: Tworzy pasek narzędzi z akcjami: „Home”, „Biblioteka gier” i „Odśwież”.
  - Dlaczego: Szybki dostęp do nawigacji i manualnego odświeżania aktywnego widoku.
  - Argumenty: brak (metoda pomocnicza).

- navigate_to_library(self)
  - Co robi: Przełącza `QStackedWidget` na stronę `LibraryView`.
  - Dlaczego: Wygodna nawigacja z toolbaru.
  - Argumenty: brak.

- refresh_current_view(self)
  - Co robi: Jeśli aktywny widżet ma metodę `refresh_data()`, uruchamia asynchronicznie jej wykonanie (`asyncio.create_task`).
  - Dlaczego: Ujednolicone odświeżanie niezależnie od konkretnego widoku (aktualnie obsługiwane przez `HomeView`).
  - Argumenty: brak.


### 3.2 app/ui/home_view.py — HomeView(QWidget)

Cel: Widok główny z listą „Live Games Count” oraz panelami „Best Deals” i „Best Upcoming Releases”, rozszerzony o filtrację.

Ważne pola i komponenty:
- `top_live_list: QListWidget` — lista gier z aktualną liczbą graczy (kliknięcie otwiera `GameDetailDialog`).
- Prawy panel filtrów: dwa slidery + pola tekstowe dla minimalnej i maksymalnej liczby graczy; lista checkowalnych tagów (z bazy).
- `trending_list: QListWidget`, `upcoming_list: QListWidget` — sekcje dolne z promocjami i nadchodzącymi premierami.
- `QTimer` odświeżający dane co 5 min.

Metody:
- __init__(self, db: Database, parent: Optional[QWidget] = None)
  - Co robi: Buduje układ (lewa lista, prawy panel filtrów, listy dolne), zapamiętuje `db`, ustawia `QTimer`, uruchamia pierwsze ładowanie.
  - Dlaczego: Po starcie UI widok ma się od razu wypełnić danymi i być gotowy na cykliczne odświeżanie.
  - Argumenty: `db` — instancja `AsyncDatabase` do łatwego pobierania watchlisty i tagów; `parent` — rodzic w drzewie Qt.

- refresh_data(self) — async
  - Co robi: Czyści i ładuje dane:
    - z bazy: appID-y z watchlisty i mapę tagów,
    - ze Store API: liczby graczy i (warunkowo) szczegóły dla brakujących tagów (aktualizuje bazę),
    - z CheapShark: listę promocji,
    - ze Store API: listę nadchodzących premier.
    Wynik sortuje po liczbie graczy i wyświetla, synchronizując też listę tagów.
  - Dlaczego: Główna ścieżka odświeżania logiki widoku, wywoływana cyklicznie i ręcznie.
  - Argumenty: brak.
  - Przykład: `asyncio.create_task(home_view.refresh_data())` lub użycie przycisku „Odśwież”.

- _init_ui(self)
  - Co robi: Składa layout, tworzy komponenty, ustawia stylesheet (ciemny motyw z zielonym akcentem), podpina sygnały.
  - Dlaczego: Rozdzielenie konstrukcji UI od logiki.
  - Argumenty: brak.

- _start_initial_load(self)
  - Co robi: Uruchamia pierwsze odświeżenie przez `asyncio.create_task(self.refresh_data())` po zainicjalizowaniu widżetów.
  - Dlaczego: Szybki bootstrap danych bez blokowania konstruktora.
  - Argumenty: brak.

- _populate_tag_checkboxes(self) — async
  - Co robi: Wczytuje unikalne tagi (gatunki i kategorie) z bazy i tworzy checkowalne pozycje na liście tagów.
  - Dlaczego: Umożliwia filtrowanie po tagach dostępnych dla watchlisty.
  - Argumenty: brak.

- _update_list_view(self)
  - Co robi: Filtruje w pamięci `_all_games_data` po zakresie graczy i wybranych tagach, sortuje i renderuje do `top_live_list`.
  - Dlaczego: Oddzielenie warstwy prezentacji od pobierania danych; szybkie przeodświeżanie przy zmianie filtrów.
  - Argumenty: brak.

- _format_players(self, value: int) -> str
  - Co robi: Formatuje liczbę graczy z lokalizacją PL (rozsądne separatory tysięcy).
  - Dlaczego: Czytelniejsza prezentacja większych liczb.
  - Argumenty: `value` — liczba graczy (int).

- Handlery suwaków i pól wejściowych:
  - _on_min_slider_moved(self, value: int)
  - _on_max_slider_moved(self, value: int)
  - _on_min_input_changed(self)
  - _on_max_input_changed(self)
  - _on_apply_filters(self)
  - _on_clear_filters(self)
  - Co robią: Synchronizują wartości filtrów (suwaki <-> pola), pilnują spójności min/max, aktualizują widok listy.
  - Dlaczego: Interaktywne filtrowanie bez dodatkowych zapytań do API.
  - Argumenty: `value` dla handlerów suwaków; pozostałe brak.

- _on_live_item_clicked(self, item: QListWidgetItem)
  - Co robi: Otwiera `GameDetailDialog` z danymi gry zapisanymi w `Qt.UserRole` elementu listy.
  - Dlaczego: Szczegółowe informacje (opis, obraz) na żądanie.
  - Argumenty: `item` — kliknięta pozycja z listy.

Dodatkowo:
- `_open_login_dialog(self)` — pomocnicza metoda otwierająca `SteamUserInfoDialog` (obecnie nieaktywna w UI, zachowana dla przyszłych opcji profilu).


### 3.3 app/ui/library_view.py — LibraryView(QWidget) [NOWE]

Cel: Zintegrowana zakładka „Biblioteka gier” prezentująca gry użytkownika, czas gry łącznie i z 2 ostatnich tygodni oraz nagłówek profilu.

- __init__(self, parent: Optional[QWidget] = None)
  - Co robi: Inicjuje UI, buduje nagłówek profilu, pole wejściowe dla SteamID/vanity/URL oraz tabelę wyników.
  - Dlaczego: Umożliwia szybki podgląd biblioteki z poziomu głównego okna.
  - Argumenty: `parent` — rodzic Qt.

- _init_ui(self)
  - Co robi: Tworzy layout, avatar i nazwę użytkownika, wiersz wejścia (`QLineEdit`) i przycisk „Pobierz”, tabelę z kolumnami: Nazwa gry | Łączna liczba godzin | Ostatnie 2 tygodnie (h).
  - Dlaczego: Czytelny układ danych profilu i tabeli.
  - Argumenty: brak.

- _on_fetch(self) — async
  - Co robi: Rozwiązuje wejście do `steamid` (`SteamWebApiClient.resolve_steamid`), pobiera `get_player_summary`, `get_owned_games`, `get_recently_played`, a następnie wypełnia nagłówek i tabelę.
  - Dlaczego: Jedno miejsce obsługi pobrania i renderowania danych biblioteki.
  - Argumenty: brak.
  - Uwagi: API Key nie jest wymagany (korzysta z publicznych danych, o ile dostępne); błędy są prezentowane w labelu statusu.


### 3.4 app/ui/user_info_dialog.py — SteamUserInfoDialog(QDialog)

Cel: Samodzielne okno do pobierania danych profilu i biblioteki. Zachowane dla kompatybilności i alternatywnego UX.

- __init__(self, parent=None)
  - Co robi: Buduje dialog, ustawienia czcionek/przyjaznych polskich fontów, pola do wprowadzenia SteamID i (opcjonalnego) API key.
  - Dlaczego: Pozwala na pracę jako autonomiczne okno poza `LibraryView`.
  - Argumenty: `parent` — rodzic Qt.

- _choose_polish_font(self) -> QFont
  - Co robi: Wybiera dostępny font dobrze obsługujący polskie znaki.
  - Dlaczego: Spójność i czytelność interfejsu w PL.

- _init_ui(self)
  - Co robi: Składa layout dialogu, przyciski, status i tabelę z grami.
  - Dlaczego: Oddzielenie konstrukcji UI.

- _on_fetch_clicked(self) — async
  - Co robi: Rozwiązuje `steamid` (vanity/URL/ID), pobiera dane profilu i biblioteki i renderuje do tabeli.
  - Dlaczego: Główna akcja użytkownika w dialogu.

- _fetch_summary_owned_recent(self, steamid: str, api_key: Optional[str]) — async
  - Co robi: Pomocnicze pobranie: `get_player_summary`, `get_owned_games`, `get_recently_played` i zbudowanie mapy czasu z 2 tygodni.
  - Dlaczego: Uporządkowanie kodu i ułatwienie testowania.


### 3.5 Pomocnicze

- NumberValidator(QRegularExpressionValidator)
  - Co robi: Waliduje pola liczby graczy (cyfry i spacje jako separator, maks. 15 znaków).
  - Dlaczego: Zapobieganie błędnym wartościom wejściowym dla filtrów.

- GameDetailDialog(QDialog) [NOWE]
  - Co robi: Wyświetla nagłówek (obraz) i krótki opis gry ze Store API; jeśli dostępne, pokazuje liczbę graczy i tagi.
  - Dlaczego: Szczegóły „na żądanie” bez opuszczania `HomeView`.
  - Metody:
    - __init__(self, game_data: dict|str, parent: Optional[QWidget]) — przygotowuje layout i uruchamia async doładowanie.
    - _load_store_and_activity(self, appid: int) — async, dociąga obraz/desc i (opcjonalnie) aktywność z lokalnej bazy.


## 4) Edge-case'y i uwagi projektowe dla UI

- Brak gier w watchliście: `HomeView` pokazuje puste listy; lista tagów może pozostać pusta do czasu pierwszego uzupełnienia tagów.
- Błędy sieci: Zapytania HTTP są otoczone `try/except`; w razie kłopotów wyświetlane są placeholdery (np. „Brak promocji”).
- Duże liczby graczy: Formatowane w lokalizacji PL dla czytelności; w polach wejściowych dopuszczone spacje.
- Spójność min/max: Handlery pilnują, aby `min <= max`; zmiana jednego suwaka może automatycznie korygować drugi.
- Asynchroniczność w UI: Odświeżanie uruchamiane przez `asyncio.create_task`, co zapobiega blokowaniu wątku GUI.
- Tagi: Aktualizowane do bazy tylko wtedy, gdy dla danej gry brak tagów (oszczędność zapytań). Pierwsze odświeżenie może uzupełnić metadane hurtowo.
- Dostępność Steam Web API: `LibraryView` nie wymaga API key dla danych publicznych; `SteamUserInfoDialog` pozwala go podać.


## 5) Mini-przykłady

- Uruchomienie okna z przekazaniem bazy i ręczne odświeżenie `HomeView`:

```python
from app.core.data.db import AsyncDatabase as Database
from app.main_window import MainWindow

# bootstrap DB
db = Database(); db.init_schema()

# utworzenie okna
win = MainWindow(db)

# odśwież bieżący widok
import asyncio
asyncio.create_task(win.home_view.refresh_data())
```

- Programowe ustawienie filtrów w `HomeView` (np. w testach UI):

```python
from PySide6.QtCore import Qt
from app.core.data.db import AsyncDatabase as Database
from app.main_window import MainWindow

# przygotowanie okna
db = Database(); db.init_schema()
win = MainWindow(db)

hv = win.home_view
hv.min_players_slider.setValue(10000)
hv.max_players_slider.setValue(200000)
# zaznacz tag „Multiplayer” jeśli istnieje na liście
for i in range(hv.tags_list_widget.count()):
    it = hv.tags_list_widget.item(i)
    if it.text().lower() == "multiplayer":
        it.setCheckState(Qt.CheckState.Checked)
        break
hv._on_apply_filters()  # przefiltruj
```

- Użycie `LibraryView` do pobrania gier dla użytkownika:

```python
from app.core.data.db import AsyncDatabase as Database
from app.main_window import MainWindow
import asyncio

# przygotowanie okna
db = Database(); db.init_schema()
win = MainWindow(db)

lv = win.library_view
lv.id_input.setText("https://steamcommunity.com/id/TwojaNazwa")
asyncio.create_task(lv._on_fetch())
```

---

Ta dokumentacja odzwierciedla aktualny stan warstwy UI w repozytorium i wskazuje kluczowe różnice względem poprzedniej wersji. W razie rozbudowy (np. nowe zakładki, dodatkowe filtry, sortowanie) zaleca się dodanie analogicznych opisów metod i mini-przykładów.
