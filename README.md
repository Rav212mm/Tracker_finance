# mBank Expense Tracker

Desktopowa aplikacja do analizy wydatków na podstawie wyciągów CSV z mBanku.

## Funkcje

- **Import CSV** — wczytuje wyciągi z mBanku, automatycznie odfiltrowuje wewnętrzne przelewy (spłata karty)
- **Dashboard** — miesięczne podsumowanie przychodów i wydatków, wskazówki oszczędnościowe z trendem miesiąc do miesiąca
- **Transakcje** — przeglądanie i filtrowanie wszystkich operacji
- **Kategorie** — automatyczna klasyfikacja wydatków (niezbędne / pół-uznaniowe / uznaniowe)

## Wymagania

- Python 3.10+
- PyQt6 ≥ 6.4
- matplotlib ≥ 3.7

## Instalacja i uruchomienie

```bash
pip install -r requirements.txt
python main.py
```

Na Windows można też użyć `install.bat`.

## Struktura

```
main.py              # punkt wejścia
database.py          # SQLite – przechowywanie transakcji
csv_importer.py      # parser wyciągów mBank CSV
analytics.py         # klasyfikacja i analiza wydatków
ui/                  # widżety PyQt6 (dashboard, import, transakcje)
```

## Uwagi

Aplikacja obsługuje format CSV eksportowany z mBanku (polskie ustawienia regionalne, separator `;`, kwoty w formacie `1 234,56 PLN`).
