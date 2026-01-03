# FRONTEND_CLIENT_C – raport naprawczy (Semgrep)

## Zakres
Na podstawie `FRONTEND_CLIENT_C_SEMGREP_REPORT.md` (analiza Semgrep dla `app/helpers/` oraz `app/core/services/`).

## Kluczowe problemy i działania

1. **Brak obsługi błędów JSON (`frontend-json-decode-error`, 28 miejsc, wysoki priorytet)**
   - *Problem*: `response.json()` bez `try/except` może zakończyć aplikację przy błędnej odpowiedzi.
   - *Działanie*: Owiń w `try/except json.JSONDecodeError`, loguj błąd (status/ścieżka) i zwróć `None` lub bezpieczną wartość.

2. **Logowanie pełnego body błędu HTTP (`frontend-http-error-leak`, np. `app/helpers/api_client.py:96`, średni priorytet)**
   - *Problem*: `e.response.text` w logu może ujawnić dane wrażliwe.
   - *Działanie*: Na poziomie `error` loguj tylko status/kod; pełne body przenieś na poziom `debug` lub usuń w produkcji.

3. **Puste bloki `except` (`frontend-empty-except`, 2 miejsca, niski priorytet)**
   - *Problem*: Ciche ignorowanie błędów utrudnia diagnostykę.
   - *Działanie*: Dodaj `logger.warning/error(...)` i ewentualnie re-raise po logowaniu.

4. **Do przeglądu / potencjalne FP (niski priorytet)**
   - `frontend-http-no-timeout`: upewnij się, że każdy HTTP call ma jawny `timeout`.
   - `frontend-no-secret-logging`: sprawdź, czy logi z "token/secret" nie ujawniają wrażliwych danych.
   - `frontend-request-without-auth`: potwierdź, że brak nagłówków auth jest intencjonalny (np. `/auth/login`).
   - `frontend-url-join-risk`: jeśli łączysz URL-e ręcznie, rozważ `urllib.parse.urljoin`.

## Plan napraw (kolejność)
1) Dodać obsługę błędów JSON we wszystkich miejscach `response.json()`.
2) Ograniczyć logowanie pełnego body odpowiedzi w błędach HTTP (status w `error`, body w `debug`).
3) Uzupełnić logowanie w pustych `except` lub re-raise.
4) Przejrzeć zgłoszenia potencjalnych FP: timeouts, auth headers, secret logging, URL join.

## Gotowe fragmenty (przykłady)
- Bezpieczny JSON decode:
  ```python
  try:
      data = response.json()
  except json.JSONDecodeError:
      logger.error("Invalid JSON from %s", path)
      return None
  ```
- Bezpieczne logowanie błędu HTTP:
  ```python
  logger.error("Request failed: status=%s", e.response.status_code)
  logger.debug("Response body: %s", e.response.text)
  ```
- Blok `except` z logowaniem:
  ```python
  try:
      ...
  except Exception as exc:
      logger.error("Operation failed", exc_info=exc)
      raise
  ```

## Podsumowanie
- **Wysoki:** obsługa błędów JSON.
- **Średni:** ograniczenie logowania pełnego body przy błędach HTTP.
- **Niski:** puste `except` + przegląd potencjalnych FP (timeouts, auth, sekrety, URL join).
