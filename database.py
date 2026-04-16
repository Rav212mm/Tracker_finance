import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

APP_DIR = Path.home() / ".expense_tracker"
DB_PATH = APP_DIR / "data.db"


def get_connection() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT,
                account TEXT,
                category TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'PLN',
                file_hash TEXT,
                is_internal INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS imported_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                file_hash TEXT UNIQUE,
                imported_at TEXT,
                transaction_count INTEGER,
                period_start TEXT,
                period_end TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_category ON transactions(category);
            CREATE INDEX IF NOT EXISTS idx_file_hash ON transactions(file_hash);
        """)


def file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def is_file_imported(hash_: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM imported_files WHERE file_hash = ?", (hash_,)
        ).fetchone()
        return row is not None


def insert_transactions(transactions: list, filename: str, hash_: str) -> int:
    if not transactions:
        return 0
    with get_connection() as conn:
        dates = [t["date"] for t in transactions]
        period_start = min(dates)
        period_end = max(dates)

        conn.execute(
            """
            INSERT INTO imported_files
                (filename, file_hash, imported_at, transaction_count, period_start, period_end)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (filename, hash_, datetime.now().isoformat(), len(transactions), period_start, period_end),
        )
        conn.executemany(
            """
            INSERT INTO transactions
                (date, description, account, category, amount, currency, file_hash, is_internal)
            VALUES (:date, :description, :account, :category, :amount, :currency, :file_hash, :is_internal)
            """,
            [dict(t, file_hash=hash_) for t in transactions],
        )
        conn.commit()
    return len(transactions)


def get_months() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) as ym FROM transactions ORDER BY ym DESC"
        ).fetchall()
        return [r["ym"] for r in rows]


def get_summary(year_month: str = None, exclude_internal: bool = True) -> dict:
    clauses = []
    params = []
    if year_month:
        clauses.append("substr(date, 1, 7) = ?")
        params.append(year_month)
    if exclude_internal:
        clauses.append("is_internal = 0")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT
                SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as total_expenses,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                COUNT(*) as transaction_count
            FROM transactions {where}
            """,
            params,
        ).fetchone()
        return {
            "total_expenses": abs(row["total_expenses"] or 0),
            "total_income": row["total_income"] or 0,
            "transaction_count": row["transaction_count"] or 0,
        }


def get_expenses_by_category(year_month: str = None, exclude_internal: bool = True) -> list:
    clauses = ["amount < 0"]
    params = []
    if year_month:
        clauses.append("substr(date, 1, 7) = ?")
        params.append(year_month)
    if exclude_internal:
        clauses.append("is_internal = 0")
    where = f"WHERE {' AND '.join(clauses)}"

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT category, SUM(ABS(amount)) as total
            FROM transactions {where}
            GROUP BY category
            ORDER BY total DESC
            """,
            params,
        ).fetchall()
        return [{"category": r["category"], "total": r["total"]} for r in rows]


def get_monthly_expenses() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT substr(date, 1, 7) as month, SUM(ABS(amount)) as total
            FROM transactions
            WHERE amount < 0 AND is_internal = 0
            GROUP BY month
            ORDER BY month
            """
        ).fetchall()
        return [{"month": r["month"], "total": r["total"]} for r in rows]


def get_category_trend(category: str, months: int = 3) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT substr(date, 1, 7) as month, SUM(ABS(amount)) as total
            FROM transactions
            WHERE category = ? AND amount < 0 AND is_internal = 0
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
            """,
            (category, months),
        ).fetchall()
        return [{"month": r["month"], "total": r["total"]} for r in rows]


def get_transactions(
    year_month: str = None,
    category: str = None,
    search: str = None,
    exclude_internal: bool = False,
) -> list:
    clauses = []
    params = []
    if year_month:
        clauses.append("substr(date, 1, 7) = ?")
        params.append(year_month)
    if category:
        clauses.append("category = ?")
        params.append(category)
    if search:
        clauses.append("(description LIKE ? OR category LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if exclude_internal:
        clauses.append("is_internal = 0")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, date, description, account, category, amount, currency, is_internal
            FROM transactions {where}
            ORDER BY date DESC, id DESC
            """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def get_imported_files() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT filename, file_hash, imported_at, transaction_count, period_start, period_end
            FROM imported_files
            ORDER BY imported_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]


def delete_file_data(hash_: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE file_hash = ?", (hash_,))
        conn.execute("DELETE FROM imported_files WHERE file_hash = ?", (hash_,))
        conn.commit()
