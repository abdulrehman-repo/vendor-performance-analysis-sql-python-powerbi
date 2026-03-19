import pandas as pd
import os
from sqlalchemy import create_engine
import time

# Creating a Database in SQLite
engine = create_engine('sqlite:///inventory.db')

def ingest_db(df, table_name, engine):
    """Ingest small/medium dataframe into database"""
    df.to_sql(table_name, con=engine, if_exists='replace', index=False)

def ingest_sales_in_chunks(engine, chunk_size=50_000):
    """Ingest large sales file using chunks"""
    start = time.time()
    first_chunk = True

    for chunk in pd.read_csv('data/sales.csv', chunksize=chunk_size):
        chunk.to_sql(
            'sales',
            con=engine,
            if_exists='replace' if first_chunk else 'append',
            index=False
        )
        first_chunk = False

    end = time.time()
    print("Sales ingestion completed")
    print(f"Total time taken: {(end - start)/60:.2f} minutes")

def load_raw_data():
    """Read CSV files and insert into SQLite"""
    for file in os.listdir('data'):
        if file.endswith('.csv'):
            table_name = file[:-4]

            # Use chunking only for sales file
            if table_name == 'sales':
                ingest_sales_in_chunks(engine)
            else:
                df = pd.read_csv(f'data/{file}')
                print(f"{table_name}: {df.shape}")
                ingest_db(df, table_name, engine)

if __name__ == '__main__':
    load_raw_data()
