"""
loader.py

Excel Loader Module
Sprint 1 - Day 2

Loads all Excel files from the data/raw folder.
Automatically handles files with different header rows.
"""

from pathlib import Path
import pandas as pd


class ExcelLoader:
    """Loads Excel datasets from the raw data folder."""

    def __init__(self, data_dir="data/raw"):
        self.data_dir = Path(data_dir)

        # Files having a title row before the actual header
        self.header_row_files = {
            "analysis.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx",
            "companies.xlsx",
            "documents.xlsx",
            "profitandloss.xlsx",
            "prosandcons.xlsx",
        }

    def load(self, filename):
        """
        Load a single Excel file.

        Parameters
        ----------
        filename : str

        Returns
        -------
        pandas.DataFrame
        """

        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

        # Determine which row contains column names
        header = 1 if filename in self.header_row_files else 0

        df = pd.read_excel(file_path, header=header)

        print(
            f"Loaded {filename:<25}"
            f" Rows: {df.shape[0]:<5}"
            f" Columns: {df.shape[1]}"
        )

        return df

    def load_all(self):
        """
        Load every Excel file from data/raw.

        Returns
        -------
        dict
            {dataset_name: dataframe}
        """

        datasets = {}

        total_rows = 0

        excel_files = sorted(self.data_dir.glob("*.xlsx"))

        for file in excel_files:
            df = self.load(file.name)
            datasets[file.stem] = df
            total_rows += len(df)

        print("\n" + "=" * 60)
        print("DATA LOADING SUMMARY")
        print("=" * 60)
        print(f"Files Loaded : {len(datasets)}")
        print(f"Total Rows   : {total_rows}")
        print("=" * 60)

        return datasets


if __name__ == "__main__":

    loader = ExcelLoader()

    datasets = loader.load_all()

    print("\nLoaded datasets:")

    for name, df in datasets.items():
        print(f"{name:<20} {df.shape}")