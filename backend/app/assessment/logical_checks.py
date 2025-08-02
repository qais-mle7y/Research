from typing import List
import networkx as nx

from app.schemas.flowchart import FlowchartDataSchema, AnalysisResult
from app.assessment.interfaces import AnalysisRule

class InfiniteLoopRule(AnalysisRule):
    '''
    Identifies potential infinite loops by finding cycles that do not have a clear exit path.
    A valid loop (like for/while) must contain a decision node that has at least one path leading outside the loop.
    '''

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        '''
        Applies the infinite loop detection rule.

        Args:
            flowchart_data: The structured Pydantic representation of the flowchart.
            graph: The NetworkX DiGraph representation of the flowchart.

        Returns:
            A list of AnalysisResult objects if infinite loops are detected, otherwise an empty list.
        '''
        results: List[AnalysisResult] = []
        try:
            cycles = list(nx.simple_cycles(graph))
            
            for cycle_nodes in cycles:
                cycle_set = set(cycle_nodes)
                has_exit = False
                
                # Check for any decision node within the cycle
                decision_nodes_in_cycle = [
                    node_id for node_id in cycle_nodes
                    if any(n.id == node_id and n.type == 'decision' for n in flowchart_data.nodes)
                ]

                if not decision_nodes_in_cycle:
                    # If there's no decision node, it's a simple, unconditional loop.
                    has_exit = False
                else:
                    # Check if any decision node has a path out of the cycle
                    for decision_node_id in decision_nodes_in_cycle:
                        successors = graph.successors(decision_node_id)
                        for successor_id in successors:
                            if successor_id not in cycle_set:
                                has_exit = True
                                break
                        if has_exit:
                            break
                
                if not has_exit:
                    elements_involved = [str(node_id) for node_id in cycle_nodes]
                    primary_element_repr = f"loop starting around node '{elements_involved[0]}'"
                    
                    results.append(AnalysisResult(
                        rule_id="MISSING_LOOP_EXIT",
                        message=f"A potential infinite loop was detected. The identified loop does not appear to have a clear exit condition. Path: {' -> '.join(elements_involved)}",
                        severity="error",
                        elements=elements_involved
                    ))

        except Exception as e:
            # Log error or handle appropriately
            print(f"Error during InfiniteLoopRule execution: {e}")
            results.append(AnalysisResult(
                rule_id="RULE_EXECUTION_ERROR",
                message=f"InfiniteLoopRule failed to execute: {str(e)}",
                severity="system_error",
                elements=[]
            ))
        return results 

class UnreachableCodeRule(AnalysisRule):
    '''
    Identifies nodes in the flowchart that are unreachable from any start node.
    '''

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        '''
        Applies the unreachable code detection rule.

        Args:
            flowchart_data: The structured Pydantic representation of the flowchart.
            graph: The NetworkX DiGraph representation of the flowchart.

        Returns:
            A list of AnalysisResult objects if unreachable nodes are detected.
        '''
        results: List[AnalysisResult] = []
        if not graph.nodes():
            return results # No nodes, so nothing is unreachable

        # Use the enhanced type detection from the frontend parser
        start_node_ids = [
            node.id for node in flowchart_data.nodes 
            if node.type == 'start'
        ]

        if not start_node_ids:
            # If no start nodes are identified, this rule cannot determine reachability.
            # Other rules (like SingleStartMultipleEndRule) should handle missing start nodes.
            return results

        all_reachable_nodes = set()
        for start_node_id in start_node_ids:
            if graph.has_node(start_node_id):
                # Perform a traversal (e.g., DFS or BFS) from this start node
                reachable_from_this_start = nx.dfs_predecessors(graph, source=start_node_id)
                all_reachable_nodes.add(start_node_id) # Add the start node itself
                all_reachable_nodes.update(reachable_from_this_start.keys())
                # DFS predecessors doesn't give all nodes in a DAG, rather a tree. Use descendants.
                all_reachable_nodes.update(nx.descendants(graph, start_node_id))


        all_node_ids = {node.id for node in flowchart_data.nodes}
        unreachable_node_ids = all_node_ids - all_reachable_nodes

        for node_id in unreachable_node_ids:
            node_info = next((n for n in flowchart_data.nodes if n.id == node_id), None)
            node_repr = f"'{node_info.value}' (ID: {node_id})" if node_info and node_info.value else f"element (ID: {node_id})"
            
            # Avoid flagging end nodes that are correctly identified by SingleStartMultipleEndRule if they become "unreachable"
            # because all paths leading to them are problematic. This rule focuses on general unreachable segments.
            # However, if an end node is truly unreachable from ANY start, it's an issue.
            # For now, we report all non-start, unreachable nodes.

            results.append(AnalysisResult(
                rule_id="UNREACHABLE_CODE",
                message=f"The {node_repr} is unreachable from any start node.",
                severity="warning",
                elements=[node_id]
            ))
        
        return results

