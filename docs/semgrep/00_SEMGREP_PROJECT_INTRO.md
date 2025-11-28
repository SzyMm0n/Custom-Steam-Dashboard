# Projekt: Statyczna analiza Custom-Steam-Dashboard przy użyciu Semgrep

## 1. Cel projektu

W ramach przedmiotu **Statyczna Analiza Oprogramowania** analizujemy naszą aplikację **Custom-Steam-Dashboard** (Python, architektura client–server) przy użyciu narzędzia **Semgrep**.

Chcemy pokazać:

- jak Semgrep działa w praktyce,
- jakie problemy potrafi wykryć (bezpieczeństwo, błędy, code smelly),
- jak napisać **własne reguły Semgrep** dopasowane do naszej aplikacji,
- jak takie narzędzie można włączyć w proces wytwarzania oprogramowania (CI / code review).

Efekt końcowy:

1. **Techniczny:**
   - plik `.semgrep.yml` z konfiguracją,
   - katalog `semgrep/` z naszymi regułami,
   - uruchomione skany na backendzie i GUI,
   - przykłady wykrytych problemów (prawdziwe błędy albo sensowne ostrzeżenia),
   - minimum po 1–2 **custom reguły** na każdy obszar (backend-auth, backend-services, frontend).

2. **Dokumentacyjny:**
   - osobne mini-raporty `.md` od każdej osoby,
   - jeden raport zbiorczy + prezentacja z podsumowaniem.

---

## 2. Krótkie przypomnienie: co to Semgrep?

- **Semgrep** to narzędzie do **statycznej analizy kodu (SAST)**:
  - skanuje kod *bez* jego uruchamiania,
  - używa reguł zapisanych w YAML (patterny, które mają być wykrywane),
  - ma gotowe rulesety (np. `p/python`, `p/security-audit`),
  - pozwala tworzyć własne reguły specyficzne dla projektu.

- Dobrze obsługuje **Pythona** i jest często używany do:
  - wykrywania podatności bezpieczeństwa,
  - wyłapywania antywzorców i złych praktyk,
  - pilnowania naszych własnych standardów projektu.

W tym projekcie będziemy korzystać z **Semgrep CLI** uruchamianego z terminala.

---

## 3. Podział ról w zespole

- **Osoba A – Backend (auth / security / walidacja)**
- **Osoba B – Backend (services / scheduler / database)**
- **Osoba C – Frontend (GUI + klienci HTTP)**
- **Osoba D – Koordynator + CI/Pipeline + raport zbiorczy + prezentacja**

Wszyscy korzystamy ze wspólnej konfiguracji Semgrepa i wspólnego standardu raportowania.

---

## 4. Środowisko i wymagania wstępne

### 4.1. Repozytorium

Projekt analizujemy z repozytorium:

- `https://github.com/SzyMm0n/Custom-Steam-Dashboard`

Każdy klonuje repo lokalnie:

```bash
git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git
cd Custom-Steam-Dashboard
```

### 4.2. Python + środowisko wirtualne

Zalecane (nie obowiązkowe, ale wygodne):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# lub
.\.venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 4.3. Instalacja Semgrepa

Każdy instaluje Semgrepa lokalnie (CLI):

```bash
pip install semgrep
# lub na macOS:
brew install semgrep
```

Szybki test:

```bash
semgrep --version
semgrep scan --config=auto --dryrun
```

### 4.4. IDE

Dopuszczalne środowiska:

- **VS Code**
- **PyCharm Professional**
- **Visual Studio**

Semgrep uruchamiamy z terminala w katalogu repo, więc IDE służy tylko do edycji i przeglądania kodu / wyników.
