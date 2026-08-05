import sqlite3

conn = sqlite3.connect("db/nifty100.db")

print("\nDUPLICATE SECTOR COMPANY IDs")
print("=" * 50)

rows = conn.execute("""
    SELECT company_id, COUNT(*) AS count
    FROM sectors
    GROUP BY company_id
    HAVING COUNT(*) > 1
""").fetchall()

for row in rows:
    print(row)

print("\nABB COMPANY RECORD")
print("=" * 50)

row = conn.execute("""
    SELECT id, company_name
    FROM companies
    WHERE id = 'ABB'
""").fetchall()

print(row)

conn.close()