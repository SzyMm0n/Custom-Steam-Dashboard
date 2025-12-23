# GPT_Analysis — przegląd statyczny (security/correctness/maintainability)

Zakres: analiza kodu **bez uruchamiania**, przede wszystkim `server/security.py`, `server/auth_routes.py`, `server/middleware.py`, `server/app.py`, `server/validation.py`, `app/helpers/api_client.py`, `app/helpers/signing.py`, `server/services/*`, `server/database/database.py`.

Poniżej: znaleziska pogrupowane per problem. Dla każdego: **klasyfikacja**, **dlaczego to problem**, **pewność**, oraz czy to **definite** czy **heurystyczne podejrzenie**.

---

## 1) Domyślny (słaby) sekret JWT i domyślny klient/sekret w `CLIENTS_JSON`
**Klasyfikacja:** security

**Dlaczego to problem:**
- W `server/security.py` jeśli `JWT_SECRET` nie jest ustawione, aplikacja ustawia `JWT_SECRET = "insecure-default-change-me"`.
- `CLIENTS_JSON` ma domyślną wartość `{"desktop-main": "change-me-in-production"}`.
- W praktyce to znaczy: uruchomienie w niepoprawnie skonfigurowanym środowisku może wystawić serwer, który akceptuje przewidywalne sekrety. Atakujący może wytworzyć ważne JWT (HS256) albo podpisać HMAC znając „sekret” z kodu.

**Pewność:** wysoka

**Status:** definite issue

---

## 2) Brak trwałego (współdzielonego) storage nonce → replay możliwy w klastrze / po restarcie
**Klasyfikacja:** security

**Dlaczego to problem:**
- Anti-replay opiera się o `_nonce_cache` (in-memory `OrderedDict`).
- Po restarcie procesu cache znika → nonce można ponownie użyć.
- Przy wielu workerach/procesach (np. uvicorn/gunicorn z >1 worker) każdy proces ma osobny cache → replay możliwy między workerami.

**Pewność:** wysoka

**Status:** definite issue (w środowiskach wieloprocesowych/HA), w single-process: ograniczenie bezpieczeństwa

---

## 3) `SignatureVerificationMiddleware` bazuje na modyfikacji prywatnego atrybutu `request._receive`
**Klasyfikacja:** correctness / maintainability

**Dlaczego to problem:**
- Middleware czyta body (`await request.body()`), a potem „przywraca” je przez podmianę `request._receive`.
- `_receive` to szczegół implementacyjny Starlette; zmiany wersji mogą to złamać.
- W niektórych przypadkach (streaming/multipart/duże body) taka technika bywa krucha i prowadzi do błędów (np. podwójne odczyty, rozjechane buffery, problemy z backpressure).

**Pewność:** średnia (zależy od wersji Starlette/FastAPI i typów requestów)

**Status:** heuristic suspicion (ryzykowny pattern, często działa, ale jest kruche)

---

## 4) Brak jawnego limitu rozmiaru body przed hash/HMAC → ryzyko DoS
**Klasyfikacja:** security

**Dlaczego to problem:**
- Weryfikacja HMAC liczy `sha256(body)` dla całego body.
- Middleware robi `await request.body()` bez limitu; duże body może zużyć pamięć/CPU (szczególnie jeśli endpointy POST w przyszłości przyjmą większe payloady).
- Sama obecność rate limiting nie zawsze chroni przed dużymi pojedynczymi requestami.

**Pewność:** średnia

**Status:** heuristic suspicion (zależy od deploymentu i typowych body, ale pattern jest DoS-friendly)

---

## 5) CORS: `allow_origins=["http://localhost:*", "http://127.0.0.1:*"]` prawdopodobnie nie działa jak oczekiwano
**Klasyfikacja:** correctness / security

**Dlaczego to problem:**
- `CORSMiddleware` w FastAPI/Starlette nie wspiera wildcardów portu w `allow_origins` w stylu `http://localhost:*` (zwykle wymagane są pełne originy albo regex przez `allow_origin_regex`).
- Skutek:
  - albo CORS nie będzie działać (błędy w przeglądarce),
  - albo ktoś zmieni to „na szybko” na `*` i wtedy robi się ryzykownie.

