import sqlite3

conn = sqlite3.connect("expenses.db")

def run(title, sql):
    print(f"\n--- {title} ---")
    for row in conn.execute(sql):
        print(row)


# 1. SELECT: Show all transactions
run("All transactions", """
    SELECT *
    FROM transactions
""")


# 2. WHERE: Show payments over 700
run("Big payments (over 700)", """
    SELECT date, amount
    FROM transactions
    WHERE amount > 700
""")


# 3. JOIN: Show payments with readable merchant and category names
run("Payments with readable names", """
    SELECT t.date, m.name, c.name, t.amount
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.id
    JOIN categories c ON t.category_id = c.id
""")


# 4. GROUP BY: Calculate total spending per category
run("Total spent per category", """
    SELECT c.name, SUM(t.amount) AS total
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    GROUP BY c.name
    ORDER BY total DESC
""")


# 5. JOIN + WHERE: Show all transactions at Uber
run("All transactions at Uber", """
    SELECT t.date, m.name, t.amount
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.id
    WHERE m.name = 'Uber'
""")


# 6. COUNT + GROUP BY: Count transactions per merchant
#    NEW: second sort rule so ties are listed alphabetically
run("Number of transactions per merchant", """
    SELECT m.name, COUNT(*) AS transaction_count
    FROM transactions t
    JOIN merchants m ON t.merchant_id = m.id
    GROUP BY m.name
    ORDER BY transaction_count DESC, m.name ASC
""")


# Close the database connection
conn.close()