class ParallelBranchBalanceRule(AnalysisRule):
    """
    Ensures that decision nodes have a balanced number of outgoing branches.
    For this rule, 'balanced' means exactly two outgoing edges (e.g., for true/false paths).
    A single branch is a warning, as it makes the decision redundant. More than two is also a warning. No branches is an error.
    """

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        """
        Applies the parallel branch balance rule.

        Args:
            flowchart_data: The structured Pydantic representation of the flowchart.
            graph: The NetworkX DiGraph representation of the flowchart.

        Returns:
            A list of AnalysisResult objects for any decision nodes with imbalanced branches.
        """
        results: List[AnalysisResult] = []
        
        decision_nodes = [node for node in flowchart_data.nodes if node.type == 'decision']

        for node in decision_nodes:
            if not graph.has_node(node.id):
                continue

            out_degree = graph.out_degree(node.id)
            node_repr = f"'{node.value}' (ID: {node.id})" if node.value else f"decision node (ID: {node.id})"

            if out_degree == 0:
                results.append(AnalysisResult(
                    rule_id="DECISION_NO_BRANCHES",
                    message=f"The {node_repr} is a dead end. Decision nodes must have exit paths.",
                    severity="error",
                    elements=[node.id]
                ))
            elif out_degree == 1:
                results.append(AnalysisResult(
                    rule_id="DECISION_SINGLE_BRANCH",
                    message=f"The {node_repr} has only one exit path. A decision should offer at least two alternative branches to be meaningful.",
                    severity="warning",
                    elements=[node.id]
                ))
            # We are not checking for > 2 for now, as some valid structures like switch-case might use this.
            # This can be a future pedagogical rule.
        
        return results 

class OrphanedIoRule(AnalysisRule):
    """
    Identifies input nodes that do not lead to any process or decision,
    and output nodes that are not preceded by any process or decision.
    This suggests the I/O operation is disconnected from the core logic.
    """

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        """
        Applies the orphaned I/O rule.
        """
        results: List[AnalysisResult] = []
        
        io_nodes = [node for node in flowchart_data.nodes if node.type in ['input', 'output']]
        process_or_decision_types = {'process', 'decision'}

        for node in io_nodes:
            if not graph.has_node(node.id):
                continue

            node_repr = f"'{node.value}' (ID: {node.id})" if node.value else f"I/O node (ID: {node.id})"

            if node.type == 'input':
                # Check if any successor path eventually hits a process/decision node
                has_downstream_logic = False
                try:
                    descendants = nx.descendants(graph, node.id)
                    for desc_id in descendants:
                        desc_node = next((n for n in flowchart_data.nodes if n.id == desc_id), None)
                        if desc_node and desc_node.type in process_or_decision_types:
                            has_downstream_logic = True
                            break
                    if not has_downstream_logic and descendants: # It has successors, but none are logic
                         results.append(AnalysisResult(
                            rule_id="ORPHAN_INPUT",
                            message=f"Input from {node_repr} is never used in a process or decision.",
                            severity="warning",
                            elements=[node.id]
                        ))
                except nx.NetworkXError:
                    pass # Should not happen if node is in graph

            elif node.type == 'output':
                # Check if any predecessor path originates from a process/decision node
                has_upstream_logic = False
                try:
                    ancestors = nx.ancestors(graph, node.id)
                    for anc_id in ancestors:
                        anc_node = next((n for n in flowchart_data.nodes if n.id == anc_id), None)
                        if anc_node and anc_node.type in process_or_decision_types:
                            has_upstream_logic = True
                            break
                    if not has_upstream_logic and ancestors: # It has predecessors, but none are logic
                        results.append(AnalysisResult(
                            rule_id="ORPHAN_OUTPUT",
                            message=f"Output to {node_repr} does not seem to originate from any process or decision.",
                            severity="warning",
                            elements=[node.id]
                        ))
                except nx.NetworkXError:
                    pass # Should not happen if node is in graph

        return results 