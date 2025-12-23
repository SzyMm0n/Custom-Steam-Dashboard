# Raport z analizy kodu przy użyciu modeli LLM
## Projekt: Custom-Steam-Dashboard

---

## 1. Wprowadzenie

Niniejszy raport prezentuje wyniki analizy kodu projektu **Custom-Steam-Dashboard** przeprowadzonej przy użyciu trzech modeli LLM:
- **GPT (LLM A)** – model dostępny w Copilot/ChatGPT
- **Claude (LLM B)** – rodzina Claude 3.x
- **Gemini (LLM C)** – rodzina Gemini

Celem analizy jest:
- Sprawdzenie, jakie klasy problemów zauważają modele językowe
- Porównanie problemów znalezionych przez **reguły Semgrep** z problemami wskazanymi **heurystycznie** przez LLM
- Pokazanie różnic w podejściu: Semgrep (deterministyczne reguły) vs LLM (analiza kontekstowa)

### Ważne założenie

> **Analiza LLM nie jest statyczną analizą kodu (SAST) i nie jest narzędziem bezpieczeństwa.**  
> Jest to **symulacja code review** wykonywanego przez system AI.

---

## 2. Modele i narzędzie

### Użyte modele LLM
| Model           | Oznaczenie w raporcie | Narzędzie |
|-----------------|----------------------|-----------|
| GPT 5.2         | LLM A | Copilot w PyCharm |
| Claude 4.5 Opus | LLM B | Copilot w PyCharm |
| Gemini 3 Pro    | LLM C | Copilot w PyCharm |

### Uwaga metodologiczna
- Nie używamy nieoficjalnych lub marketingowych nazw wersji modeli
- Celem nie jest test konkretnej wersji, lecz porównanie podejść modeli LLM jako klasy narzędzi

---

## 3. Zakres analizowanych plików

Aby porównanie z Semgrepem było sensowne, **LLM analizowały dokładnie ten sam zakres kodu** co analiza statyczna:

### Backend
- `server/` – cały folder serwera

### Frontend
- `app/` – cały folder aplikacji klienckiej

---

## 4. Metodologia

### Jednolity prompt (użyty dla wszystkich modeli)

```text
You are acting as a code reviewer and security-oriented static analysis assistant.

Analyze the following Python source code WITHOUT executing it.

Focus ONLY on:
1) security issues,
2) correctness issues,
3) risky or misleading patterns,
4) maintainability concerns.

Do NOT comment on formatting or style unless it impacts safety or correctness.

For each finding:
- classify it (security / correctness / maintainability),
- explain WHY it might be a problem,
- assess confidence (high / medium / low),
- state whether this is a definite issue or a heuristic suspicion.

If you are unsure or missing context, say so explicitly.
```

### Sposób pracy
- Każdy model otrzymał identyczny prompt i te same pliki źródłowe
- Wyniki zapisane w osobnych plikach Markdown
- Brak modyfikacji wyników przez autora

---

## 5. Wyniki – zestawienie tabelaryczne

### 5.1. Podsumowanie ilościowe

| Model | Liczba findings | Security | Correctness | Maintainability |
|-------|-----------------|----------|-------------|-----------------|
| GPT (LLM A) | 16 | 10 | 4 | 2 |
| Claude (LLM B) | 11+ | 7 | 2 | 2 |
| Gemini (LLM C) | 36 | 18 | 10 | 8 |

### 5.2. Wspólne findings (wykryte przez wszystkie 3 modele)

| Problem | GPT | Claude | Gemini | Semgrep |
|---------|-----|--------|--------|---------|
| Domyślny/słaby JWT_SECRET | ✅ Definite | ✅ Definite | ✅ High | ✅ (hardcoded-jwt-secret) |
| Domyślny CLIENTS_JSON | ✅ Definite | ✅ Definite | ✅ High | ❌ |
| In-memory nonce cache (brak persistence) | ✅ Definite | ✅ Medium | ✅ Medium | ❌ |
| Modyfikacja `request._receive` w middleware | ✅ Heuristic | ✅ Medium | ✅ Medium | ❌ |
| Broad exception disclosure (`str(e)` w HTTP 500) | ✅ Definite | ✅ Low | ✅ Low | ✅ (broad-exception-disclosure) |
| Global mutable state w `app.py` | ❌ | ✅ Medium | ✅ Medium | ❌ |
| SQL z f-strings (dynamiczne nazwy tabel) | ✅ Heuristic | ✅ Medium | ✅ High | ❌ |
| Hardcoded client secret w exectuable | ❌ | ✅ Definite | ✅ High | ❌ |

