from src.etl.loader import ExcelLoader

loader = ExcelLoader()
datasets = loader.load_all()

df = datasets["profitandloss"]

duplicates = df[df.duplicated(subset=["company_id", "year"], keep=False)]

# Show complete duplicate rows
print(
    duplicates[
        duplicates["company_id"] == "ADANIPORTS"
    ].to_string(index=False)
)