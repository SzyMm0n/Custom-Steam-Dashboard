#!/usr/bin/env python3
"""
Konwerter CSV do CLIENTS_JSON dla testów Postman.
Wczytuje plik credentials.csv i tworzy format CLIENTS_JSON.

Usage:
    python csv_to_clients_json.py [ścieżka_do_csv] [ścieżka_do_json]

Example:
    python csv_to_clients_json.py credentials.csv clients.json
"""

import csv
import json
import sys
from pathlib import Path


def csv_to_clients_json(csv_file: str, output_file: str = 'clients.json', format_type: str = "json") -> dict:
    """
    Konwertuje plik CSV do formatu CLIENTS_JSON.

    Args:
        csv_file: Ścieżka do pliku CSV z credentials
        output_file: Ścieżka do pliku wyjściowego (opcjonalne)
        format_type: Typ wyjścia: 'json' (plik JSON) lub 'env' (format dla zmiennej środowiskowej)

    Returns:
        Słownik z client_id jako klucze i client_secret jako wartości
    """
    csv_path = Path(csv_file)

    if not csv_path.exists():
        raise FileNotFoundError(f"Plik {csv_file} nie istnieje")

    clients_dict = {}

    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            client_id = row['client_id']
            client_secret = row['client_secret']
            clients_dict[client_id] = client_secret

    # Jeśli podano plik wyjściowy
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            if format_type == "env":
                # Format dla zmiennej środowiskowej (single line, escaped)
                json_str = json.dumps(clients_dict, separators=(',', ':'))
                f.write(f"CLIENTS_JSON='{json_str}'\n")
            else:
                # Format JSON (pretty-printed)
                json.dump(clients_dict, f, indent=2)

        print(f"✓ Wczytano {len(clients_dict)} użytkowników z {csv_path.name}")
        print(f"✓ Zapisano do pliku: {output_path.absolute()}")

    return clients_dict


def print_clients_json(clients_dict: dict, format_type: str = "json") -> None:
    """
    Wyświetla CLIENTS_JSON w konsoli.

    Args:
        clients_dict: Słownik z credentials
        format_type: Typ wyjścia: 'json' lub 'env'
    """
    if format_type == "env":
        # Format dla zmiennej środowiskowej
        json_str = json.dumps(clients_dict, separators=(',', ':'))
        print("\n" + "="*80)
        print("CLIENTS_JSON (format dla zmiennej środowiskowej):")
        print("="*80)
        print(f"CLIENTS_JSON='{json_str}'")
    else:
        # Format JSON
        print("\n" + "="*80)
        print("CLIENTS_JSON (format JSON):")
        print("="*80)
        print(json.dumps(clients_dict, indent=2))

    print("="*80)
    print(f"Łącznie: {len(clients_dict)} użytkowników\n")


def main():
    """Main entry point."""
    # Domyślne wartości
    default_csv = "credentials.csv"

    # Parsowanie argumentów
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = default_csv

    output_file = None
    format_type = "json"

    if len(sys.argv) > 2:
        output_file = sys.argv[2]

        # Wykryj format na podstawie rozszerzenia
        if output_file.endswith('.txt') or output_file.endswith('.env'):
            format_type = "env"

    # Sprawdź czy plik istnieje
    if not Path(csv_file).exists():
        print(f"❌ Błąd: Plik {csv_file} nie istnieje")
        print(f"\nUżycie: python {Path(__file__).name} [ścieżka_do_csv] [ścieżka_do_json]")
        print(f"Przykład: python {Path(__file__).name} credentials.csv clients.json")
        sys.exit(1)

    try:
        # Konwertuj
        clients_dict = csv_to_clients_json(csv_file, output_file, format_type)

        # Wyświetl w konsoli
        print_clients_json(clients_dict, format_type)

    except Exception as e:
        print(f"❌ Błąd podczas konwersji: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

