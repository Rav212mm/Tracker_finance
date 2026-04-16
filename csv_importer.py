import csv
from datetime import date

# Categories that represent internal bank transfers (to avoid double-counting)
INTERNAL_CATEGORIES = {"Spłata karty kredytowej"}

# Description fragments that indicate the credit card repayment receiving side
INTERNAL_DESC_PATTERNS = [
    "SPŁATA - PRZELEW WEWNĘTRZNY",
    "SPŁATA - PRZELEW WEWN",
]


def parse_amount(amount_str: str) -> tuple:
    """Parse '-1 575,38 PLN' → (-1575.38, 'PLN')"""
    amount_str = amount_str.strip()
    # Split off currency suffix
    parts = amount_str.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].isalpha():
        currency = parts[1]
        num_part = parts[0]
    else:
        currency = "PLN"
        num_part = amount_str
    # Remove non-breaking spaces and regular spaces (thousands separator), swap decimal comma
    num_part = num_part.replace("\xa0", "").replace(" ", "").replace(",", ".")
    return float(num_part), currency


def is_internal_transfer(description: str, category: str) -> bool:
    """
    Mark as internal transfer the credit card repayment (both sides):
    - Debit from savings: category 'Spłata karty kredytowej' with negative amount
    - Credit to VISA: category 'Spłata karty kredytowej' with positive amount
    Both are internal and should not count as real income or expense.
    """
    if category.strip() in INTERNAL_CATEGORIES:
        return True
    desc_upper = description.upper()
    for pattern in INTERNAL_DESC_PATTERNS:
        if pattern in desc_upper:
            return True
    return False


def import_csv(filepath: str) -> list:
    """Parse an mBank CSV export and return a list of transaction dicts."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    lines = content.splitlines()

    # Find the data header row
    header_idx = None
    for i, line in enumerate(lines):
        if "#Data operacji" in line:
            header_idx = i
            break

    if header_idx is None:
        raise ValueError(
            "Nieprawidłowy format pliku — nie znaleziono wiersza '#Data operacji'.\n"
            "Upewnij się, że eksportujesz plik z mBanku jako CSV."
        )

    data_block = "\n".join(lines[header_idx + 1 :])
    reader = csv.reader(data_block.splitlines(), delimiter=";", quotechar='"')

    transactions = []
    for row in reader:
        if len(row) < 5:
            continue

        date_str = row[0].strip()
        # Skip empty rows and comment rows
        if not date_str or date_str.startswith("#") or not date_str[0].isdigit():
            continue

        try:
            trans_date = date.fromisoformat(date_str)
        except ValueError:
            continue

        try:
            # Normalize whitespace in description (the CSV has lots of padding spaces)
            description = " ".join(row[1].split())
            account = row[2].strip()
            category = row[3].strip()
            amount_str = row[4].strip()

            if not amount_str:
                continue

            amount, currency = parse_amount(amount_str)
            internal = is_internal_transfer(description, category)

            transactions.append(
                {
                    "date": trans_date.isoformat(),
                    "description": description,
                    "account": account,
                    "category": category,
                    "amount": amount,
                    "currency": currency,
                    "is_internal": 1 if internal else 0,
                }
            )
        except (ValueError, IndexError):
            continue

    return transactions
