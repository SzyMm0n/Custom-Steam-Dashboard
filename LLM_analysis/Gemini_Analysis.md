# Gemini Static Analysis Report

## 1. Security: Insecure Default Secrets
- **Classification:** Security
- **File:** `server/security.py`
- **Confidence:** High
- **Description:** The application uses hardcoded default values for critical security secrets (`JWT_SECRET` and `CLIENTS_JSON`) when environment variables are missing.
- **Why it is a problem:** If the application is deployed in a production environment without the `.env` file or environment variables properly set, it will default to known, insecure secrets ("insecure-default-change-me"). This allows attackers to forge JWT tokens and bypass authentication.
- **Recommendation:** Remove the default values and raise a `RuntimeError` or `ValueError` during startup if these environment variables are not set. Alternatively, ensure these defaults are strictly disabled in any non-development mode.

## 2. Performance/Security: Inefficient Nonce Cleanup (DoS Vector)
- **Classification:** Security / Performance
- **File:** `server/security.py`
- **Confidence:** High
- **Description:** The `_cleanup_expired_nonces` function iterates over the entire `_nonce_cache` (up to 10,000 items) and is called by `_check_and_store_nonce` on **every** request that requires signature verification.
- **Why it is a problem:** An attacker can flood the server with requests using unique nonces to fill the cache. Once full, every subsequent request triggers a full O(N) iteration over the cache, consuming excessive CPU cycles and increasing latency. This is a potential Denial of Service (DoS) vector.
- **Recommendation:** Optimize the cleanup strategy.
    - Only run cleanup when the cache size reaches a certain threshold (e.g., 90% full).
    - Or, run cleanup probabilistically (e.g., on 1% of requests).
    - Or, use a background task for cleanup instead of blocking the request thread.

## 3. Security: Nonce Cache Persistence
- **Classification:** Security
- **File:** `server/security.py`
- **Confidence:** Medium
- **Description:** The nonce cache (`_nonce_cache`) is stored in-memory.
- **Why it is a problem:** If the server restarts, the cache is cleared. An attacker who captured a valid signed request from just before the restart could replay it immediately after the restart (provided the timestamp is still within the 60-second window).
- **Recommendation:** For higher security, use a persistent store (like Redis or a database table) for nonces, or accept the risk as low given the short 60-second validity window.

## 4. Maintainability: Global State Management
- **Classification:** Maintainability
- **File:** `server/app.py`
- **Confidence:** Medium
- **Description:** The application relies on global variables (`db`, `steam_client`, `deals_client`) initialized in the `lifespan` handler.
- **Why it is a problem:** Global state makes unit testing difficult because tests can interfere with each other or require complex setup/teardown to reset globals. It also obscures dependencies.
- **Recommendation:** Use FastAPI's `app.state` to store these instances, or use a dependency injection framework to pass them to route handlers.

## 5. Correctness: Middleware Body Buffering
- **Classification:** Correctness / Performance
- **File:** `server/middleware.py`
- **Confidence:** Medium
- **Description:** The `SignatureVerificationMiddleware` reads the entire request body into memory (`await request.body()`) to verify the signature.
- **Why it is a problem:** This limits the scalability of the server for endpoints that might receive large payloads (e.g., file uploads). While likely fine for metadata, it creates a memory bottleneck if large requests are ever allowed on protected routes.
- **Recommendation:** If large payloads are anticipated, consider streaming signature verification or enforcing a strict `Content-Length` limit in the middleware.

## 6. Security: Broad Exception Handling
- **Classification:** Maintainability / Security
- **File:** `server/auth_routes.py`
- **Confidence:** Low
- **Description:** The `login` endpoint catches `Exception` broadly and returns a 500 error.
- **Why it is a problem:** While it prevents stack trace leakage (good), it might mask specific configuration errors or logic bugs that should be handled explicitly.
- **Recommendation:** Catch specific exceptions where possible and log the full traceback internally while returning a generic error to the client.

