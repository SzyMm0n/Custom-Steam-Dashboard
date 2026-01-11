#!/usr/bin/env python3
"""
Aktualizuje wartość CLIENTS_JSON w pliku test-env na podstawie clients.json.

Usage:
    python update_test_env.py [ścieżka_do_clients_json] [ścieżka_do_test_env]

Example:
    python update_test_env.py clients.json test-env
"""

import json
import sys
from pathlib import Path


def update_test_env(clients_json_path: str, test_env_path: str) -> None:
    """
    Aktualizuje CLIENTS_JSON w pliku test-env.

    Args:
        clients_json_path: Ścieżka do pliku clients.json
        test_env_path: Ścieżka do pliku test-env
    """
    # Wczytaj clients.json
    clients_json_file = Path(clients_json_path)
    if not clients_json_file.exists():
        raise FileNotFoundError(f"Plik {clients_json_path} nie istnieje")

    with open(clients_json_file, 'r') as f:
        clients_dict = json.load(f)

    # Konwertuj do kompaktnego JSON (bez spacji)
    clients_json_str = json.dumps(clients_dict, separators=(',', ':'))

    # Wczytaj test-env
    test_env_file = Path(test_env_path)
    if not test_env_file.exists():
        raise FileNotFoundError(f"Plik {test_env_path} nie istnieje")

    with open(test_env_file, 'r') as f:
        lines = f.readlines()

    # Znajdź i zaktualizuj linię z CLIENTS_JSON
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('CLIENTS_JSON='):
            lines[i] = f'CLIENTS_JSON={clients_json_str}\n'
            updated = True
            break

    if not updated:
        raise ValueError("Nie znaleziono linii CLIENTS_JSON= w pliku test-env")

    # Zapisz zaktualizowany plik
    with open(test_env_file, 'w') as f:
        f.writelines(lines)

    print(f"✓ Wczytano {len(clients_dict)} użytkowników z {clients_json_file.name}")
    print(f"✓ Zaktualizowano CLIENTS_JSON w {test_env_file.name}")
    print(f"✓ Długość wartości CLIENTS_JSON: {len(clients_json_str)} znaków")


def main():
    """Main entry point."""
    # Domyślne wartości
    default_clients_json = "clients.json"
    default_test_env = "test-env"

    # Parsowanie argumentów
    if len(sys.argv) > 1:
        clients_json_path = sys.argv[1]
    else:
        clients_json_path = default_clients_json

    if len(sys.argv) > 2:
        test_env_path = sys.argv[2]
    else:
        test_env_path = default_test_env

    try:
        update_test_env(clients_json_path, test_env_path)
    except Exception as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

