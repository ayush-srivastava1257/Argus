"""
Agent Executor — High-level entry point that wraps run_investigation()
with pre/post processing, report generation, and error handling.
"""
import time
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from agent.graph import run_investigation
from agent.report_generator import ReportGenerator


_report_gen = ReportGenerator()


def execute_investigation(user_query: str, return_report: bool = False) -> Dict[str, Any]:
    """
    Top-level investigation entry point with report generation and timing.
    
    Args:
        user_query: Natural language AML investigation query.
        return_report: If True, includes a structured report dict in output.
        
    Returns:
        Full agent state dict including risk scores, explanation, and optionally report.
    """
    t_start = time.time()

    try:
        state = run_investigation(user_query)
    except Exception as e:
        return {
            "error": str(e),
            "user_query": user_query,
            "explanation": f"Investigation failed: {str(e)}",
            "escalation_recommendation": "REVIEW — Manual fallback required.",
        }

    # Inject total wall-clock time
    state["total_duration_ms"] = round((time.time() - t_start) * 1000, 1)

    if return_report:
        try:
            state["structured_report"] = _report_gen.generate_investigation_report(state)
            state["report_markdown"] = _report_gen.to_markdown(state["structured_report"])
            state["report_html_card"] = _report_gen.to_html_summary(state["structured_report"])
        except Exception as e:
            state["report_error"] = str(e)

    return state


def execute_batch_pattern_scan(pattern: str, days: int = 30) -> Dict[str, Any]:
    """Convenience wrapper for pattern-specific batch scans."""
    query = f"Find {pattern} patterns in the last {days} days"
    return execute_investigation(query, return_report=True)


def execute_entity_investigation(entity_id: str) -> Dict[str, Any]:
    """Convenience wrapper for single-entity investigations."""
    query = f"Is customer ID {entity_id} suspicious?"
    return execute_investigation(query, return_report=True)