### 5.3. Unikalne findings per model

#### GPT (LLM A) – unikalne obserwacje:
- `rate_limit_key()` dekoduje JWT inaczej niż `verify_jwt()` (brak leeway) – niespójność logiczna
- Twarde okno 60s dla timestamp HMAC może powodować fałszywe negatywy
- `SteamIDValidator` akceptuje tylko `https://` (brak `http://`)

#### Claude (LLM B) – unikalne obserwacje:
- Potencjalna race condition w walidacji nonce (TOCTOU)
- Error messages ujawniają dokładne różnice czasowe (information leak)
- CORS wildcard pattern `localhost:*` może nie działać jak oczekiwano

#### Gemini (LLM C) – unikalne obserwacje:
- Nieefektywne czyszczenie nonce cache (DoS vector) – O(N) na każdy request
- Regex HTML parsing (`parse_html_tags`) jest niepewny
- `asyncio.create_task` bez referencji może prowadzić do garbage collection
- `QDesktopServices.openUrl` z niezwalidowanym URL
- `QTimer` z asyncio może powodować piętrowanie tasków
- Brak minimum dla długości nonce w `generate_nonce`
- Potencjalny XSS w widgetach Qt z HTML

---

## 6. Porównanie z Semgrepem

### 6.1. Co się pokrywa (wykryte przez oba podejścia)

| Problem | Semgrep | LLM (wszystkie) |
|---------|---------|-----------------|
| Hardcoded JWT secret | ✅ `hardcoded-jwt-secret` (1 finding) | ✅ Wykryte przez wszystkie 3 modele |
| Broad exception disclosure | ✅ `broad-exception-disclosure` (15 findings) | ✅ Wykryte przez wszystkie 3 modele |
| Insecure dependency `require_auth` | ✅ `insecure-dependency-require-auth` (4 findings) | ⚠️ Częściowo (Claude jako heuristic) |

### 6.2. Czego Semgrep nie widzi (wykryte tylko przez LLM)

| Problem | Dlaczego Semgrep nie wykrywa | Modele wykrywające |
|---------|------------------------------|-------------------|
| Domyślny CLIENTS_JSON | Brak reguły dla tej konkretnej zmiennej | GPT, Claude, Gemini |
| In-memory nonce cache | Problem architekturalny, nie wzorzec kodu | GPT, Claude, Gemini |
| Race condition w nonce | Wymaga analizy przepływu danych | Claude |
| Modyfikacja `_receive` | Użycie prywatnych API – trudne do wyrażenia regułą | GPT, Claude, Gemini |
| Client secret w executable | Wymaga zrozumienia procesu budowania | Claude, Gemini |
| SQL injection przez f-strings na identyfikatorach | Częściowe – zależy od kontekstu użycia | GPT, Claude, Gemini |
| CORS wildcards nie działają | Wymaga znajomości semantyki biblioteki | GPT, Claude |
| `rate_limit_key` vs `verify_jwt` niespójność | Wymaga porównania logiki dwóch funkcji | GPT |
| HTML regex parsing jako sanityzacja | Wymaga zrozumienia ograniczeń regex | GPT, Gemini |

### 6.3. Czego LLM nie widzi (wykryte tylko przez Semgrep)

| Problem | Semgrep Finding | Uwagi |
|---------|-----------------|-------|
| `insecure-dependency-require-auth` – wszystkie 4 lokalizacje | Precyzyjne wykrycie w konkretnych liniach | LLM zauważa problem ogólnie, ale nie wszystkie lokalizacje |

### 6.4. Analiza jakościowa

#### Mocne strony Semgrep:
- **Deterministyczne wyniki** – zawsze te same findings dla tego samego kodu
- **Precyzyjne lokalizacje** – dokładny plik i linia
- **Powtarzalność** – możliwość integracji z CI/CD
- **Skalowalność** – działa na dużych bazach kodu
- **Brak false positives z "halucynacji"**

#### Mocne strony LLM:
- **Wykrywanie problemów architekturalnych** – np. brak persistence dla nonce cache
- **Zrozumienie kontekstu biznesowego** – np. implikacje embeddingu sekretów w executable
- **Wykrywanie niespójności logicznych** – np. różnice między `rate_limit_key` a `verify_jwt`
- **Ocena ryzyka** – subiektywna ocena powagi problemu
- **Rekomendacje naprawcze** – sugestie jak naprawić problem
- **Wykrywanie wzorców trudnych do wyrażenia regułami** – np. race conditions