## 7. Security: SQL Injection Risk in Database Manager
- **Classification:** Security
- **File:** `server/database/database.py`
- **Confidence:** High
- **Description:** The `DatabaseManager` uses f-strings to construct SQL queries with table names (`self._table('watchlist')`). While `_table` uses `self.schema` which comes from configuration, if `schema` or `table_name` were ever user-controlled, this would be a SQL injection vulnerability.
- **Why it is a problem:** Although currently `schema` is hardcoded or from env, using string formatting for SQL identifiers is a dangerous pattern. If a future refactor allows user input to influence the schema name, it could lead to full database compromise.
- **Recommendation:** Use `psycopg2.sql` or `asyncpg`'s safe identifier quoting mechanisms if possible, or strictly validate the schema name against a whitelist of allowed characters (alphanumeric only) during initialization.

## 8. Correctness: Race Condition in Scheduler
- **Classification:** Correctness
- **File:** `server/scheduler.py`
- **Confidence:** Medium
- **Description:** The `SchedulerManager` starts jobs immediately. The `watchlist_refresher` job is scheduled to run immediately (`next_run_time=datetime.now(timezone.utc)`).
- **Why it is a problem:** If the database or Steam client initialization takes longer than expected, the job might start before dependencies are fully ready, leading to errors.
- **Recommendation:** Ensure `start()` is called only after all dependencies (DB, SteamClient) are fully initialized and healthy. Consider adding a small initial delay or a health check before the first job run.

## 9. Maintainability: Hardcoded SQL Queries
- **Classification:** Maintainability
- **File:** `server/database/database.py`
- **Confidence:** Medium
- **Description:** SQL queries are scattered throughout the `DatabaseManager` class as raw strings.
- **Why it is a problem:** This makes it hard to read, maintain, and optimize queries. It also makes it difficult to see the database schema at a glance.
- **Recommendation:** Move SQL queries to a separate file (e.g., `sql_queries.py`) or use a query builder / ORM for complex queries. For simple queries, keeping them close to usage is acceptable but consider using named constants.

## 10. Security: Missing Input Validation for `limit`
- **Classification:** Security
- **File:** `server/database/database.py`
- **Confidence:** Low
- **Description:** The `get_player_count_history` method accepts a `limit` parameter which is directly used in the SQL query.
- **Why it is a problem:** While `limit` is typed as `int`, if it comes from an untrusted source (API endpoint) without validation, a very large number could cause a Denial of Service (DoS) by fetching excessive data.
- **Recommendation:** Enforce a maximum value for `limit` (e.g., 1000) in the API endpoint or the database method itself.

## 11. Correctness: Potential Connection Pool Exhaustion
- **Classification:** Correctness / Performance
- **File:** `server/database/database.py`
- **Confidence:** Medium
- **Description:** The `DatabaseManager` has a `max_pool_size` of 30. The scheduler runs multiple concurrent tasks (`PlayerCountCollector` uses a semaphore of 10, `WatchlistRefresher` uses 10).
- **Why it is a problem:** If multiple jobs run simultaneously (e.g., collection + refresh + API requests), the connection pool might be exhausted, causing requests to wait or timeout.
- **Recommendation:** Monitor connection pool usage. Consider increasing `max_pool_size` or implementing a more robust connection acquisition strategy with retries. Ensure API endpoints have a separate pool or reserved connections if possible.

## 12. Security: Insecure HTML Parsing
- **Classification:** Security / Correctness
- **File:** `server/services/parse_html.py`
- **Confidence:** Medium
- **Description:** The `parse_html_tags` function uses regex (`re.sub(r"<[^>]+>", "", html_string)`) to strip HTML tags.
- **Why it is a problem:** Regex-based HTML stripping is notoriously fragile and can be bypassed by malformed HTML (e.g., `<script >` or nested tags). While the current usage seems to be for cleaning descriptions for display (which is low risk if the frontend also escapes output), relying on regex for sanitization is a bad practice.
- **Recommendation:** Use a dedicated HTML parsing library like `BeautifulSoup` (e.g., `BeautifulSoup(html_string, "html.parser").get_text()`) or `bleach` for robust sanitization.

