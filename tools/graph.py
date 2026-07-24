import duckdb
import networkx as nx
from typing import Dict, Any, Tuple
import pandas as pd

class GraphAnalyzer:
    def __init__(self, data_loader):
        self.dl = data_loader

    def build_ego_graph(self, account_id: str, degrees: int = 1) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Builds a directed network graph around the target account to trace money flow.
        Returns the NetworkX graph object and a summary of graph metrics.
        """
        df = self.dl.load_transactions()
        
        # Step 1: Find all direct counterparties (Degree 1)
        query_deg1 = f"""
            SELECT sender_account_id, receiver_account_id, amount
            FROM df
            WHERE sender_account_id = '{account_id}' OR receiver_account_id = '{account_id}'
        """
        edges_df = duckdb.query(query_deg1).df()
        
        # Step 2: If degrees == 2, expand the search to counterparties' counterparties
        if degrees > 1 and not edges_df.empty:
            counterparties = set(edges_df['sender_account_id']).union(set(edges_df['receiver_account_id']))
            # limit the list to prevent massive queries in dense networks
            cp_list = "', '".join(list(counterparties)[:50]) 
            query_deg2 = f"""
                SELECT sender_account_id, receiver_account_id, amount
                FROM df
                WHERE sender_account_id IN ('{cp_list}') OR receiver_account_id IN ('{cp_list}')
                LIMIT 500
            """
            edges_df = pd.concat([edges_df, duckdb.query(query_deg2).df()]).drop_duplicates()

        # Build the NetworkX Graph
        G = nx.from_pandas_edgelist(
            edges_df, 
            source='sender_account_id', 
            target='receiver_account_id', 
            edge_attr='amount', 
            create_using=nx.DiGraph()
        )
        
        if account_id not in G:
            return G, {"error": "Target account not found in graph."}

        # Calculate Graph Metrics
        in_degree = G.in_degree(account_id)
        out_degree = G.out_degree(account_id)
        
        # PageRank (measures influence/centrality of the node)
        try:
            pagerank = nx.pagerank(G, weight='amount')
            pr_score = pagerank.get(account_id, 0.0)
        except:
            pr_score = 0.0
            
        metrics = {
            "nodes_in_network": G.number_of_nodes(),
            "edges_in_network": G.number_of_edges(),
            "target_in_degree": in_degree,
            "target_out_degree": out_degree,
            "pagerank_centrality": pr_score
        }
        
        # Look for cyclic patterns (money returning to source)
        try:
            cycles = list(nx.simple_cycles(G))
            # Only count cycles involving our target account
            target_cycles = [c for c in cycles if account_id in c]
            metrics["cyclic_flows_detected"] = len(target_cycles)
        except nx.NetworkXNoCycle:
            metrics["cyclic_flows_detected"] = 0
            
        # Generate Interactive PyVis Graph HTML
        try:
            from pyvis.network import Network
            net = Network(height="400px", width="100%", bgcolor="#080D16", font_color="#E7EDF5", directed=True)
            # Add nodes and edges from NetworkX graph
            net.from_nx(G)
            
            # Highlight target account in red
            for node in net.nodes:
                if node['id'] == account_id:
                    node['color'] = '#EF4444'
                    node['size'] = 25
                else:
                    node['color'] = '#3B82F6'
                    
            # Generate HTML string
            metrics["pyvis_html"] = net.generate_html()
        except ImportError:
            metrics["pyvis_html"] = None
            
        return G, metrics
