"""
Argus Compliance Report Exporter — Generates multi-format compliance audit reports (HTML, JSON, CSV).
Suitable for regulatory submission (FinCEN, FATF, internal compliance audit).
"""
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any

class ComplianceReportExporter:
    def __init__(self):
        pass

    def export_json(self, investigation_result: Dict[str, Any]) -> str:
        """Exports full investigation audit package as pretty-printed JSON."""
        audit_package = {
            "metadata": {
                "system": "Argus Financial Crime Intelligence Engine",
                "version": "2.4.0-enterprise",
                "timestamp": datetime.now().isoformat(),
                "classification": "CONFIDENTIAL // COMPLIANCE AUDIT"
            },
            "investigation_result": investigation_result
        }
        return json.dumps(audit_package, indent=2, default=str)

    def export_csv(self, investigation_result: Dict[str, Any]) -> str:
        """Exports flagged entity matrix as CSV."""
        feats = investigation_result.get("feature_results", {})
        top_entities = feats.get("top_entities", []) if isinstance(feats, dict) else []
        if top_entities:
            df = pd.DataFrame(top_entities)
            return df.to_csv(index=False)
        else:
            return "account_id,tx_count,total_volume,avg_amount,flag,risk_level\nN/A,0,0.0,0.0,NO_DATA,LOW"

    def export_html(self, investigation_result: Dict[str, Any]) -> str:
        """Generates professional executive HTML compliance audit report."""
        intent = investigation_result.get("intent", "N/A")
        entity_id = investigation_result.get("target_entity_id") or "N/A"
        risk = investigation_result.get("risk_results", {})
        score = risk.get("composite_score", 0)
        band = risk.get("risk_band", "UNKNOWN")
        escalation = investigation_result.get("escalation_recommendation", "Review")
        explanation = investigation_result.get("explanation", "Analysis complete.")
        behavior = investigation_result.get("agent_behavior_summary", "Standard workflow")
        plan = investigation_result.get("execution_plan", [])
        
        plan_rows = ""
        for step in plan:
            plan_rows += f"<tr><td>Step {step.get('order')}</td><td><b>{step.get('tool', '').upper()}</b></td><td>{step.get('reason')}</td></tr>"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Argus AML Compliance Investigation Audit Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #050505; color: #E2E8F0; margin: 0; padding: 40px; }}
        .header {{ border-bottom: 2px solid #1E2D52; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; }}
        .title {{ font-size: 24px; font-weight: 700; color: #FFFFFF; letter-spacing: -0.5px; }}
        .badge {{ background-color: #071D49; color: #38BDF8; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 12px; border: 1px solid #1E2D52; }}
        .card {{ background-color: #101010; border: 1px solid #1E2D52; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .metric-grid {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ flex: 1; background-color: #071D49; border: 1px solid #1E2D52; padding: 16px; border-radius: 6px; text-align: center; }}
        .metric-value {{ font-size: 28px; font-weight: 700; color: #38BDF8; margin-top: 5px; }}
        .metric-label {{ font-size: 12px; color: #94A3B8; font-weight: 600; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #1E2D52; font-size: 13px; }}
        th {{ background-color: #071D49; color: #94A3B8; font-weight: 600; }}
        .footer {{ margin-top: 40px; border-top: 1px solid #1E2D52; padding-top: 20px; font-size: 11px; color: #64748B; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">ARGUS FINANCIAL CRIME COMPLIANCE AUDIT REPORT</div>
            <div style="font-size: 13px; color: #94A3B8; margin-top: 4px;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>
        <div>
            <span class="badge">CONFIDENTIAL // REGULATORY AUDIT</span>
        </div>
    </div>

    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Composite Risk Score</div>
            <div class="metric-value">{score}/100</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Risk Classification</div>
            <div class="metric-value">{band}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Target Entity ID</div>
            <div class="metric-value" style="font-size: 20px;">{entity_id}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Parsed Intent</div>
            <div class="metric-value" style="font-size: 18px;">{intent}</div>
        </div>
    </div>

    <div class="card">
        <h3 style="margin-top:0; color:#38BDF8;">Executive Summary & Evidence Findings</h3>
        <p style="line-height:1.6;">{explanation}</p>
        <p><b>Recommended Action:</b> <span style="color:#F59E0B;">{escalation}</span></p>
        <p><b>Selected Strategy:</b> <i>{behavior}</i></p>
    </div>

    <div class="card">
        <h3 style="margin-top:0; color:#38BDF8;">Agentic Execution Plan & Audit Trail</h3>
        <table>
            <thead>
                <tr><th>Order</th><th>Tool Executed</th><th>Analytical Justification</th></tr>
            </thead>
            <tbody>
                {plan_rows}
            </tbody>
        </table>
    </div>

    <div class="footer">
        Argus Enterprise AML Platform &bull; Automated Regulatory Compliance Sign-off &bull; Version 2.4.0
    </div>
</body>
</html>
"""
        return html_content
