"""
Graph Tool — Visualization wrapper for network graph analysis.
Builds Plotly and NetworkX-based AML network visualizations.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import duckdb
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from tools.graph import GraphAnalyzer
import utils.viz as viz


class GraphTool:
    """
    Wraps GraphAnalyzer with Plotly visualization outputs.
    Generates network graphs, Sankey diagrams, and circular flow matrices.
    """

    def __init__(self, data_loader):
        self.dl = data_loader
        self.analyzer = GraphAnalyzer(data_loader)

    def build_account_network(self, account_id: str) -> Dict[str, Any]:
        """Build ego-graph with PyVis HTML and Plotly edge chart."""
        G, metrics = self.analyzer.build_ego_graph(account_id, degrees=1)
        return metrics

    def create_money_flow_sankey(self, top_n: int = 20) -> go.Figure:
        """Create a Sankey diagram of top money flows."""
        try:
            df = self.dl.load_transactions()
            if df is None or df.empty:
                return go.Figure()

            amount_col = "amount" if "amount" in df.columns else None
            if not amount_col:
                return go.Figure()

            top_flows = (
                df.groupby(["sender_account_id", "receiver_account_id"])[amount_col]
                .sum()
                .reset_index()
                .sort_values(amount_col, ascending=False)
                .head(top_n)
            )

            if top_flows.empty:
                return go.Figure()

            all_nodes = list(
                set(top_flows["sender_account_id"]).union(set(top_flows["receiver_account_id"]))
            )
            node_map = {n: i for i, n in enumerate(all_nodes)}

            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15, thickness=20,
                    line=dict(color=viz.THEME["border"], width=0.5),
                    label=[str(n)[:12] + "..." if len(str(n)) > 12 else str(n) for n in all_nodes],
                    color=viz.THEME["accent_blue"],
                ),
                link=dict(
                    source=[node_map[s] for s in top_flows["sender_account_id"]],
                    target=[node_map[t] for t in top_flows["receiver_account_id"]],
                    value=top_flows[amount_col].tolist(),
                    color="rgba(59, 130, 246, 0.35)",
                ),
            )])
            fig.update_layout(title_text="Top Money Flow — Sankey Diagram", font_size=11)
            return viz.apply_enterprise_theme(fig, height=480)
        except Exception:
            return go.Figure()

    def create_velocity_heatmap(self) -> go.Figure:
        """Create transaction velocity heatmap (hour x weekday) via VisualizationTool."""
        from tools.visualization_tool import VisualizationTool
        vt = VisualizationTool(self.dl)
        return vt.velocity_heatmap()

    def create_structuring_timeline(self) -> go.Figure:
        """Plot structuring-suspect transactions over time via VisualizationTool."""
        from tools.visualization_tool import VisualizationTool
        vt = VisualizationTool(self.dl)
        return vt.structuring_timeline()

