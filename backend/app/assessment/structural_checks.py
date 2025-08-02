# backend/app/assessment/structural_checks.py
# This file will contain concrete implementations of structural analysis rules.

from typing import List, Dict # Dict, Any no longer needed for direct use here
import networkx as nx # Added import
# Use Pydantic models from the central schema location
from app.schemas.flowchart import FlowchartDataSchema, AnalysisResult, FlowchartNodeSchema, FlowchartEdgeSchema # Updated imports
from .interfaces import AnalysisRule

# Define standard symbol types (these might come from a config or a shared model later)
SYMBOL_TYPE_START = "start"
SYMBOL_TYPE_END = "end"

class SingleStartMultipleEndRule(AnalysisRule):
    """
    Ensures the flowchart has exactly one start symbol and at least one end symbol.
    """

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        results: List[AnalysisResult] = []
        nodes: List[FlowchartNodeSchema] = flowchart_data.nodes

        start_symbols_count = 0
        end_symbols_count = 0

        for node in nodes:
            # Ensure node.type is not None before calling .lower()
            node_type_str = node.type if node.type is not None else ""
            if node_type_str.lower() == SYMBOL_TYPE_START:
                start_symbols_count += 1
            elif node_type_str.lower() == SYMBOL_TYPE_END:
                end_symbols_count += 1

        if start_symbols_count == 0:
            results.append(AnalysisResult(
                rule_id="NO_START_SYMBOL",
                message="The flowchart must have exactly one start symbol, but none was found.",
                severity="error",
                elements=[]
            ))
        elif start_symbols_count > 1:
            # Find all start nodes to list them in the message/elements
            start_node_ids = [node.id for node in nodes if (node.type if node.type is not None else "").lower() == SYMBOL_TYPE_START]
            results.append(AnalysisResult(
                rule_id="MULTIPLE_START_SYMBOLS",
                message=f"The flowchart must have exactly one start symbol, but {start_symbols_count} were found.",
                severity="error",
                elements=start_node_ids
            ))

        if end_symbols_count == 0:
            results.append(AnalysisResult(
                rule_id="NO_END_SYMBOL",
                message="The flowchart must have at least one end symbol, but none was found.",
                severity="error",
                elements=[]
            ))

        return results

class UnconnectedSymbolsRule(AnalysisRule):
    """
    Checks for symbols that are not connected to the flowchart (no incoming or outgoing edges),
    excluding start symbols (which have no incoming) and end symbols (which have no outgoing).
    """

    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        results: List[AnalysisResult] = []
        nodes: List[FlowchartNodeSchema] = flowchart_data.nodes
        edges: List[FlowchartEdgeSchema] = flowchart_data.edges
        node_ids = {node.id for node in nodes}

        # Track incoming and outgoing connections for each node ID
        incoming_connections: Dict[str, int] = {node_id: 0 for node_id in node_ids}
        outgoing_connections: Dict[str, int] = {node_id: 0 for node_id in node_ids}

        for edge in edges:
            if edge.sourceId in outgoing_connections:
                outgoing_connections[edge.sourceId] += 1
            if edge.targetId in incoming_connections:
                incoming_connections[edge.targetId] += 1

        for node in nodes:
            node_id = node.id
            node_type_str = node.type if node.type is not None else ""
            is_start_node = node_type_str.lower() == SYMBOL_TYPE_START
            is_end_node = node_type_str.lower() == SYMBOL_TYPE_END

            has_incoming = incoming_connections.get(node_id, 0) > 0
            has_outgoing = outgoing_connections.get(node_id, 0) > 0

            # Standard nodes (not start/end) must have both incoming and outgoing connections
            if not is_start_node and not is_end_node:
                if not has_incoming and not has_outgoing:
                    results.append(AnalysisResult(
                        rule_id="UNCONNECTED_SYMBOL_BOTH",
                        message=f"Symbol '{node.value or node.id}' ({node.id}) is fully unconnected.",
                        severity="warning",
                        elements=[node.id]
                    ))
                elif not has_incoming:
                    results.append(AnalysisResult(
                        rule_id="UNCONNECTED_SYMBOL_NO_INCOMING",
                        message=f"Symbol '{node.value or node.id}' ({node.id}) has no incoming connections.",
                        severity="warning",
                        elements=[node.id]
                    ))
                elif not has_outgoing:
                    results.append(AnalysisResult(
                        rule_id="UNCONNECTED_SYMBOL_NO_OUTGOING",
                        message=f"Symbol '{node.value or node.id}' ({node.id}) has no outgoing connections.",
                        severity="warning",
                        elements=[node.id]
                    ))
            
            # Start nodes must have outgoing, but no incoming is allowed by definition
            elif is_start_node and not has_outgoing and len(nodes) > 1: # only flag if not a trivial one-node flowchart
                 results.append(AnalysisResult(
                    rule_id="START_SYMBOL_NO_OUTGOING",
                    message=f"Start symbol '{node.value or node.id}' ({node.id}) has no outgoing connections.",
                    severity="warning",
                    elements=[node.id]
                ))

            # End nodes must have incoming, but no outgoing is allowed by definition
            elif is_end_node and not has_incoming and len(nodes) > 1: # only flag if not a trivial one-node flowchart
                 results.append(AnalysisResult(
                    rule_id="END_SYMBOL_NO_INCOMING",
                    message=f"End symbol '{node.value or node.id}' ({node.id}) has no incoming connections.",
                    severity="warning",
                    elements=[node.id]
                ))

        return results
