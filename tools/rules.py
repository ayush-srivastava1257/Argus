import duckdb
import pandas as pd
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import AML_THRESHOLDS

class RuleEngine:
    def __init__(self, data_loader):
        self.dl = data_loader

    def evaluate_account(self, account_id: str) -> Dict[str, Any]:
        """
        Runs deterministic AML rules against an account.
        """
        df = self.dl.load_transactions()
        results = {
            "flagged_rules": [],
            "risk_score_contribution": 0,
            "details": {}
        }
        
        try:
            # Rule 1: Structuring (Smurfing)
            # Multiple deposits just below the reporting threshold (e.g., $10k)
            struct_config = AML_THRESHOLDS["structuring"]
            near_thresh = struct_config["near_threshold_amount"]
            abs_thresh = struct_config["absolute_threshold"]
            min_count = struct_config["min_transaction_count"]
            
            structuring_query = f"""
                SELECT COUNT(*) as struct_count
                FROM df
                WHERE receiver_account_id = '{account_id}'
                AND amount >= {near_thresh} 
                AND amount < {abs_thresh}
            """
            struct_res = duckdb.query(structuring_query).df()
            if not struct_res.empty and struct_res['struct_count'].iloc[0] >= min_count:
                count = int(struct_res['struct_count'].iloc[0])
                results["flagged_rules"].append("STRUCTURING_DETECTED")
                results["risk_score_contribution"] += 35
                results["details"]["structuring"] = f"{count} transactions detected just below the ${abs_thresh} threshold."

            # Rule 2: Rapid Cash-Out (Pass-through)
            # High volume in, mostly flows out within a short time
            cashout_query = f"""
                SELECT 
                    SUM(CASE WHEN receiver_account_id = '{account_id}' THEN amount ELSE 0 END) as total_in,
                    SUM(CASE WHEN sender_account_id = '{account_id}' THEN amount ELSE 0 END) as total_out
                FROM df
            """
            cashout_res = duckdb.query(cashout_query).df()
            if not cashout_res.empty:
                total_in = float(cashout_res['total_in'].iloc[0] or 0)
                total_out = float(cashout_res['total_out'].iloc[0] or 0)
                
                if total_in > 0:
                    pass_through_ratio = total_out / total_in
                    if pass_through_ratio >= AML_THRESHOLDS["rapid_cash_out"]["pass_through_ratio"]:
                        results["flagged_rules"].append("RAPID_CASH_OUT")
                        results["risk_score_contribution"] += 40
                        results["details"]["rapid_cash_out"] = f"{pass_through_ratio*100:.1f}% of incoming funds (${total_in:.2f}) were quickly transferred out."

            # Rule 3: Fan-In
            # Many unique senders to one receiver
            fan_in_query = f"""
                SELECT COUNT(DISTINCT sender_account_id) as unique_senders
                FROM df
                WHERE receiver_account_id = '{account_id}'
            """
            fan_in_res = duckdb.query(fan_in_query).df()
            if not fan_in_res.empty:
                senders = int(fan_in_res['unique_senders'].iloc[0])
                if senders >= AML_THRESHOLDS["fan_in"]["min_unique_senders"]:
                    results["flagged_rules"].append("FAN_IN_PATTERN")
                    results["risk_score_contribution"] += 25
                    results["details"]["fan_in"] = f"Account received funds from {senders} distinct senders."
            
            return results
        except Exception as e:
            return {"error": str(e)}
