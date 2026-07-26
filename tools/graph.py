import duckdb
import networkx as nx
from typing import Dict, Any, Tuple
import pandas as pd

class GraphAnalyzer:
    def __init__(self, data_loader):
        self.dl = data_loader

    def build_ego_graph(self, account_id: str, degrees: int = 1, enable_physics: bool = False) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Builds a directed financial topology network graph around the target account to trace money flow.
        Returns the NetworkX graph object and a summary of network topology metrics.
        """
        df = self.dl.load_transactions()
        if df.empty:
            return nx.DiGraph(), {"error": "Dataset empty", "pyvis_html": None}
            
        # Step 1: Find direct counterparties (Degree 1)
        query_deg1 = f"""
            SELECT sender_account_id, receiver_account_id, amount
            FROM df
            WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
        """
        edges_df = duckdb.query(query_deg1).df()
        
        if edges_df.empty:
            return nx.DiGraph(), {"error": "No counterparty network found", "pyvis_html": None, "nodes_in_network": 0}

        # Step 2: Expand to degree 2 if requested
        if degrees > 1 and not edges_df.empty:
            counterparties = set(edges_df['sender_account_id']).union(set(edges_df['receiver_account_id']))
            cp_list = "', '".join(list(counterparties)[:50]) 
            query_deg2 = f"""
                SELECT sender_account_id, receiver_account_id, amount
                FROM df
                WHERE sender_account_id IN ('{cp_list}') OR receiver_account_id IN ('{cp_list}')
                LIMIT 500
            """
            edges_df = pd.concat([edges_df, duckdb.query(query_deg2).df()]).drop_duplicates()

        # Build NetworkX Directed Graph
        G = nx.from_pandas_edgelist(
            edges_df, 
            source='sender_account_id', 
            target='receiver_account_id', 
            edge_attr='amount', 
            create_using=nx.DiGraph()
        )
        
        if account_id not in G:
            return G, {"error": "Target account not found in graph.", "pyvis_html": None}

        # Calculate Enterprise Topology Metrics
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        in_degree = G.in_degree(account_id)
        out_degree = G.out_degree(account_id)
        
        density = round(nx.density(G), 4)
        avg_degree = round((2.0 * n_edges) / max(1, n_nodes), 2)
        try:
            connected_comp = nx.number_weakly_connected_components(G)
        except Exception:
            connected_comp = 1

        try:
            pagerank = nx.pagerank(G, weight='amount')
            pr_score = pagerank.get(account_id, 0.0)
            top_central = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
            central_ids = [k for k, v in top_central]
        except Exception:
            pr_score = 0.0
            central_ids = [account_id]
            
        metrics = {
            "nodes_in_network": n_nodes,
            "edges_in_network": n_edges,
            "network_density": density,
            "connected_components": connected_comp,
            "average_degree": avg_degree,
            "target_in_degree": in_degree,
            "target_out_degree": out_degree,
            "pagerank_centrality": pr_score,
            "top_central_accounts": central_ids
        }
        
        # Detect cyclic flows
        try:
            cycles = list(nx.simple_cycles(G))
            target_cycles = [c for c in cycles if account_id in c]
            metrics["cyclic_flows_detected"] = len(target_cycles)
        except Exception:
            metrics["cyclic_flows_detected"] = 0
            
        # Generate PyVis Interactive STILL Graph HTML (Physics Disabled by default)
        if n_nodes >= 2:
            try:
                from pyvis.network import Network
                net = Network(height="450px", width="100%", bgcolor="#05070B", font_color="#F9FAFB", directed=True)
                net.from_nx(G)
                
                # Freeze physics layout by default unless enable_physics is True
                net.toggle_physics(enable_physics)
                
                # Color nodes by AML Risk Tier: Red (Critical/Target), Orange (High), Amber (Medium), Blue (Low)
                for node in net.nodes:
                    nid = node['id']
                    if nid == account_id:
                        node['color'] = '#EF4444' # Critical Target
                        node['size'] = 28
                        node['title'] = f"CRITICAL TARGET: {nid}"
                    elif nid in central_ids:
                        node['color'] = '#EA580C' # High Risk Central Hub
                        node['size'] = 20
                        node['title'] = f"High Risk Central Hub: {nid}"
                    elif G.degree(nid) > 3:
                        node['color'] = '#F59E0B' # Medium Risk Hub
                        node['size'] = 16
                        node['title'] = f"Medium Risk Account: {nid}"
                    else:
                        node['color'] = '#2563EB' # Low Risk Counterparty
                        node['size'] = 12
                        node['title'] = f"Low Risk Counterparty: {nid}"
                        
                for edge in net.edges:
                    edge['color'] = 'rgba(56, 189, 248, 0.4)'
                    
                metrics["pyvis_html"] = net.generate_html()
            except Exception:
                metrics["pyvis_html"] = None
        else:
            metrics["pyvis_html"] = None

        return G, metrics
