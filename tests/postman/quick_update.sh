#!/bin/bash
# Quick workflow script - generuje użytkowników i aktualizuje test-env
# Usage: ./quick_update.sh [liczba_użytkowników]
# Example: ./quick_update.sh 1000

set -e  # Exit on error

# Domyślna liczba użytkowników
NUM_USERS=${1:-100}

echo "================================================"
echo "Quick Update Workflow - $NUM_USERS użytkowników"
echo "================================================"
echo ""

# Krok 1: Generuj credentials
echo "1/3 Generowanie credentials..."
python generate_credentials.py "$NUM_USERS" credentials.csv

# Krok 2: Konwertuj do JSON
echo "2/3 Konwersja do JSON..."
python csv_to_clients_json.py credentials.csv clients.json > /dev/null

# Krok 3: Aktualizuj test-env
echo "3/3 Aktualizacja test-env..."
python update_test_env.py clients.json test-env

echo ""
echo "================================================"
echo "✓ Gotowe!"
echo "================================================"
echo "Plik test-env zawiera teraz $NUM_USERS użytkowników."
echo ""
echo "Aby użyć z Docker:"
echo "  docker-compose --env-file tests/postman/test-env up"
echo ""

