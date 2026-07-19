from src.etl.loader import ExcelLoader

loader = ExcelLoader()
datasets = loader.load_all()

companies = set(
    datasets["companies"]["id"]
    .astype(str)
    .str.strip()
)

profit = datasets["profitandloss"]

invalid = profit[
    ~profit["company_id"]
        .astype(str)
        .str.strip()
        .isin(companies)
]

print("Invalid FK Count:", len(invalid))

print("\nUnique Invalid company_id values:")
print(invalid["company_id"].drop_duplicates().tolist())