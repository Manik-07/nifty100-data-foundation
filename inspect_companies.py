from src.etl.loader import ExcelLoader

loader = ExcelLoader()
datasets = loader.load_all()

companies = datasets["companies"]

print(companies["id"].tolist())