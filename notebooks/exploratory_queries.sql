-- 1. Total Companies
SELECT COUNT(*) AS Total_Companies
FROM companies;

-- 2. Top 10 Companies by ROE
SELECT company_name, roe_percentage
FROM companies
ORDER BY roe_percentage DESC
LIMIT 10;

-- 3. Average Sales by Year
SELECT year,
       AVG(sales) AS avg_sales
FROM profitandloss
GROUP BY year;

-- 4. Companies with Highest Market Cap
SELECT company_id,
       MAX(market_cap_crore) AS market_cap
FROM market_cap
GROUP BY company_id
ORDER BY market_cap DESC
LIMIT 10;

-- 5. Cash Flow Summary
SELECT company_id,
       SUM(net_cash_flow) AS total_cash_flow
FROM cashflow
GROUP BY company_id
ORDER BY total_cash_flow DESC;

-- 6. Total Documents
SELECT COUNT(*) AS documents
FROM documents;

-- 7. Sector Wise Company Count
SELECT broad_sector,
       COUNT(*) AS total_companies
FROM sectors
GROUP BY broad_sector;

-- 8. Average ROE
SELECT AVG(roe_percentage)
FROM companies;

-- 9. Highest Closing Price
SELECT company_id,
       MAX(close_price)
FROM stock_prices
GROUP BY company_id;

-- 10. Duplicate Company-Year Records
SELECT company_id,
       year,
       COUNT(*)
FROM profitandloss
GROUP BY company_id, year
HAVING COUNT(*) > 1;