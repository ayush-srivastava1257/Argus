import duckdb
import pandas as pd
import sys
import os
from pathlib import Path

# Add the project root to sys.path to allow imports when running as a module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DATASETS

class DataLoader:
    def __init__(self):
        # Initialize an in-memory DuckDB connection
        self.con = duckdb.connect(':memory:')
        
    def check_data_files(self):
        """Check which datasets are available on disk."""
        available = {}
        for name, path in DATASETS.items():
            available[name] = path.exists()
        return available

    def load_transactions(self) -> pd.DataFrame:
        """
        Loads the core transaction data from the IBM dataset into a canonical schema,
        or uses the uploaded dataset if one exists in the DuckDB connection.
        Returns a Pandas DataFrame.
        """
        # First, check if custom data was uploaded
        try:
            tables = self.con.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'uploaded'").fetchall()
            if tables:
                df = self.con.execute("SELECT * FROM uploaded").df()
                
                # Attempt SAML-D to Canonical mapping if it looks like SAML-D
                if 'Sender_account' in df.columns and 'Receiver_account' in df.columns:
                    df = df.rename(columns={
                        'Sender_account': 'sender_account_id',
                        'Receiver_account': 'receiver_account_id',
                        'Amount': 'amount',
                        'Payment_currency': 'currency',
                        'Payment_type': 'transaction_type',
                        'Is_laundering': 'is_laundering',
                    })
                    if 'Date' in df.columns and 'Time' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str), errors='coerce')
                elif 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    
                return df
        except Exception as e:
            print(f"Warning: Failed to check or load uploaded table ({e})")

        if not DATASETS["ibm_aml_transactions"].exists():
            raise FileNotFoundError(f"Missing transaction dataset at {DATASETS['ibm_aml_transactions']}")
            
        csv_path = str(DATASETS["ibm_aml_transactions"])
        
        # Load and map to Canonical Schema using DuckDB
        query = f"""
            SELECT 
                ROW_NUMBER() OVER () AS transaction_id,
                Timestamp AS timestamp,
                "From Bank" AS sender_bank_id,
                "Account" AS sender_account_id,
                "To Bank" AS receiver_bank_id,
                "Account.1" AS receiver_account_id,
                "Amount Received" AS amount,
                "Receiving Currency" AS currency,
                "Payment Format" AS transaction_type,
                "Is Laundering" AS is_laundering
            FROM read_csv_auto('{csv_path}')
        """
        try:
            df = self.con.execute(query).df()
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            return df
        except Exception as e:
            # Fallback if headers are slightly different than expected in HI-Small
            print(f"Warning: primary query failed ({e}). Trying fallback schema mapping...")
            query_fallback = f"""
                SELECT 
                    *
                FROM read_csv_auto('{csv_path}')
            """
            return self.con.execute(query_fallback).df()

    def load_customers(self) -> pd.DataFrame:
        """
        Loads customer profile data (KYC) into a canonical schema.
        """
        if not DATASETS["kyc_customers"].exists():
            return pd.DataFrame() # Return empty if missing
            
        csv_path = str(DATASETS["kyc_customers"])
        query = f"""
            SELECT 
                Customer_ID AS customer_id,
                Age AS age,
                Customer_Type AS customer_type,
                City AS city,
                Region AS region,
                Bank_Name AS bank_name
            FROM read_csv_auto('{csv_path}')
        """
        return self.con.execute(query).df()

if __name__ == "__main__":
    loader = DataLoader()
    print("Checking datasets:")
    for name, is_avail in loader.check_data_files().items():
        print(f"  {name}: {'Found' if is_avail else 'Missing'}")
