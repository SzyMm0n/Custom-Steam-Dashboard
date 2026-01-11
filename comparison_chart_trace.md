# Trace: pobieranie danych do wykresu porównania → rysowanie (statyczny debug)

Kontekst: `ComparisonView` w `app/ui/comparison_view_server.py`, użytkownik wybiera kilka gier i klika "Porównaj wybrane" (zakres czasu np. `7d`). Poniżej opis przebiegu od kliknięcia do narysowania wykresu z przybliżeniem, jakie obiekty/memory pojawiają się po drodze. To nie jest pomiar runtime, a uporządkowany ślad z kodu – miejsca do podglądu w debuggerze są wskazane.

## Kroki z danymi i pamięcią
1. **Klik przycisku `Porównaj wybrane`** (`_compare_btn.clicked` → `asyncio.create_task(self._load_comparison())`)
   - Dane: `_selected_appids` (lista int, n ≈ liczba zaznaczonych gier), `_selected_time_range` (np. `"7d"`).
   - Pamięć: referencja do listy wyboru już istnieje; tworzony jest task w pętli asyncio (kilka bajtów na uchwyt taska).
   - Czas: natychmiast (event loop wpisuje task, <1 ms).

2. **Wejście do `ComparisonView._load_comparison`**
   - Dane: `days = _time_range_to_days('7d')` → `7` (float/int), `self._selected_appids` kopiowane tylko jako referencja w wywołaniu.
   - Pamięć: chwilowe stringi dla tekstu przycisku, zmienna `days` (kilka bajtów).
   - Czas: mikrosekundy.

3. **Wywołanie `ServerClient.get_player_history_comparison(appids, days)`**
   - Dane wejścia: `appids=[...]` (n elementów), `days=7`.
   - Pamięć: mały dict/querystring; log w loggerze.
   - Czas: przygotowanie parametrów ~<0.1 ms; czeka na I/O sieci.

4. **`AuthenticatedAPIClient.ensure_authenticated`** (jeśli brak tokenu lub wygasł)
   - Krok `login()`:
     - `body_bytes = b'{"client_id": "<id>"}'` (kilkadziesiąt bajtów).
     - `sign_request(...)` tworzy nagłówki HMAC (kilka stringów, ~1 KB łącznie).
     - `httpx.AsyncClient.post` wysyła żądanie, buforuje odpowiedź JSON (kilka KB).
     - Dane trwałe: `_access_token` (string JWT, ~1–2 KB), `_token_expires_at` (int).
   - Czas: zależny od sieci/serwera; zwykle 50–300 ms (TLS + round-trip); pomijalny CPU.

5. **`AuthenticatedAPIClient.post`**
   - `body_bytes = json.dumps({"appids": appids})` (dla n=5 ~50–100 bajtów); nagłówki z `_build_headers` (autoryzacja + HMAC).
   - `httpx` odbiera JSON z serwera: `{ "games": { "570": {name, history:[...]}, ... } }`.
   - Pamięć: dict `data` z listami historii – główny koszt (historia * liczba gier * rekordów). Każdy rekord w history to mały dict `{time_stamp:int, count:int}` (~48–64 B/rekord + overhead).
   - Czas: serializacja + podpisanie ~1–2 ms; sieć dominuje (50–300 ms typowo); deserializacja JSON przy przyjęciu (zależna od wielkości, np. 10–30 tys. rekordów ≈ kilka ms).

6. **`ServerClient.get_player_history_comparison`**
   - Konwersja kluczy `str` → `int`: tworzy nowy dict comprehension `{int(k): v for k, v in games_data.items()}` (kolejna mapa referencji do tych samych list `history`).
   - Zwraca do `_load_comparison` jako `history_data`.
   - Czas: zależy od liczby gier; dla 5 gier mikrosekundy–0.2 ms.

7. **Powrót w `ComparisonView._load_comparison`**
   - Ustawia `self._history_data = history_data` (referencja do dict).
   - Wywołuje `_update_chart()` i `_update_stats_table()`.
   - Pamięć: brak dużych kopii – jedna referencja do danych historii.
   - Czas: wywołania funkcji ~mikrosekundy; logika w następnych krokach dominuje.