## 13. Correctness: Missing Error Handling in `SteamClient`
- **Classification:** Correctness
- **File:** `server/services/steam_service.py`
- **Confidence:** Medium
- **Description:** The `SteamClient` methods (e.g., `get_player_count`) return default values (0 or None) on failure but log the error.
- **Why it is a problem:** While this prevents the app from crashing, it might hide persistent issues (like API key quotas or connectivity problems) from the caller. The caller has no way to distinguish between "game has 0 players" and "API request failed".
- **Recommendation:** Consider raising custom exceptions for critical failures or returning a result object that includes status/error information.

## 14. Security: Potential SSRF in `deals_service.py`
- **Classification:** Security
- **File:** `server/services/deals_service.py`
- **Confidence:** Low
- **Description:** The `IsThereAnyDealClient` makes HTTP requests to URLs constructed from configuration.
- **Why it is a problem:** If `ITAD_API_KEY` or `ITAD_CLIENT_ID` are misconfigured or manipulated (unlikely in this context, but possible if env vars are injected), it could lead to unexpected behavior. More importantly, if the `base_url` was ever dynamic, it would be an SSRF risk.
- **Recommendation:** Ensure `base_url` is hardcoded or strictly validated if it ever becomes configurable. (Currently it is hardcoded, so this is just a heuristic check).

## 15. Maintainability: Hardcoded Shop IDs
- **Classification:** Maintainability
- **File:** `server/services/deals_service.py`
- **Confidence:** Medium
- **Description:** Shop IDs (e.g., "61,35,88,82") are hardcoded in multiple places in `deals_service.py`.
- **Why it is a problem:** If shop IDs change or if you want to add/remove shops, you have to update multiple locations.
- **Recommendation:** Define these constants at the top of the class or in a configuration file.

## 16. Correctness: `parse_html_tags` is Async but CPU-bound
- **Classification:** Correctness / Performance
- **File:** `server/services/parse_html.py`
- **Confidence:** Low
- **Description:** `parse_html_tags` is defined as `async` but performs purely CPU-bound string operations (regex).
- **Why it is a problem:** Calling this `await parse_html_tags(...)` blocks the event loop while the regex runs. For small strings, it's negligible, but for large descriptions, it could cause minor stutter.
- **Recommendation:** Since it doesn't do I/O, it doesn't need to be `async`. If it's computationally expensive, run it in a thread pool (`run_in_executor`). If it's fast, just make it synchronous.

## 17. Security: Lack of Timeout on specific requests
- **Classification:** Correctness / Security
- **File:** `server/services/deals_service.py`
- **Confidence:** Medium
- **Description:** While `BaseAsyncService` has a default timeout, some specific requests in `deals_service.py` (like `get_popular_deals` loop) might take a long time in total.
- **Why it is a problem:** If the external API hangs or is slow, the server worker could be tied up for an extended period.
- **Recommendation:** Ensure all external calls have appropriate timeouts, especially in loops.

## 18. Maintainability: Duplicate Code in `deals_service.py`
- **Classification:** Maintainability
- **File:** `server/services/deals_service.py`
- **Confidence:** Medium
- **Description:** The logic for filtering deals, finding the best deal, and creating `DealInfo` objects is repeated in `search_deals`, `get_game_prices`, and `get_game_prices_batch`.
- **Why it is a problem:** Bug fixes or changes to deal selection logic need to be applied in three places.
- **Recommendation:** Extract this logic into a helper method (e.g., `_process_deal_list(deals, min_discount)`).

