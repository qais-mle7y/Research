import networkx as nx
from typing import Dict, Any, Tuple, List, Optional
from ..schemas.flowchart import FlowchartDataSchema, FlowchartNodeSchema, FlowchartEdgeSchema
from .type_normalizer import normalize_node_type
import re

def parse_subroutine_info(value: str) -> Tuple[Optional[str], List[str]]:
    """
    Extracts subroutine name and parameters from a node's value text.
    
    Args:
        value: The text content of the subroutine node
        
    Returns:
        Tuple of (function_name, parameter_list)
    """
    if not value:
        return None, []
    
    value = value.strip()
    
    # Pattern 1: function name(param1, param2, ...)
    pattern1 = r'(?:function|def|void|int|float|double|string|subroutine|procedure|method)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)'
    match1 = re.search(pattern1, value, re.IGNORECASE)
    if match1:
        func_name = match1.group(1)
        params_str = match1.group(2).strip()
        params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
        return func_name, params
    
    # Pattern 2: just name(param1, param2, ...)
    pattern2 = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)'
    match2 = re.search(pattern2, value)
    if match2:
        func_name = match2.group(1)
        params_str = match2.group(2).strip()
        params = [p.strip() for p in params_str.split(',') if p.strip()] if params_str else []
        return func_name, params
    
    # Pattern 3: call/invoke function_name
    pattern3 = r'(?:call|invoke)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    match3 = re.search(pattern3, value, re.IGNORECASE)
    if match3:
        func_name = match3.group(1)
        return func_name, []  # Call without visible parameters
    
    # Pattern 4: just a function name (assume it's a function)
    pattern4 = r'^([a-zA-Z_][a-zA-Z0-9_]*)$'
    match4 = re.search(pattern4, value)
    if match4:
        func_name = match4.group(1)
        return func_name, []
    
    return None, []

def create_graph_from_flowchart_data(data: FlowchartDataSchema) -> nx.DiGraph:
    """
    Constructs a NetworkX DiGraph from FlowchartDataSchema.

    Nodes are added with their attributes, and their 'type' is normalized
    based on style and value to ensure consistency for analysis.

    Args:
        data: An instance of FlowchartDataSchema containing nodes and edges.

    Returns:
        A NetworkX DiGraph object representing the flowchart.
    """
    graph = nx.DiGraph()

    for node_data in data.nodes:
        # Convert Pydantic model to dict for attributes, excluding None values
        node_attrs: Dict[str, Any] = node_data.model_dump(exclude_none=True)
        
        # Normalize the node type for consistent analysis downstream
        normalized_type = normalize_node_type(
            style=node_data.style,
            value=node_data.value,
            existing_type=node_data.type
        )
        node_attrs['type'] = normalized_type
        
        # If this is a subroutine node, parse the function information
        if normalized_type == 'subroutine':
            func_name, params = parse_subroutine_info(node_data.value or '')
            node_attrs['subroutine_name'] = func_name
            node_attrs['subroutine_params'] = params
        
        # The node ID for NetworkX will be the 'id' field from the Pydantic model.
        # All other fields become attributes of the node in the graph.
        graph.add_node(node_data.id, **node_attrs)

    for edge_data in data.edges:
        # Convert Pydantic model to dict for attributes, excluding None values
        edge_attrs: Dict[str, Any] = edge_data.model_dump(exclude_none=True)
        # Remove sourceId and targetId from attributes as they define the edge itself
        edge_attrs.pop('sourceId', None)
        edge_attrs.pop('targetId', None)
        
        # Check if source and target nodes exist in the graph before adding edge
        # Also ensure sourceId and targetId are not None before using them
        if edge_data.sourceId and edge_data.targetId and \
           graph.has_node(edge_data.sourceId) and graph.has_node(edge_data.targetId):
            graph.add_edge(edge_data.sourceId, edge_data.targetId, **edge_attrs)
        else:
            # Handle missing nodes or missing sourceId/targetId
            print(f"Warning: Skipping edge ID {edge_data.id} due to missing source/target node or ID. "
                  f"Source: {edge_data.sourceId}, Target: {edge_data.targetId}")

    return graph 