import os
import pandas as pd
import sqlite3
from create_tables import create_tables

def load_all(
    data_dir="C:/Users/HP/Desktop/Edureka/LocalFoodWastage/data",
    db_path="C:/Users/HP/Desktop/Edureka/LocalFoodWastage/db/food_wastage.db"
):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    create_tables(db_path)
    conn = sqlite3.connect(db_path)

    pd.read_csv(f"{data_dir}/providers_data.csv").to_sql("providers", conn, if_exists="replace", index=False)
    pd.read_csv(f"{data_dir}/receivers_data.csv").to_sql("receivers", conn, if_exists="replace", index=False)
    pd.read_csv(f"{data_dir}/food_listings_data.csv").to_sql("food_listings", conn, if_exists="replace", index=False)
    pd.read_csv(f"{data_dir}/claims_data.csv").to_sql("claims", conn, if_exists="replace", index=False)

    conn.close()
    print("Loaded all CSVs.")

if __name__ == "__main__":
    load_all()
