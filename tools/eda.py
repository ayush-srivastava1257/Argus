import duckdb
import pandas as pd
from typing import Dict, Any

class EDAAnalyzer:
    def __init__(self, data_loader):
        self.dl = data_loader

    def generate_summary(self, account_id: str) -> str:
        """
        Generates a human-readable profile summary of an account for the LLM.
        """
        try:
            # Get Customer Profile if available
            cust_df = self.dl.load_customers()
            profile_text = ""
            if not cust_df.empty:
                cust_info = duckdb.query(f"SELECT * FROM cust_df WHERE customer_id = '{account_id}'").df()
                if not cust_info.empty:
                    row = cust_info.iloc[0]
                    profile_text = f"Customer Profile: {row.get('age', 'Unknown')} yr old {row.get('customer_type', 'Unknown')} in {row.get('city', 'Unknown')}.\n"
            
            # Get Transaction stats
            tx_df = self.dl.load_transactions()
            stats = duckdb.query(f"""
                SELECT 
                    COUNT(*) as total_tx,
                    SUM(CASE WHEN receiver_account_id = '{account_id}' THEN amount ELSE 0 END) as total_in,
                    SUM(CASE WHEN sender_account_id = '{account_id}' THEN amount ELSE 0 END) as total_out
                FROM tx_df
                WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
            """).df()
            
            if stats.empty or stats['total_tx'].iloc[0] == 0:
                return f"No transaction history found for {account_id}."
                
            total_in = stats['total_in'].iloc[0] or 0
            total_out = stats['total_out'].iloc[0] or 0
            total_tx = stats['total_tx'].iloc[0]
            
            summary = f"Account {account_id} Analysis:\n"
            summary += profile_text
            summary += f"Total Transactions: {total_tx}\n"
            summary += f"Total Money In: ${total_in:,.2f}\n"
            summary += f"Total Money Out: ${total_out:,.2f}\n"
            summary += f"Net Flow: ${(total_in - total_out):,.2f}\n"
            
            return summary
        except Exception as e:
            return f"Error generating EDA: {str(e)}"
