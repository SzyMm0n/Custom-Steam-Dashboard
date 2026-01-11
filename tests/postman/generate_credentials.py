#!/usr/bin/env python3
"""
Generator credential dla testów Postman.
Generuje N użytkowników z losowymi client_id i client_secret.

Usage:
    python generate_credentials.py [liczba_użytkowników] [ścieżka_do_pliku]

Example:
    python generate_credentials.py 1000 credentials.csv
"""

import csv
import random
import string
import sys
from pathlib import Path


def generate_secret(length: int = 48) -> str:
    """
    Generuje losowy secret składający się z liter i cyfr.

    Args:
        length: Długość generowanego sekretnu (domyślnie 48)

    Returns:
        Losowy string o określonej długości
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_credentials(num_users: int, output_file: str) -> None:
    """
    Generuje plik CSV z credentials dla użytkowników.

    Args:
        num_users: Liczba użytkowników do wygenerowania
        output_file: Ścieżka do pliku wyjściowego CSV
    """
    output_path = Path(output_file)

    # Twórz katalog jeśli nie istnieje
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Nagłówek
        writer.writerow(['client_id', 'client_secret'])

        # Generuj użytkowników
        for i in range(1, num_users + 1):
            client_id = f"user-{i:03d}"  # Format: user-001, user-002, ...
            client_secret = generate_secret()
            writer.writerow([client_id, client_secret])

    print(f"✓ Wygenerowano {num_users} użytkowników")
    print(f"✓ Zapisano do pliku: {output_path.absolute()}")


def main():
    """Main entry point."""
    # Domyślne wartości
    default_num_users = 8000
    default_output = "credentials.csv"

    # Parsowanie argumentów
    if len(sys.argv) > 1:
        try:
            num_users = int(sys.argv[1])
        except ValueError:
            print(f"❌ Błąd: '{sys.argv[1]}' nie jest liczbą")
            sys.exit(1)
    else:
        num_users = default_num_users

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = default_output

    print(f"Generowanie {num_users} użytkowników...")
    generate_credentials(num_users, output_file)


if __name__ == "__main__":
    main()

