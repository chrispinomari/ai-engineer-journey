import sqlite3

# Connect to a database file. If it doesn't exist, Python creates it.
conn = sqlite3.connect("expenses.db")

# Build the three tables (the "shelves"). We drop old ones first
# so you can safely re-run this script from scratch.
conn.executescript("""
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE merchants (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE transactions (
    id          INTEGER PRIMARY KEY,
    date        TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    merchant_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
""")

# Stock the shelves with sample data.
conn.executemany("INSERT INTO categories (name) VALUES (?)",
    [("Food",), ("Transport",), ("Bills",), ("Entertainment",)])

conn.executemany("INSERT INTO merchants (name) VALUES (?)",
    [("Java House",), ("Naivas",), ("Uber",), ("Safaricom",), ("Netflix",)])

# (date, amount, merchant_id, category_id)
conn.executemany(
    "INSERT INTO transactions (date, amount, merchant_id, category_id) VALUES (?, ?, ?, ?)",
    [
        ("2026-10-01", 450,  1, 1),
        ("2026-10-02", 650,  3, 2),
        ("2026-10-03", 1000, 4, 3),
        ("2026-10-04", 1200, 2, 1),
        ("2026-10-06", 800,  1, 1),
        ("2026-10-08", 1100, 5, 4),
        ("2026-10-10", 400,  3, 2),
        ("2026-10-12", 250,  4, 3),
    ],
)

conn.commit()  # "Save" the changes permanently
conn.close()
print("Database created!")