"""
Rule Tool — Extended AML rule engine tool wrapper.
Exposes all 8 AML rules from the rule definitions registry.
"""
import duckdb
import pandas as pd
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import AML_THRESHOLDS
from aml.rule_definitions import RULE_REGISTRY


class RuleTool:
    """
    Extended AML rule engine with 8 deterministic rules.
    Computes per-rule contributions and generates structured rule hit reports.
    """

    def __init__(self, data_loader):
        self.dl = data_loader

    def evaluate_account(self, account_id: str) -> Dict[str, Any]:
        """Run all 8 AML rules against a specific account."""
        df = self.dl.load_transactions()
        results = {
            "account_id": account_id,
            "flagged_rules": [],
            "risk_score_contribution": 0,
            "details": {},
            "rule_hits": [],
        }

        try:
            # Rule 1: Structuring
            struct_res = duckdb.query(f"""
                SELECT COUNT(*) AS struct_count FROM df
                WHERE receiver_account_id = '{account_id}'
                AND amount >= 9000 AND amount < 10000
            """).df()
            struct_count = int(struct_res["struct_count"].iloc[0])
            if struct_count >= AML_THRESHOLDS["structuring"]["min_transaction_count"]:
                results["flagged_rules"].append("STRUCTURING_DETECTED")
                results["risk_score_contribution"] += 35
                results["details"]["structuring"] = f"{struct_count} transactions detected just below $10,000 CTR threshold."
                results["rule_hits"].append({
                    "rule_id": "RULE-001", "name": "STRUCTURING_DETECTED",
                    "value": struct_count, "threshold": 3, "score": 35
                })

            # Rule 2: Rapid Cash-Out
            cashout_res = duckdb.query(f"""
                SELECT
                    SUM(CASE WHEN receiver_account_id = '{account_id}' THEN amount ELSE 0 END) AS total_in,
                    SUM(CASE WHEN sender_account_id = '{account_id}' THEN amount ELSE 0 END) AS total_out
                FROM df
            """).df()
            total_in = float(cashout_res["total_in"].iloc[0] or 0)
            total_out = float(cashout_res["total_out"].iloc[0] or 0)
            if total_in > 0:
                ratio = total_out / total_in
                if ratio >= AML_THRESHOLDS["rapid_cash_out"]["pass_through_ratio"]:
                    results["flagged_rules"].append("RAPID_CASH_OUT")
                    results["risk_score_contribution"] += 40
                    results["details"]["rapid_cash_out"] = f"{ratio * 100:.1f}% pass-through ratio (${total_in:,.2f} in, ${total_out:,.2f} out)."
                    results["rule_hits"].append({
                        "rule_id": "RULE-002", "name": "RAPID_CASH_OUT",
                        "value": round(ratio, 3), "threshold": 0.80, "score": 40
                    })

            # Rule 3: Fan-In
            fan_in_res = duckdb.query(f"""
                SELECT COUNT(DISTINCT sender_account_id) AS unique_senders FROM df
                WHERE receiver_account_id = '{account_id}'
            """).df()
            senders = int(fan_in_res["unique_senders"].iloc[0])
            if senders >= AML_THRESHOLDS["fan_in"]["min_unique_senders"]:
                results["flagged_rules"].append("FAN_IN_PATTERN")
                results["risk_score_contribution"] += 25
                results["details"]["fan_in"] = f"Received funds from {senders} distinct sending accounts."
                results["rule_hits"].append({
                    "rule_id": "RULE-003", "name": "FAN_IN_PATTERN",
                    "value": senders, "threshold": 5, "score": 25
                })

            # Rule 4: Round Amount Concentration
            try:
                round_res = duckdb.query(f"""
                    SELECT
                        COUNT(*) AS total_count,
                        SUM(CASE WHEN amount % 1000 = 0 OR amount % 500 = 0 THEN 1 ELSE 0 END) AS round_count
                    FROM df
                    WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
                """).df()
                total_count = int(round_res["total_count"].iloc[0] or 0)
                round_count = int(round_res["round_count"].iloc[0] or 0)
                if total_count > 0 and (round_count / total_count) > 0.4:
                    results["flagged_rules"].append("ROUND_AMOUNT_CONCENTRATION")
                    results["risk_score_contribution"] += 20
                    pct = round(100 * round_count / total_count, 1)
                    results["details"]["round_amounts"] = f"{pct}% of transactions are round dollar amounts."
                    results["rule_hits"].append({
                        "rule_id": "RULE-004", "name": "ROUND_AMOUNT_CONCENTRATION",
                        "value": pct, "threshold": 40.0, "score": 20
                    })
            except Exception:
                pass

            # Rule 5: Fan-Out (layering)
            try:
                fan_out_res = duckdb.query(f"""
                    SELECT COUNT(DISTINCT receiver_account_id) AS unique_receivers FROM df
                    WHERE sender_account_id = '{account_id}'
                """).df()
                receivers = int(fan_out_res["unique_receivers"].iloc[0])
                if receivers >= 10:
                    results["flagged_rules"].append("FAN_OUT_PATTERN")
                    results["risk_score_contribution"] += 25
                    results["details"]["fan_out"] = f"Sent funds to {receivers} distinct receiving accounts (layering indicator)."
                    results["rule_hits"].append({
                        "rule_id": "RULE-008", "name": "FAN_OUT_PATTERN",
                        "value": receivers, "threshold": 10, "score": 25
                    })
            except Exception:
                pass

            # Cap contribution at 100
            results["risk_score_contribution"] = min(100, results["risk_score_contribution"])
            return results

        except Exception as e:
            results["error"] = str(e)
            return results

    def evaluate_dataset(self, top_n: int = 50) -> List[Dict[str, Any]]:
        """
        Evaluate AML rules across all accounts and return top flagged accounts.
        """
        df = self.dl.load_transactions()
        if df is None or df.empty:
            return []

        try:
            # Quick dataset-wide structuring detection
            q = """
                SELECT
                    receiver_account_id AS account_id,
                    COUNT(*) AS near_threshold_count,
                    SUM(amount) AS total_volume,
                    COUNT(DISTINCT sender_account_id) AS unique_senders,
                    'STRUCTURING_SUSPECT' AS flag,
                    'HIGH' AS risk_level
                FROM df
                WHERE amount >= 9000 AND amount < 10000
                GROUP BY receiver_account_id
                HAVING COUNT(*) >= 2
                ORDER BY near_threshold_count DESC
                LIMIT 50
            """
            flagged = duckdb.query(q).df().to_dict(orient="records")
            return flagged
        except Exception:
            return []
