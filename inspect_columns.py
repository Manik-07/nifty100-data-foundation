from src.etl.loader import ExcelLoader

loader = ExcelLoader()

datasets = loader.load_all()

for name, df in datasets.items():

    print("\n" + "=" * 60)
    print(f"DATASET: {name.upper()}")
    print("=" * 60)

    print(df.columns.tolist())