from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
    get_peers,
    get_valuation,
)

import sqlite3


# --------------------------------------------------
# 1. Test Companies
# --------------------------------------------------

print("\n1. COMPANIES")
print("-" * 50)

companies = get_companies()

print("Total companies:", len(companies))
print(companies.head())


# --------------------------------------------------
# 2. Test Sectors
# --------------------------------------------------

print("\n2. SECTORS")
print("-" * 50)

sectors = get_sectors()

print("Total sector rows:", len(sectors))
print(sectors.head())


# --------------------------------------------------
# 3. Test Company Financial Data
# --------------------------------------------------

print("\n3. SAMPLE COMPANY")
print("-" * 50)

if not companies.empty:

    ticker = companies.iloc[0]["company_id"]

    print("Testing company:", ticker)

    print("\nFinancial Ratios:")
    print(get_ratios(ticker).head())

    print("\nProfit & Loss:")
    print(get_pl(ticker).head())

    print("\nBalance Sheet:")
    print(get_bs(ticker).head())

    print("\nCash Flow:")
    print(get_cf(ticker).head())

    print("\nValuation:")
    print(get_valuation(ticker).head())


# --------------------------------------------------
# 4. Test Peer Groups
# --------------------------------------------------

print("\n4. PEER GROUP")
print("-" * 50)

conn = sqlite3.connect("db/nifty100.db")

peer = conn.execute(
    "SELECT peer_group_name FROM peer_groups LIMIT 1"
).fetchone()

conn.close()

if peer:

    group_name = peer[0]

    print("Testing peer group:", group_name)

    peers = get_peers(group_name)

    print(peers.head())

else:

    print("No peer groups found.")


print("\n" + "=" * 50)
print("DATABASE TEST COMPLETED")
print("=" * 50)