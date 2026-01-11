# Narzędzia Postman dla testowania API

Zestaw skryptów Python do generowania credentials i konwersji do formatu CLIENTS_JSON dla testowania API w Postman.

## Skrypty

### 1. `generate_credentials.py`

Generuje plik CSV z N użytkownikami (client_id i client_secret).

**Użycie:**
```bash
python generate_credentials.py [liczba_użytkowników] [ścieżka_do_pliku]
```

**Przykłady:**
```bash
# Generuj 100 użytkowników (domyślnie) do credentials.csv
python generate_credentials.py

# Generuj 1000 użytkowników
python generate_credentials.py 1000

# Generuj 500 użytkowników do konkretnego pliku
python generate_credentials.py 500 my_credentials.csv

# Generuj 800 użytkowników (jak w cred.csv)
python generate_credentials.py 800 credentials.csv
```

**Format wyjściowy (CSV):**
```csv
client_id,client_secret
user-001,K7mN9pQr2sT4vW6xY8zA1bC3dE5fG7hJ9kL2mN4pQ6r
user-002,R8sT4vW6xY2zA9bC1dE3fG5hJ7kL9mN4pQ6rS8tU0v
...
```

### 2. `csv_to_clients_json.py`

Wczytuje plik CSV i konwertuje do formatu CLIENTS_JSON.

**Użycie:**
```bash
python csv_to_clients_json.py [ścieżka_do_csv] [ścieżka_do_json]
```

**Przykłady:**
```bash
# Konwertuj credentials.csv i wyświetl w konsoli
python csv_to_clients_json.py

# Konwertuj i zapisz do pliku JSON
python csv_to_clients_json.py credentials.csv clients.json

# Konwertuj i zapisz w formacie zmiennej środowiskowej
python csv_to_clients_json.py credentials.csv clients.env

# Użyj konkretnego pliku CSV
python csv_to_clients_json.py ../temp/cred.csv output.json
```

### 3. `update_test_env.py`

Wczytuje plik `clients.json` i aktualizuje wartość `CLIENTS_JSON` w pliku `test-env`.

**Użycie:**
```bash
python update_test_env.py [ścieżka_do_clients_json] [ścieżka_do_test_env]
```

**Przykłady:**
```bash
# Użyj domyślnych plików (clients.json i test-env)
python update_test_env.py

# Użyj konkretnych plików
python update_test_env.py clients.json test-env

# Zaktualizuj z innego pliku JSON
python update_test_env.py my_clients.json ../server/.env
```

**Format wyjściowy (JSON):**
```json
{
  "user-001": "K7mN9pQr2sT4vW6xY8zA1bC3dE5fG7hJ9kL2mN4pQ6r",
  "user-002": "R8sT4vW6xY2zA9bC1dE3fG5hJ7kL9mN4pQ6rS8tU0v",
  ...
}
```

**Format wyjściowy (ENV):**
```bash
CLIENTS_JSON='{"user-001":"K7mN9pQr2sT4vW6xY8zA1bC3dE5fG7hJ9kL2mN4pQ6r","user-002":"R8sT4vW6xY2zA9bC1dE3fG5hJ7kL9mN4pQ6rS8tU0v"}'
```

## Workflow dla testowania Postman

### Szybki sposób (jeden skrypt)

Użyj skryptu `quick_update.sh` do automatyzacji wszystkich kroków:

```bash
cd tests/postman

# Wygeneruj 100 użytkowników (domyślnie)
./quick_update.sh

# Lub określ liczbę użytkowników
./quick_update.sh 1000
```

### Krok po kroku

### Krok 1: Generuj credentials

```bash
cd tests/postman
python generate_credentials.py 1000 credentials.csv
```

### Krok 2: Konwertuj do CLIENTS_JSON

```bash
python csv_to_clients_json.py credentials.csv clients.json
```

### Krok 3: Zaktualizuj test-env

```bash
python update_test_env.py clients.json test-env
```

### Krok 4: Użyj w Postman/Docker

Teraz możesz użyć zaktualizowanego pliku `test-env`:

**Opcja A - Docker:**
```bash
# Plik test-env jest gotowy do użycia w docker-compose
docker-compose --env-file tests/postman/test-env up
```

**Opcja B - Postman:**
1. Otwórz plik `test-env`
2. Skopiuj wartość `CLIENTS_JSON`
3. W Postman, utwórz zmienną środowiskową i wklej wartość

## Szybki workflow (wszystko w jednym)

**Opcja A - Skrypt Bash (zalecane):**
```bash
cd tests/postman
./quick_update.sh 500
```

**Opcja B - Ręcznie:**
```bash
cd tests/postman

# Wygeneruj 500 użytkowników i zaktualizuj test-env
python generate_credentials.py 500 credentials.csv
python csv_to_clients_json.py credentials.csv clients.json
python update_test_env.py clients.json test-env

echo "✓ Gotowe! Plik test-env został zaktualizowany."
```

## Przykład end-to-end

```bash
# 1. Generuj 500 użytkowników
python generate_credentials.py 500 test_users.csv

# 2. Konwertuj do JSON
python csv_to_clients_json.py test_users.csv test_users.json

# 3. Zaktualizuj test-env
python update_test_env.py test_users.json test-env

# 4. Sprawdź czy aktualizacja się powiodła
grep "CLIENTS_JSON=" test-env | head -c 100
```

## Konwersja istniejącego pliku cred.csv

Jeśli masz już plik `temp/cred.csv` z 800 użytkownikami:

```bash
# Konwertuj do JSON
python csv_to_clients_json.py ../../temp/cred.csv cred_clients.json

# Zaktualizuj test-env
python update_test_env.py cred_clients.json test-env
```

## Aktualizacja test-env z istniejącego clients.json

Jeśli masz już wygenerowany `clients.json`:

```bash
# Po prostu zaktualizuj test-env
python update_test_env.py clients.json test-env
```

## Wymagania

- Python 3.7+
- Brak dodatkowych zależności (używa tylko standardowej biblioteki)

## Struktura plików

```
tests/postman/
├── README.md                    # Ten plik
├── generate_credentials.py      # Generator credentials
├── csv_to_clients_json.py       # Konwerter CSV → JSON
├── update_test_env.py           # Aktualizator test-env
├── quick_update.sh              # Skrypt automatyzujący cały workflow
├── credentials.csv              # Wygenerowany plik CSV (gitignore)
├── clients.json                 # Wygenerowany plik JSON (gitignore)
└── test-env                     # Plik środowiskowy z CLIENTS_JSON
```

