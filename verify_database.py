import sqlite3

# Connect to database
conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()

tables = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "prosandcons",
    "sectors",
    "stock_prices"
]

print("=" * 50)
print("DATABASE ROW COUNTS")
print("=" * 50)

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<20} {count}")

print("\n" + "=" * 50)
print("FOREIGN KEY CHECK")
print("=" * 50)

cursor.execute("PRAGMA foreign_key_check;")
violations = cursor.fetchall()

if len(violations) == 0:
    print("✅ No Foreign Key Violations")
else:
    print("❌ Foreign Key Violations Found")
    for row in violations:
        print(row)

cursor.close()
conn.close()