---

## 7. Ograniczenia analizy

### 7.1. Ograniczenia metodologiczne

1. **Brak deterministyczności LLM** – wyniki mogą się różnić przy ponownym uruchomieniu
2. **Możliwość halucynacji** – modele mogą "widzieć" problemy, które nie istnieją
3. **Brak pełnego kontekstu aplikacji** – modele nie wiedzą jak kod jest deployowany
4. **Ograniczenie okna kontekstowego** – duże pliki mogą być analizowane fragmentarycznie

### 7.2. Ograniczenia specyficzne dla tego projektu

1. **Brak analizy runtime** – nie wiemy jak zachowuje się aplikacja pod obciążeniem
2. **Brak pełnej konfiguracji deploy** – liczba workerów, reverse-proxy, maksymalny rozmiar request body nieznane
3. **Frontend UI** – nie wszystkie pliki UI zostały w pełni przeanalizowane
4. **Różnice w głębokości analizy** – Gemini zwrócił znacznie więcej findings niż pozostałe modele

### 7.3. Ryzyko nadmiernego zaufania do AI

> **OSTRZEŻENIE:** Wyniki analizy LLM nie powinny być traktowane jako definitywna ocena bezpieczeństwa.  
> LLM generuje **hipotezy**, nie dowody. Każdy finding wymaga ręcznej weryfikacji.

---

## 8. Wnioski edukacyjne

### 8.1. Kiedy używać Semgrep?

- ✅ W procesie CI/CD jako automatyczny gatekeeper
- ✅ Do wykrywania znanych, powtarzalnych wzorców luk
- ✅ Gdy potrzebujemy audytowalności i powtarzalności
- ✅ Na dużych bazach kodu gdzie LLM by nie dał rady

### 8.2. Kiedy używać LLM?

- ✅ Jako "drugi pair of eyes" podczas code review
- ✅ Do wykrywania problemów architekturalnych
- ✅ Gdy szukamy niespójności logicznych między modułami
- ✅ Do generowania hipotez do dalszej weryfikacji

### 8.3. Optymalne podejście

**Kombinacja obu narzędzi:**
1. **Semgrep** jako pierwsza linia obrony (automatycznie w CI)
2. **LLM** jako dodatkowa warstwa dla nowych modułów lub refaktoryzacji
3. **Ręczny review** dla findings z obu źródeł

### 8.4. Wartość edukacyjna projektu

1. **LLM nie zastępuje SAST** – ale może być cennym uzupełnieniem
2. **Różne modele widzą różne rzeczy** – warto używać więcej niż jednego
3. **Gemini był najbardziej "wyczerpujący"** – ale to może oznaczać więcej false positives
4. **Claude i GPT były bardziej konserwatywne** – skupiały się na najważniejszych problemach
5. **Wspólne findings są najbardziej wiarygodne** – jeśli 3 modele zgadzają się, problem prawdopodobnie istnieje

---

## 9. Podsumowanie

### Kluczowe ustalenia:

| Aspekt | Semgrep | LLM |
|--------|---------|-----|
| Liczba findings | 20 | 16-36 (zależnie od modelu) |
| Deterministyczność | ✅ Pełna | ❌ Brak |
| Pokrycie architekturalne | ❌ Ograniczone | ✅ Dobre |
| False positives | Niskie | Średnie do wysokie |
| Integracja z CI/CD | ✅ Natywna | ❌ Wymaga dodatkowej pracy |
| Wykrywanie niespójności logicznych | ❌ Brak | ✅ Dobre |
| Rekomendacje naprawcze | ❌ Brak | ✅ Wbudowane |

### Najważniejsze problemy znalezione przez oba podejścia:

1. **Hardcoded/insecure default secrets** (JWT_SECRET, CLIENTS_JSON)
2. **Information disclosure przez exception handling**
3. **Brak persistence dla mechanizmów anti-replay**
4. **Potencjalne SQL injection przez dynamiczne identyfikatory**
5. **Client secrets embedded w executable**

---

## Załączniki

- `GPT_Analysis.md` – pełny raport LLM A
- `Claude_Analysis.md` – pełny raport LLM B
- `Gemini_Analysis.md` – pełny raport LLM C
- `semgrep/reports/A_BACKEND_AUTH_REPORT.md` – raport Semgrep

---

*Raport wygenerowany: 2025-12-23*  
*Projekt: Custom-Steam-Dashboard*  
*Cel: porównanie analizy LLM z analizą Semgrep dla celów edukacyjnych*