**Pewność:** średnia

**Status:** heuristic suspicion (bez uruchomienia i bez wersji Starlette nie potwierdzę 100%, ale to typowy problem)

---

## 6) `rate_limit_key()` dekoduje JWT inaczej niż `verify_jwt()` (brak leeway, inne ścieżki błędów)
**Klasyfikacja:** correctness / maintainability

**Dlaczego to problem:**
- `rate_limit_key` robi `jwt.decode(..., JWT_SECRET, algorithms=[JWT_ALGORITHM])` bez `leeway` i bez wspólnej obsługi wyjątków jak w `verify_jwt()`.
- To może powodować niespójność: token jeszcze akceptowany w `require_auth()`/`verify_jwt()` (z leeway), ale rate limiter nie umie go zdekodować → kluczem staje się IP zamiast `client_id`. Daje to inne limity niż zamierzono.

**Pewność:** wysoka

**Status:** definite issue (niespójność logiczna)

---

## 7) `require_session_and_signed_request()` zakłada, że HMAC weryfikuje tylko middleware
**Klasyfikacja:** security / correctness

**Dlaczego to problem:**
- Dependency sprawdza tylko JWT i zgodność `X-Client-Id` z JWT, ale **nie weryfikuje** samego HMAC (komentarz: „w middleware”).
- Jeśli middleware zostanie wyłączony, źle wpięty, albo ktoś doda nowe endpointy i zapomni o `PROTECTED_PATHS`/prefixach, to endpointy będą miały tylko JWT bez „request signing”, mimo że nazwa dependency sugeruje oba mechanizmy.

**Pewność:** średnia

**Status:** heuristic suspicion (zależy od konfiguracji i przyszłych zmian; ryzyko zmian/rozszerzeń)

---

## 8) `PROTECTED_PATHS`/`EXEMPT_PATHS` oparte o `startswith()` — ryzyko „pomyłek w routingu”
**Klasyfikacja:** security / correctness

**Dlaczego to problem:**
- Decyzja o weryfikacji podpisu oparta jest o `path.startswith(prefix)`.
- To zwykle działa, ale bywa podatne na:
  - pomyłki przy dodaniu nowego endpointu (np. `/api2/...` nie będzie chronione),
  - niektóre edge-case’y z „podobnymi prefixami”.
- Lepszy mechanizm: explicit flag per-route (dependency) albo router-level middleware.

**Pewność:** średnia

**Status:** heuristic suspicion

---

## 9) Weryfikacja timestamp HMAC: twarde okno 60s może powodować fałszywe negatywy
**Klasyfikacja:** correctness / availability

**Dlaczego to problem:**
- `verify_request_signature()` wymaga `abs(now - ts) <= 60`.
- Przy driftach zegara, chwilowych opóźnieniach, laptopach „po sleep”, wolnych łączach — może wywalać legalne requesty.
- To nie jest błąd bezpieczeństwa per se, ale wpływa na niezawodność.

**Pewność:** średnia

**Status:** heuristic suspicion

---

## 10) Logowanie wrażliwych danych: zwracanie `str(e)` w HTTP 500
**Klasyfikacja:** security

**Dlaczego to problem:**
- W wielu endpointach w `server/app.py` obsługa błędów robi `raise HTTPException(status_code=500, detail=str(e))`.
- `str(e)` może zawierać:
  - fragmenty zapytań SQL,
  - nazwy tabel/schematów,
  - szczegóły zewnętrznych requestów,
  - ścieżki plików, stack details (czasem).
- Ujawnianie szczegółów wyjątków klientowi zwiększa powierzchnię informacji dla atakującego.

**Pewność:** wysoka

**Status:** definite issue

---

## 11) `DatabaseManager` ma niebezpieczne domyślne poświadczenia (`postgres`/`password`)
**Klasyfikacja:** security

**Dlaczego to problem:**
- `PGPASSWORD` defaultuje do literalnego stringa `"password"`, user do `"postgres"`.
- Jeśli ktoś uruchomi to „na szybko” w środowisku, gdzie DB rzeczywiście ma takie hasło (albo jest wystawiona), to mamy realne ryzyko kompromitacji.

**Pewność:** wysoka