8. **`_update_chart`**
   - Czyści oś: `self._ax.clear()` (zwalnia referencje do poprzednich artystów; pamięć odzyskana przy GC).
   - Ustawia kolory z `ThemeManager` (kilka stringów hex/RGB w dict `colors`).
   - Pętla po `self._history_data.items()`:
     - `history = game_data['history']` (lista rekordów, referencja).
     - `history = sorted(history, key=...)` tworzy **nową listę** posortowaną (kopiuje referencje; koszt = liczba rekordów * overhead listy).
     - `timestamps = [datetime.fromtimestamp(...)]` tworzy listę obiektów `datetime` (nowe obiekty; główny koszt per rekord).
     - `counts = [record.get('count', 0)]` lista int (kopie wartości; koszt per rekord).
     - `self._ax.plot(timestamps, counts, ...)` – matplotlib konwertuje listy do tablic (najczęściej NumPy) i tworzy obiekty `Line2D` + bufory danych (koszt ~ sizeof(list) + ~16 B/element w wewn. tablicy, zależnie od backendu).
   - Formatowanie osi/legendy dodaje stringi i struktury opisowe (małe).
   - `self._figure.tight_layout()` + `self._canvas.draw()` – rasteryzacja/rysowanie: tworzy bufory obrazu (typowo RGBA, szerokość*wysokość*4 bajty; dla figury ~1000x600 to ~2.4 MB na bufor) + struktury Qt dla widgetu.
   - Czas: zależny od liczby punktów; dla 5 gier × 500 pkt ≈ 2500 pkt → parsowanie list/datetime ~1–3 ms, plot + draw na CPU zwykle 10–40 ms; większe dane rosną liniowo + koszt rysowania.

9. **`_update_stats_table`**
   - Czyści tabelę: `setRowCount(0)` usuwa istniejące wiersze (Qt zwalnia przy GC/RAII).
   - Pętla po grach:
     - `counts = [record.get('count', 0) for record in history]` – nowa lista int (kopie wartości; koszt per rekord).
     - Wyliczenia `min`, `max`, `avg`, `median`, `volatility` na tej liście (stałe, małe struktury).
     - Tworzy `QTableWidgetItem` per kolumna (5 szt. tekstowych + nazwa); każde to obiekt Qt z krótkim tekstem.
   - Pamięć: lista `counts` i obiekty tabeli; `counts` zostaje zwolniona po iteracji.
   - Czas: dla kilku gier i setek punktów – ułamki ms; dominują operacje GUI Qt przy tworzeniu wierszy (1–5 ms zależnie od liczby wierszy).

10. **UI gotowe**
    - Dane historii pozostają w `self._history_data` (dict → listy rekordów).
    - Matplotlib trzyma referencje do swoich danych w artystach; kolejne `_update_chart` nadpisze je i oczyści.
    - Czas całkowity: sieć (dominująca) + rysowanie. Typowo 60–400 ms (zależnie od API i sprzętu) przy umiarkowanej liczbie punktów.

## Jak podglądać w debuggerze
- Ustaw breakpoint w `_load_comparison` na linii przed wywołaniem `get_player_history_comparison`; sprawdzaj `len(self._selected_appids)` i `days`.
- Drugi breakpoint w `ServerClient.get_player_history_comparison` zaraz po `data = await ...`: sprawdzaj `len(data['games'])`, sumę długości `history`.
- Breakpoint w `_update_chart` w pętli: obserwuj `len(history)`, `len(timestamps)`, `len(counts)` i `self._ax.lines` (liczba serii).
- Breakpoint w `_update_stats_table`: podgląd `counts`, wyliczone statystyki oraz `self._stats_table.rowCount()`.
- Pamięć widoczna w debuggerze: obserwuj rosnące liczby obiektów list/datetime po każdym przebiegu oraz chwilowy wzrost przy `self._canvas.draw()` (bufory renderera).

## Największe źródła przyrostu pamięci
- Listy historii z serwera (`history` per gra) – utrzymywane w `self._history_data`.
- Listy `timestamps` i `counts` tworzonych przy każdym `_update_chart` (nowe na każde odświeżenie).
- Bufor obrazu matplotlib/Qt po `draw()` (~kilka MB zależnie od rozmiaru widgetu).
- Tabela statystyk (`QTableWidgetItem` na każdy wiersz/kolumnę).

## Miejsca potencjalnych optymalizacji
- Unikać `sorted(history, ...)` gdy historia już jest posortowana (można pominąć kopiowanie).
- Reużywać tablic NumPy zamiast list przy rysowaniu (redukcja kopii i konwersji po stronie matplotlib).
- Przy bardzo dużych zakresach czasu – downsampling przed rysowaniem, aby zmniejszyć liczbę punktów/obiektów `datetime`.
