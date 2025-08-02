from typing import List
import networkx as nx

from app.schemas.flowchart import FlowchartDataSchema, AnalysisResult
from app.assessment.interfaces import AnalysisRule

class DecisionNestingDepthRule(AnalysisRule):
    """
    Analyzes the nesting depth of decision nodes.
    Issues a warning if the number of preceding decision nodes on the longest path
    from a start node exceeds a defined threshold.
    """
    MAX_DEPTH = 3  # Configurable threshold for nesting

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        """
        Applies the decision nesting depth rule.
        """
        results: List[AnalysisResult] = []
        if not graph.nodes():
            return results

        start_node_ids = [node.id for node in flowchart_data.nodes if node.type == 'start']
        if not start_node_ids:
            return results

        decision_nodes = [node for node in flowchart_data.nodes if node.type == 'decision']

        for decision_node in decision_nodes:
            if not graph.has_node(decision_node.id):
                continue

            max_depth = 0
            # Find the longest path from any start node to this decision node
            for start_id in start_node_ids:
                if nx.has_path(graph, start_id, decision_node.id):
                    # Consider all simple paths to find the one with the most decisions
                    for path in nx.all_simple_paths(graph, source=start_id, target=decision_node.id):
                        # Count how many nodes in this path are decisions (excluding the current one)
                        path_decisions = sum(1 for node_id in path[:-1] if any(n.id == node_id and n.type == 'decision' for n in flowchart_data.nodes))
                        if path_decisions > max_depth:
                            max_depth = path_decisions
            
            # The nesting depth is the number of preceding decisions.
            # If current node is a decision, its depth is max_depth.
            nesting_depth = max_depth

            if nesting_depth >= self.MAX_DEPTH:
                node_repr = f"'{decision_node.value}' (ID: {decision_node.id})" if decision_node.value else f"decision node (ID: {decision_node.id})"
                results.append(AnalysisResult(
                    rule_id="DEEP_NESTING",
                    message=f"The {node_repr} is nested deeply ({nesting_depth + 1} levels). Consider simplifying the logic to improve readability.",
                    severity="info", # Pedagogical feedback is often informational
                    elements=[decision_node.id]
                ))

        return results 