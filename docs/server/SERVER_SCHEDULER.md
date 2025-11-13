# Dokumentacja Schedulera

**Data aktualizacji:** 2025-11-13  
**Wersja:** 2.0

## Spis Treści

1. [Przegląd](#przegląd)
2. [Zadania Cykliczne](#zadania-cykliczne)
3. [Klasa SchedulerManager](#klasa-schedulermanager)
4. [Konfiguracja](#konfiguracja)

---

## Przegląd

**SchedulerManager** zarządza zadaniami cyklicznymi w Custom Steam Dashboard używając **APScheduler**.

**Plik:** `server/scheduler.py`

### Funkcjonalności

- ✅ Aktualizacja liczby graczy co 5 minut
- ✅ Agregacja danych co godzinę
- ✅ Agregacja danych co dzień
- ✅ Automatyczny start/stop przy uruchomieniu/wyłączeniu serwera

---

## Zadania Cykliczne

### 1. **Update Player Counts** (co 5 minut)

**Zadanie:** Pobiera aktualną liczbę graczy dla wszystkich gier z watchlisty.

```python
async def _update_player_counts_task(self):
    """
    Aktualizuje liczby graczy dla watchlisty.
    Wykonywane: co 5 minut
    """
    try:
        logger.info("Starting player counts update...")
        
        # 1. Pobierz appids z watchlisty
        watchlist = await self.db.get_watchlist()
        appids = [game['appid'] for game in watchlist]
        
        if not appids:
            logger.warning("Watchlist is empty, skipping update")
            return
        
        # 2. Pobierz aktualne liczby graczy z Steam
        player_data = await self.steam_client.get_player_counts_batch(appids)
        
        if not player_data:
            logger.warning("No player data retrieved")
            return
        
        # 3. Zapisz surowe dane do player_counts_raw
        await self.db.save_player_counts(player_data)
        
        # 4. Aktualizuj watchlist
        await self.db.update_watchlist_players(player_data)
        
        logger.info(f"Updated player counts for {len(player_data)} games")
        
    except Exception as e:
        logger.error(f"Error updating player counts: {e}", exc_info=True)
```

**Cron:** `*/5 * * * *` (co 5 minut)

---

### 2. **Aggregate Hourly** (co godzinę)

**Zadanie:** Agreguje surowe dane z `player_counts_raw` do `player_counts_hourly`.

```python
async def _aggregate_hourly_task(self):
    """
    Agreguje dane godzinowe.
    Wykonywane: na początku każdej godziny (xx:00)
    """
    try:
        logger.info("Starting hourly aggregation...")
        
        await self.db.aggregate_hourly()
        
        logger.info("Hourly aggregation completed")
        
    except Exception as e:
        logger.error(f"Error in hourly aggregation: {e}", exc_info=True)
```

**Cron:** `0 * * * *` (co godzinę o xx:00)

**Wykonuje:**
1. Oblicza AVG, MAX, MIN dla każdej gry z ostatniej godziny
2. Zapisuje do `player_counts_hourly`
3. Usuwa surowe dane starsze niż 24 godziny

---

### 3. **Aggregate Daily** (codziennie o 00:05)

**Zadanie:** Agreguje dane godzinowe do dziennych.

```python
async def _aggregate_daily_task(self):
    """
    Agreguje dane dzienne.
    Wykonywane: codziennie o 00:05
    """
    try:
        logger.info("Starting daily aggregation...")
        
        await self.db.aggregate_daily()
        
        logger.info("Daily aggregation completed")
        
    except Exception as e:
        logger.error(f"Error in daily aggregation: {e}", exc_info=True)
```

**Cron:** `5 0 * * *` (codziennie o 00:05)

**Wykonuje:**
1. Oblicza AVG, MAX, MIN dla każdej gry z ostatniego dnia
2. Zapisuje do `player_counts_daily`
3. Usuwa dane godzinowe starsze niż 7 dni

---

## Klasa SchedulerManager

**Plik:** `server/scheduler.py`

### Inicjalizacja

```python
class SchedulerManager:
    """
    Zarządza zadaniami cyklicznymi APScheduler.
    """
    
    def __init__(self, db: DatabaseManager, steam_client: SteamClient):
        """
        Args:
            db: Instancja DatabaseManager
            steam_client: Instancja SteamClient
        """
        self.db = db
        self.steam_client = steam_client
        
        # Utwórz scheduler z AsyncIOScheduler
        self.scheduler = AsyncIOScheduler(
            timezone=timezone.utc  # Używaj UTC dla spójności
        )
        
        # Zarejestruj zadania
        self._register_jobs()
```

### Rejestracja Zadań

```python
def _register_jobs(self):
    """Rejestruje wszystkie zadania cykliczne."""
    
    # 1. Aktualizacja liczby graczy (co 5 minut)
    self.scheduler.add_job(
        self._update_player_counts_task,
        trigger=CronTrigger(minute='*/5', timezone=timezone.utc),
        id='update_player_counts',
        name='Update player counts for watchlist',
        replace_existing=True,
        misfire_grace_time=60  # Tolerancja 60 sekund
    )
    logger.info("Registered job: update_player_counts (every 5 minutes)")
    
    # 2. Agregacja godzinowa (co godzinę)
    self.scheduler.add_job(
        self._aggregate_hourly_task,
        trigger=CronTrigger(hour='*', minute=0, timezone=timezone.utc),
        id='aggregate_hourly',
        name='Aggregate hourly player data',
        replace_existing=True,
        misfire_grace_time=300
    )
    logger.info("Registered job: aggregate_hourly (hourly at xx:00)")
    
    # 3. Agregacja dzienna (codziennie o 00:05)
    self.scheduler.add_job(
        self._aggregate_daily_task,
        trigger=CronTrigger(hour=0, minute=5, timezone=timezone.utc),
        id='aggregate_daily',
        name='Aggregate daily player data',
        replace_existing=True,
        misfire_grace_time=600
    )
    logger.info("Registered job: aggregate_daily (daily at 00:05 UTC)")
```

### Uruchamianie i Zatrzymywanie

```python
def start(self):
    """Uruchamia scheduler."""
    if not self.scheduler.running:
        self.scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Wyświetl zarejestrowane zadania
        jobs = self.scheduler.get_jobs()
        logger.info(f"Active jobs: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.id}: {job.name}")
    else:
        logger.warning("Scheduler is already running")

def shutdown(self):
    """Zatrzymuje scheduler."""
    if self.scheduler.running:
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down successfully")
    else:
        logger.warning("Scheduler is not running")
```

---

## Konfiguracja

### Użycie w app.py

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager dla FastAPI."""
    global scheduler_manager
    
    # Startup
    db = await init_db()
    steam_client = SteamClient()
    
    # Inicjalizuj i uruchom scheduler
    scheduler_manager = SchedulerManager(db, steam_client)
    scheduler_manager.start()
    
    yield
    
    # Shutdown
    scheduler_manager.shutdown()
```

### Misfire Grace Time

**Misfire** = sytuacja, gdy zadanie nie mogło zostać wykonane na czas (np. serwer był wyłączony).

```python
misfire_grace_time=60  # Tolerancja 60 sekund
```

- Jeśli zadanie spóźni się o mniej niż 60s, zostanie wykonane
- Jeśli spóźni się o więcej, zostanie pominięte

---

## Monitorowanie

### Logi

Każde zadanie loguje swoje wykonanie:

```
[INFO] Starting player counts update...
[INFO] Updated player counts for 100 games
[INFO] Starting hourly aggregation...
[INFO] Hourly aggregation completed
```

### Health Check

Endpoint `/health` pokazuje status schedulera:

```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running"
}
```

---

## Harmonogram Zadań

| Zadanie | Częstotliwość | Cron | Czas wykonania |
|---------|---------------|------|----------------|
| Update Player Counts | Co 5 minut | `*/5 * * * *` | ~10-30s |
| Aggregate Hourly | Co godzinę | `0 * * * *` | ~5-15s |
| Aggregate Daily | Codziennie | `5 0 * * *` | ~5-15s |

---

## Timezone

**Ważne:** Wszystkie zadania używają **UTC timezone** dla spójności.

```python
from datetime import timezone

scheduler = AsyncIOScheduler(timezone=timezone.utc)
```

To zapewnia, że zadania działają poprawnie niezależnie od strefy czasowej serwera.

---

## Troubleshooting

### Scheduler nie uruchamia się

```python
# Sprawdź logi
[ERROR] Failed to start scheduler: ...
```

**Rozwiązanie:**
- Upewnij się, że `asyncio` event loop jest dostępny
- Sprawdź czy baza danych jest podłączona

### Zadania się nie wykonują

```python
# Sprawdź status
scheduler.get_jobs()
```

**Rozwiązanie:**
- Sprawdź czy scheduler jest uruchomiony (`scheduler.running`)
- Sprawdź logi pod kątem błędów w zadaniach
- Zweryfikuj `misfire_grace_time`

### Błędy w zadaniach

Wszystkie wyjątki są łapane i logowane, ale nie przerywają działania schedulera:

```python
try:
    await self._update_player_counts_task()
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    # Scheduler kontynuuje pracę
```

---

## Następne Kroki

- **Services**: [SERVER_SERVICES.md](SERVER_SERVICES.md)
- **API**: [SERVER_API_ENDPOINTS.md](SERVER_API_ENDPOINTS.md)