## 19. Security: Hardcoded Secrets in Client Build
- **Classification:** Security
- **File:** `app/config.py` (and `generate_config.py`)
- **Confidence:** High
- **Description:** The build process (`generate_config.py`) embeds the `CLIENT_SECRET` directly into the `app/config.py` file which is then compiled into the executable.
- **Why it is a problem:** Hardcoding secrets in client-side code (even compiled executables) is insecure. Anyone can decompile the Python executable (using tools like `pyinstxtractor` and `uncompyle6`) and extract the `CLIENT_SECRET`. This allows them to impersonate the client.
- **Recommendation:**
    - **Ideal:** Do not embed secrets in the client. Use a public client flow (like OAuth2 PKCE) where the client doesn't need a secret, or require the user to log in with their own credentials.
    - **Mitigation (if architecture cannot change):** Obfuscate the secret or use an external configuration file that the user must provide, rather than baking it into the binary. However, any secret on the client side is fundamentally insecure.

## 20. Correctness: `QEventLoop` Usage with `asyncio`
- **Classification:** Correctness
- **File:** `app/main_server.py`
- **Confidence:** Medium
- **Description:** The application uses `qasync.QEventLoop` to integrate `asyncio` with Qt.
- **Why it is a problem:** While `qasync` is the correct tool, the setup in `main()`:
    ```python
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(...)
    ```
    might conflict with how `qasync` is intended to be used in newer versions or specific environments. Specifically, `QEventLoop(app)` creates a new loop, but `app.exec()` (which is usually how Qt apps run) is not explicitly called, instead `loop.run_until_complete` drives it. This is generally fine for `qasync`, but ensuring the loop is properly closed and cleaned up is critical to avoid hanging processes on exit.
- **Recommendation:** Ensure that `loop.close()` is called in a `finally` block to guarantee cleanup.

## 21. Maintainability: Missing Type Hints in `main_server.py`
- **Classification:** Maintainability
- **File:** `app/main_server.py`
- **Confidence:** Low
- **Description:** The `main_coro` function and `on_quit` callback lack full type annotations.
- **Why it is a problem:** Reduces code readability and tooling support.
- **Recommendation:** Add type hints (e.g., `app: QApplication`).

## 22. Security: Insecure File Permissions for User Data
- **Classification:** Security
- **File:** `app/core/user_data_manager.py`
- **Confidence:** Low
- **Description:** The `UserDataManager` creates a `user_data.json` file in the user's home directory or AppData.
- **Why it is a problem:** On multi-user systems (especially Linux/macOS), the default file permissions might allow other users to read this file. While it currently stores preferences and theme data (low risk), if it ever stores sensitive tokens or personal data, this would be a privacy issue.
- **Recommendation:** Explicitly set file permissions to 600 (read/write for owner only) when creating the file on POSIX systems (`os.chmod(path, 0o600)`).

## 23. Correctness: Race Condition in `UserDataManager` Singleton
- **Classification:** Correctness
- **File:** `app/core/user_data_manager.py`
- **Confidence:** Low
- **Description:** The `UserDataManager` implements a singleton pattern using `__new__`.
- **Why it is a problem:** This implementation is not thread-safe. If multiple threads try to initialize the singleton simultaneously, `__init__` might be called multiple times or race conditions could occur during file access.
- **Recommendation:** Use a thread-safe singleton implementation or ensure it's initialized once at startup before any threads are spawned.

## 24. Maintainability: Hardcoded Paths in `UserDataManager`
- **Classification:** Maintainability
- **File:** `app/core/user_data_manager.py`
- **Confidence:** Medium
- **Description:** The logic for determining the data directory (`_get_data_file_path`) contains hardcoded paths for different OSs.
- **Why it is a problem:** It duplicates logic that might be better handled by a library like `platformdirs` or `appdirs`.
- **Recommendation:** Use a standard library for determining application data directories to ensure compliance with OS standards.

