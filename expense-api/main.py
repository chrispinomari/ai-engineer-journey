import csv
import datetime
import io
import os
import sqlite3
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="Expense & Insights API")

# Which database file to use. Tests can change this to a throwaway file.
DB_PATH = os.environ.get("EXPENSES_DB", "expenses.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # SQLite ignores foreign keys unless you switch this on.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---- The "order form": what a valid new transaction looks like ----
class TransactionIn(BaseModel):
    date: datetime.date                 # must be a real date like 2026-10-15
    amount: float = Field(gt=0)         # must be greater than 0
    merchant_id: int
    category_id: int


@app.get("/")
def home():
    return {"message": "Expense API is running"}


@app.get("/categories")
def list_categories():
    conn = get_connection()
    rows = conn.execute("SELECT id, name FROM categories").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/merchants")
def list_merchants():
    conn = get_connection()
    rows = conn.execute("SELECT id, name FROM merchants").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/transactions")
def list_transactions(
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    category: Optional[str] = None,
):
    # "WHERE 1=1" is always true. It lets us add optional "AND ..."
    # filters below without worrying about which one comes first.
    sql = """
        SELECT t.id, t.date, t.amount,
               m.name AS merchant, c.name AS category
        FROM transactions t
        JOIN merchants  m ON t.merchant_id = m.id
        JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    """
    params = []

    if start_date:
        sql += " AND t.date >= ?"
        params.append(start_date.isoformat())
    if end_date:
        sql += " AND t.date <= ?"
        params.append(end_date.isoformat())
    if category:
        sql += " AND c.name = ?"
        params.append(category)

    sql += " ORDER BY t.date DESC"

    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/transactions", status_code=201)
def add_transaction(tx: TransactionIn):
    conn = get_connection()

    # Check the merchant and category really exist before saving.
    if not conn.execute("SELECT 1 FROM merchants WHERE id = ?",
                        (tx.merchant_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not conn.execute("SELECT 1 FROM categories WHERE id = ?",
                        (tx.category_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Category not found")

    cursor = conn.execute(
        "INSERT INTO transactions (date, amount, merchant_id, category_id) "
        "VALUES (?, ?, ?, ?)",
        (tx.date.isoformat(), tx.amount, tx.merchant_id, tx.category_id),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"id": new_id, **tx.model_dump(mode="json")}


@app.get("/spending/by-category")
def spending_by_category():
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.name AS category, SUM(t.amount) AS total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        GROUP BY c.name
        ORDER BY total DESC, c.name ASC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/spending/by-merchant")
def spending_by_merchant():
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.name AS merchant, SUM(t.amount) AS total
        FROM transactions t
        JOIN merchants m ON t.merchant_id = m.id
        GROUP BY m.name
        ORDER BY total DESC, m.name ASC
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/spending/monthly")
def spending_monthly():
    # substr(date, 1, 7) takes the first 7 characters: "2026-10"
    conn = get_connection()
    rows = conn.execute("""
        SELECT substr(date, 1, 7) AS month, SUM(amount) AS total
        FROM transactions
        GROUP BY month
        ORDER BY month
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_or_create(conn, table, name):
    # Find the row with this name. If it doesn't exist, create it.
    # `table` is always written by us in this file, never typed by a user.
    row = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute(f"INSERT INTO {table} (name) VALUES (?)", (name,))
    return cursor.lastrowid


@app.post("/transactions/upload")
async def upload_csv(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    conn = get_connection()
    imported = 0
    errors = []

    for line_no, row in enumerate(reader, start=2):  # line 1 is the header
        try:
            date = datetime.date.fromisoformat(row["date"].strip())
            amount = float(row["amount"])
            if amount <= 0:
                raise ValueError("amount must be greater than 0")
            merchant = row["merchant"].strip()
            category = row["category"].strip()
            if not merchant or not category:
                raise ValueError("merchant and category cannot be empty")

            merchant_id = get_or_create(conn, "merchants", merchant)
            category_id = get_or_create(conn, "categories", category)
            conn.execute(
                "INSERT INTO transactions (date, amount, merchant_id, category_id) "
                "VALUES (?, ?, ?, ?)",
                (date.isoformat(), amount, merchant_id, category_id),
            )
            imported += 1
        except (ValueError, KeyError, AttributeError) as e:
            errors.append({"line": line_no, "error": str(e)})

    conn.commit()
    conn.close()
    return {"imported": imported, "errors": errors}