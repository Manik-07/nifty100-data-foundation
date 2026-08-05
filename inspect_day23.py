import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cursor = conn.cursor()


# --------------------------------------------------
# Financial Ratio Columns
# --------------------------------------------------

print("\nFINANCIAL RATIOS COLUMNS")
print("=" * 60)

columns = cursor.execute(
    "PRAGMA table_info(financial_ratios)"
).fetchall()

for column in columns:
    print(column[1])


# --------------------------------------------------
# Available Ratio Years
# --------------------------------------------------

print("\nFINANCIAL RATIO YEARS")
print("=" * 60)

years = cursor.execute("""
    SELECT DISTINCT year
    FROM financial_ratios
    ORDER BY year
""").fetchall()

for year in years:
    print(year[0])


# --------------------------------------------------
# Sector Names
# --------------------------------------------------

print("\nSECTORS")
print("=" * 60)

sectors = cursor.execute("""
    SELECT broad_sector, COUNT(DISTINCT company_id)
    FROM sectors
    GROUP BY broad_sector
    ORDER BY broad_sector
""").fetchall()

for sector, count in sectors:
    print(f"{sector}: {count}")


# --------------------------------------------------
# Sample Latest Ratios
# --------------------------------------------------

print("\nSAMPLE FINANCIAL RATIOS")
print("=" * 60)

rows = cursor.execute("""
    SELECT *
    FROM financial_ratios
    LIMIT 3
""").fetchall()

for row in rows:
    print(row)


# --------------------------------------------------
# Analysis Columns
# --------------------------------------------------

print("\nANALYSIS COLUMNS")
print("=" * 60)

columns = cursor.execute(
    "PRAGMA table_info(analysis)"
).fetchall()

for column in columns:
    print(column[1])


conn.close()