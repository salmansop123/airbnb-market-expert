# import pandas as pd
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from database.db_connection import get_connection

# def load_data():
#     conn = get_connection()
    
#     # Read entire properties table into a Pandas DataFrame
#     df = pd.read_sql("SELECT * FROM properties", conn)
#     conn.close()
    
#     print(f"Loaded {len(df)} rows from database")
#     print(df.head())  # show first 5 rows
#     return df

# if __name__ == "__main__":
#     df = load_data()


import pandas as pd
import sys
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_engine():
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME")
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

def load_data():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM properties", engine)
    print(f"Loaded {len(df)} rows\n")
    print(df.head())
    return df

def clean_data(df):
    print("\n--- Cleaning Data ---")

    # Step 1: Remove rows with no price
    before = len(df)
    df = df.dropna(subset=["price"])
    print(f"Removed {before - len(df)} rows with missing price")

    # Step 2: Remove duplicate rows
    before = len(df)
    df = df.drop_duplicates(subset=["title", "region", "price"])
    print(f"Removed {before - len(df)} duplicate rows")

    # Step 3: Remove unrealistic prices (less than $10 or more than $10,000)
    before = len(df)
    df = df[(df["price"] >= 10) & (df["price"] <= 10000)]
    print(f"Removed {before - len(df)} rows with unrealistic prices")

    # Step 4: Clean title column
    df["title"] = df["title"].str.strip()  # remove extra spaces

    print(f"\nFinal clean dataset: {len(df)} rows")
    print(df.head())

    return df

def save_clean_data(df):
    output_path = "data/processed/clean_listings.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved clean data to {output_path}")

if __name__ == "__main__":
    df = load_data()
    df_clean = clean_data(df)
    save_clean_data(df_clean)