**Status:** definite issue

---

## 12) Budowanie SQL z f-stringów dla `ALTER ROLE ...` i `SET search_path` (ryzyko SQL injection, choć źródło jest env)
**Klasyfikacja:** security

**Dlaczego to problem:**
- W `server/database/database.py` jest:
  - `ALTER ROLE {self.user} IN DATABASE {self.database} SET search_path ...`
  - plus dynamiczne wstawianie `schema`.
- Jeśli `PGUSER`/`PGDATABASE`/`schema` są kontrolowane/zmienione przez atakującego (np. złe zarządzanie `.env`/CI/secrets), to może dojść do „SQL injection” w DDL.
- To nie jest typowy wektor z zewnątrz (to konfiguracja), ale nadal ryzykowne i trudne do audytu.

**Pewność:** średnia

**Status:** heuristic suspicion (zależne od modelu zaufania do env)

---

## 13) `parse_html_tags`: regexowe usuwanie HTML bywa mylące (XSS/HTML-injection w UI zależnie od dalszego użycia)
**Klasyfikacja:** maintainability / security

**Dlaczego to problem:**
- Funkcja w `server/services/parse_html.py` robi prosty `re.sub(r"<[^>]+>", "", html_string)`.
- To nie jest parser HTML. Złożone przypadki (np. `<script>`, `<style>`, komentarze, encje, „broken markup”) mogą być przetwarzane nieintuicyjnie.
- Jeżeli „oczyszczony” tekst jest potem renderowany jako HTML w UI (np. `setHtml` zamiast `setText`), to nadal można wprowadzić XSS/HTML injection. Nie widzę tutaj renderowania UI, więc to zależy od downstream.

**Pewność:** niska do średniej (brakuje kontekstu frontendu)

**Status:** heuristic suspicion

---

## 14) `SteamIDValidator`/`VanityURLValidator`: akceptuje tylko `https://` — poprawność i UX
**Klasyfikacja:** correctness

**Dlaczego to problem:**
- Walidatory uznają URL tylko jeśli zaczyna się od `https://`.
- `http://steamcommunity.com/...` albo brak schematu może się pojawić. To nie jest luka, ale może wywoływać błędy/nieintuicyjne odrzucenia.

**Pewność:** średnia

**Status:** heuristic suspicion

---

## 15) `SteamClient.get_most_played_games()` tworzy taski dla wszystkich wyników bez limitu liczby elementów
**Klasyfikacja:** correctness / availability

**Dlaczego to problem:**
- Jest semaphore=10, ale nadal tworzone są taski dla każdego elementu `items`.
- Jeśli API zwróci bardzo dużo pozycji, liczba tasków może być spora i zużyć pamięć.
- Najczęściej `GetMostPlayedGames` zwraca ograniczoną listę, więc to raczej „edge case”.

**Pewność:** niska

**Status:** heuristic suspicion

---

## 16) Klient desktopowy: logowanie odpowiedzi błędu z serwera (`e.response.text`) może ujawniać dane w logach klienta
**Klasyfikacja:** security

**Dlaczego to problem:**
- W `app/helpers/api_client.py` przy błędach loguje `e.response.text`.
- Jeśli serwer w przyszłości zwróci wrażliwe informacje (a obecnie czasem zwraca `detail=str(e)`), to wrażliwe szczegóły wylądują w logach użytkownika.

**Pewność:** średnia

**Status:** heuristic suspicion (zależne od tego, gdzie trafiają logi i co serwer zwraca)

---

# Szybka mapa miejsc (dla nawigacji)
- JWT/HMAC: `server/security.py`, `server/middleware.py`, `server/auth_routes.py`
- Rate limiting: `server/app.py` + `server/security.rate_limit_key`
- DB: `server/database/database.py`
- Klient: `app/helpers/api_client.py`, `app/helpers/signing.py`
- Parsowanie HTML: `server/services/parse_html.py`

# Braki kontekstu / ograniczenia
- Nie widziałem pełnego kodu UI (jak renderuje teksty HTML) ani pełnej konfiguracji deploy (liczba workerów, reverse-proxy, maksymalny rozmiar request body). W związku z tym część punktów jest **heurystyczna**.