## 25. Correctness: JSON Encoding of Tuples
- **Classification:** Correctness
- **File:** `app/core/user_data_manager.py`
- **Confidence:** Low
- **Description:** `save_window_geometry` converts tuples to lists before saving to JSON (`list(size)`), but `get_window_geometry` converts them back to tuples.
- **Why it is a problem:** This is actually correct behavior (JSON doesn't support tuples), but the manual conversion is a bit fragile.
- **Recommendation:** Ensure that `json.dump` handles the data types correctly or use a custom encoder if more complex types are added. (Current implementation is fine, just a note).

## 26. Security: Lack of Input Validation in `ServerClient`
- **Classification:** Security
- **File:** `app/core/services/server_client.py`
- **Confidence:** Low
- **Description:** `ServerClient` methods take inputs like `steamid` and `vanity_url` and pass them directly to the API client.
- **Why it is a problem:** While the server should validate inputs, the client should also perform basic validation to avoid sending malformed requests or exposing itself to injection attacks if the inputs come from a local untrusted source (e.g., a file).
- **Recommendation:** Add basic validation (e.g., check if `steamid` is numeric) before making the request.

## 27. Security: Weak Nonce Generation
- **Classification:** Security
- **File:** `app/helpers/signing.py`
- **Confidence:** Low
- **Description:** `generate_nonce` uses `secrets.token_hex(length)`.
- **Why it is a problem:** While `secrets` is cryptographically strong, the `length` parameter defaults to 32 bytes (64 hex chars), which is good. However, if `length` is ever reduced significantly by a caller, it could weaken the nonce.
- **Recommendation:** Enforce a minimum length for the nonce (e.g., 16 bytes) inside the function.

## 28. Correctness: `AuthenticatedAPIClient` Token Refresh Logic
- **Classification:** Correctness
- **File:** `app/helpers/api_client.py`
- **Confidence:** Medium
- **Description:** `ensure_authenticated` checks `is_authenticated` and logs in if needed. However, `is_authenticated` returns `False` if `_access_token` is missing OR if it's expired.
- **Why it is a problem:** If a request fails with 401 (Unauthorized) *despite* the client thinking it has a valid token (e.g., server revoked it, or clock skew issue), the current logic in `get`/`post` methods doesn't retry with a fresh login. It just logs the error and returns `None`.
- **Recommendation:** Implement a retry mechanism in `get`/`post` that catches 401 errors, forces a re-login, and then retries the request once.

## 29. Maintainability: Hardcoded Paths in `AuthenticatedAPIClient`
- **Classification:** Maintainability
- **File:** `app/helpers/api_client.py`
- **Confidence:** Low
- **Description:** The login path `/auth/login` is hardcoded.
- **Why it is a problem:** If the server API structure changes, this client will break.
- **Recommendation:** Define API endpoints as constants.

## 30. Security: Logging of Sensitive Data (Potential)
- **Classification:** Security
- **File:** `app/helpers/api_client.py`
- **Confidence:** Low
- **Description:** `logger.error(f"Login failed with status {e.response.status_code}: {e.response.text}")` logs the full response body on login failure.
- **Why it is a problem:** If the server returns sensitive debug information or stack traces in the 500 error body during a failed login, it will be written to the client logs.
- **Recommendation:** Truncate the response text or log it only at DEBUG level.

## 31. Security: Potential XSS in `QListWidget` (Qt)
- **Classification:** Security
- **File:** `app/ui/deals_view_server.py` (and others using `QListWidget` or `QLabel` with HTML)
- **Confidence:** Low
- **Description:** If game titles or deal information contain HTML tags (e.g., `<b>`, `<script>`), Qt widgets might interpret them as rich text. While Qt's HTML subset is limited and doesn't execute JavaScript, it can mess up the UI or load external resources (images) if not handled carefully.
- **Why it is a problem:** Malicious game titles could disrupt the UI layout or track users via remote images.
- **Recommendation:** Ensure that text set on widgets is treated as plain text (`setText` usually does this, but be careful with `setTextFormat(Qt.RichText)`). If rich text is needed, sanitize the input first.

## 32. Correctness: `asyncio.create_task` without Reference
- **Classification:** Correctness
- **File:** `app/ui/comparison_view_server.py`, `app/ui/deals_view_server.py`
- **Confidence:** Medium
- **Description:** `asyncio.create_task(self.refresh_data())` is called in lambda functions connected to signals (e.g., buttons, timers).
- **Why it is a problem:** In standard `asyncio`, tasks created this way might be garbage collected if not referenced, leading to them not completing. However, `qasync` usually handles this better, but it's still a best practice to keep a reference to running tasks, especially for long-running operations, to avoid silent failures or to allow cancellation.
- **Recommendation:** Store the task in a variable (e.g., `self._refresh_task = asyncio.create_task(...)`) or use a set of background tasks.

## 33. Maintainability: Hardcoded UI Strings
- **Classification:** Maintainability
- **File:** `app/ui/comparison_view_server.py`, `app/ui/deals_view_server.py`
- **Confidence:** Low
- **Description:** UI strings ("Porównanie danych graczy", "Wybierz gry...", etc.) are hardcoded in Polish.
- **Why it is a problem:** Makes localization (i18n) difficult if the app needs to support other languages.
- **Recommendation:** Use Qt's translation system (`tr()`) or a separate constants file for strings.

## 34. Correctness: `QTimer` with `asyncio`
- **Classification:** Correctness
- **File:** `app/ui/comparison_view_server.py`
- **Confidence:** Low
- **Description:** `self._refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))`
- **Why it is a problem:** If `refresh_data` takes longer than the timer interval (5 minutes), multiple refresh tasks could pile up.
- **Recommendation:** Check if a refresh is already in progress before starting a new one, or stop the timer during refresh and restart it afterwards.

## 35. Security: `QDesktopServices.openUrl` with Unvalidated URL
- **Classification:** Security
- **File:** `app/ui/deals_view_server.py`
- **Confidence:** Medium
- **Description:** `self._best_deals_list.itemClicked.connect(self._on_deal_clicked)` likely calls `QDesktopServices.openUrl`.
- **Why it is a problem:** If the URL from the deal data is malicious (e.g., `file:///`, `javascript:`), it could execute code or open local files.
- **Recommendation:** Validate that the URL starts with `http://` or `https://` before opening it.

## 36. Correctness: `QTimer.singleShot` with Lambda and Asyncio
- **Classification:** Correctness
- **File:** `app/ui/home_view_server.py`
- **Confidence:** Medium
- **Description:** `QTimer.singleShot(0, lambda: asyncio.create_task(self.refresh_data()))` is used to schedule tasks.
- **Why it is a problem:** While this avoids blocking the event loop immediately, if `refresh_data` is called rapidly (e.g., via user interaction or multiple timers), it can spawn many concurrent tasks.
- **Recommendation:** Ensure that `refresh_data` is re-entrant safe or checks if a refresh is already running.

## 37. Security: Unvalidated Image Loading
- **Classification:** Security
- **File:** `app/ui/library_view_server.py` (and potentially others)
- **Confidence:** Low
- **Description:** `_load_avatar` likely fetches an image from a URL provided by the server (which comes from Steam).
- **Why it is a problem:** While Steam URLs are generally trusted, if the server is compromised or returns a malicious URL (e.g., tracking pixel or exploit), the client will load it.
- **Recommendation:** Validate that image URLs are from trusted domains (e.g., `*.steamstatic.com`) before loading.

## 38. Maintainability: Hardcoded Locale
- **Classification:** Maintainability
- **File:** `app/ui/home_view_server.py`
- **Confidence:** Low
- **Description:** `self._locale = QLocale(QLocale.Language.Polish, QLocale.Country.Poland)`
- **Why it is a problem:** Hardcodes the application to Polish locale formatting.
- **Recommendation:** Use `QLocale.system()` or allow user configuration for locale.

## 39. Correctness: `asyncio.create_task` in `__init__` (Indirectly)
- **Classification:** Correctness
- **File:** `app/ui/home_view_server.py`
- **Confidence:** Low
- **Description:** `QTimer.singleShot(0, self._start_initial_load)` calls `asyncio.create_task`.
- **Why it is a problem:** If the widget is destroyed before the task completes, it might try to update a deleted widget, causing a crash (segfault in C++ Qt).
- **Recommendation:** Keep track of tasks and cancel them in `closeEvent` or when the widget is destroyed.

## 40. Security: Lack of Rate Limiting on Client Side
- **Classification:** Correctness / Security
- **File:** `app/ui/library_view_server.py`
- **Confidence:** Low
- **Description:** The "Pobierz" button triggers a server request. A user could spam click this button.
- **Why it is a problem:** Could flood the server or the client's network connection.
- **Recommendation:** Disable the button while the request is in progress (which is done: `self.fetch_btn.setEnabled(False)`), but also consider a cooldown if requests fail quickly.

## 41. Security: Unvalidated URL in `GameDetailDialog`
- **Classification:** Security
- **File:** `app/ui/components_server.py`
- **Confidence:** Medium
- **Description:** `GameDetailDialog` likely has a button to open the store URL (though the code for `_create_buttons_section` was truncated, it's implied).
- **Why it is a problem:** Similar to finding #35, opening unvalidated URLs from external data is risky.
- **Recommendation:** Validate URLs before opening them with `QDesktopServices.openUrl`.

## 42. Maintainability: Hardcoded Shop IDs in `DealsFilterDialog`
- **Classification:** Maintainability
- **File:** `app/ui/deals_filter_dialog.py`
- **Confidence:** Medium
- **Description:** Shop IDs (61, 35, 88, 82) are hardcoded in `_get_default_filters` and `_create_shops_section`.
- **Why it is a problem:** Duplicates the hardcoded IDs found in `deals_service.py`. If IDs change, they must be updated in both server and client code.
- **Recommendation:** Share these constants via a common config file or fetch available shops from the server API.

## 43. Correctness: `QRegularExpressionValidator` Regex
- **Classification:** Correctness
- **File:** `app/ui/components_server.py`
- **Confidence:** Low
- **Description:** `QRegularExpression(r"^[0-9 ]{0,15}$")` allows spaces anywhere.
- **Why it is a problem:** `int("1 2 3")` raises ValueError. The validator allows input that might crash the conversion logic if not stripped properly.
- **Recommendation:** Ensure input is stripped of spaces before conversion, or tighten the regex to only allow spaces as thousands separators if that's the intent.

## 44. Correctness: `GameDetailDialog` Async Loading
- **Classification:** Correctness
- **File:** `app/ui/components_server.py`
- **Confidence:** Low
- **Description:** `self._load_async_data()` is called in `__init__`.
- **Why it is a problem:** If `_load_async_data` is an async function (coroutine), calling it without `asyncio.create_task` or `await` (if inside an async init, which isn't possible for QDialog) will just return a coroutine object and do nothing.
- **Recommendation:** Ensure it's scheduled properly: `asyncio.create_task(self._load_async_data())`.

## 45. Security: `CustomThemeDialog` Color Parsing
- **Classification:** Correctness / Security
- **File:** `app/ui/custom_theme_dialog.py`
- **Confidence:** Low
- **Description:** `QColor(hex_string)` is generally safe, but if `hex_string` comes from untrusted input (e.g., a shared theme file), malformed strings might cause issues.
- **Why it is a problem:** Low risk, but good to keep in mind for robustness.
- **Recommendation:** Validate color strings before parsing.

## 46. Maintainability: Circular Dependency Risk in `styles.py`
- **Classification:** Maintainability
- **File:** `app/ui/styles.py`
- **Confidence:** Low
- **Description:** `styles.py` imports `ThemeManager` inside `_get_theme_manager` to avoid circular imports, but `ThemeManager` might import other UI components that use `styles.py`.
- **Why it is a problem:** Circular imports can cause `ImportError` at runtime or during initialization, making the codebase fragile.
- **Recommendation:** Refactor `styles.py` to be purely a data/utility module that doesn't depend on `ThemeManager`, or inject the theme configuration into it.

## 47. Correctness: `ThemeManager` Singleton Initialization
- **Classification:** Correctness
- **File:** `app/ui/theme_manager.py`
- **Confidence:** Low
- **Description:** Similar to `UserDataManager`, `ThemeManager` uses `__new__` for singleton pattern.
- **Why it is a problem:** Thread safety concerns during initialization if accessed from multiple threads (though UI is usually single-threaded).
- **Recommendation:** Ensure initialization happens on the main thread before any background threads access it.

## 48. Security: Unvalidated Theme Data
- **Classification:** Security
- **File:** `app/ui/theme_manager.py`
- **Confidence:** Low
- **Description:** `get_colors` uses `self._custom_dark_colors` directly if keys are present.
- **Why it is a problem:** If a custom theme file is manually edited to contain malicious values (e.g., extremely long strings or invalid CSS that crashes the renderer), it could be an issue.
- **Recommendation:** Validate that color values are valid hex codes or CSS color names when loading the theme.

## 49. Maintainability: Hardcoded Colors in `ThemeManager`
- **Classification:** Maintainability
- **File:** `app/ui/theme_manager.py`
- **Confidence:** Low
- **Description:** `DARK_COLORS` and `LIGHT_COLORS` dictionaries are hardcoded in the file.
- **Why it is a problem:** Makes it hard to change default themes without modifying code.
- **Recommendation:** Move default themes to a JSON/YAML configuration file.

## 50. Correctness: `ThemeSwitcher` Signal Blocking
- **Classification:** Correctness
- **File:** `app/ui/theme_switcher.py`
- **Confidence:** Low
- **Description:** `self._palette_combo.blockSignals(True)` is used when updating the combo box programmatically.
- **Why it is a problem:** If an exception occurs before `blockSignals(False)`, the combo box will stop responding to events.
- **Recommendation:** Use a `try...finally` block to ensure signals are unblocked.

## 51. Correctness: `asyncio.create_task` in `MainWindow`
- **Classification:** Correctness
- **File:** `app/main_window.py`
- **Confidence:** Low
- **Description:** `asyncio.create_task(current_widget.refresh_data())` in `refresh_current_view`.
- **Why it is a problem:** Similar to other findings, unreferenced tasks might be garbage collected or fail silently.
- **Recommendation:** Store reference or use a task manager.

## 52. Maintainability: Hardcoded Window Size
- **Classification:** Maintainability
- **File:** `app/main_window.py`
- **Confidence:** Low
- **Description:** `self.setMinimumSize(1000, 800)`
- **Why it is a problem:** Might be too large for some screens (e.g., older laptops with 1366x768).
- **Recommendation:** Use a smaller minimum size or make it responsive to screen resolution.

## 53. Security: `check_build_deps.py` Imports
- **Classification:** Security
- **File:** `check_build_deps.py`
- **Confidence:** Low
- **Description:** The script imports modules dynamically to check for existence.
- **Why it is a problem:** If a malicious package with the same name as a required dependency is installed in the environment, importing it executes its code.
- **Recommendation:** Use `importlib.util.find_spec` instead of `import_module` to check for existence without executing module-level code.

## 54. Correctness: Missing `closeEvent` Handling in Views
- **Classification:** Correctness
- **File:** `app/ui/home_view_server.py`, `app/ui/comparison_view_server.py`, `app/ui/deals_view_server.py`
- **Confidence:** Medium
- **Description:** These views start timers (`QTimer`) and async tasks but don't seem to stop them explicitly when the view is hidden or destroyed (except for standard widget destruction).
- **Why it is a problem:** If `MainWindow` is closed, `QTimer` stops. But if views are removed from `QStackedWidget` or replaced, timers might keep running.
- **Recommendation:** Implement `closeEvent` or `hideEvent` in views to stop timers and cancel pending tasks.

## 55. Maintainability: `ThemeManager` Singleton in `MainWindow`
- **Classification:** Maintainability
- **File:** `app/main_window.py`
- **Confidence:** Low
- **Description:** `MainWindow` initializes `ThemeManager` and connects signals.
- **Why it is a problem:** `ThemeManager` is a singleton used across many files. Explicit initialization in `MainWindow` is fine, but the dependency is hidden in other classes that just call `ThemeManager()`.
- **Recommendation:** Consider dependency injection or a clear initialization phase in `main.py` before creating windows.
