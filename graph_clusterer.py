import networkx as nx
from typing import List, Dict

class GraphClusterer:
    def __init__(self):
        self.graph = nx.Graph()
        
    def build_clusters(self, records: List[Dict], matches: List[Dict]) -> List[Dict]:
        self.graph.clear()
        
        # Add nodes
        for r in records:
            self.graph.add_node(r['internal_id'], **r)
            
        # Add edges
        for m in matches:
            if m['combined_score'] >= 0.40:
                self.graph.add_edge(m['source_id'], m['target_id'], weight=m['combined_score'])
                
        # Find clusters
        clusters = []
        for i, comp in enumerate(nx.connected_components(self.graph)):
            comp_nodes = list(comp)
            if len(comp_nodes) < 2:
                continue
                
            # Find golden record (longest description as proxy for most complete)
            golden = max(comp_nodes, key=lambda n: len(self.graph.nodes[n].get('cleaned_description', '')))
            
            cluster_members = []
            for n in comp_nodes:
                node_data = self.graph.nodes[n]
                cluster_members.append({
                    'internal_id': n,
                    'cpse': node_data.get('cpse'),
                    'material_code': node_data.get('material_code'),
                    'description': node_data.get('material_description')
                })
                
            clusters.append({
                'cluster_id': f"CLS-{i:05d}",
                'golden_record_id': golden,
                'golden_description': self.graph.nodes[golden].get('material_description'),
                'size': len(comp_nodes),
                'members': cluster_members
            })
            
        return clusters
