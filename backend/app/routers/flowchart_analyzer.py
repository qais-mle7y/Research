from fastapi import APIRouter, HTTPException, status, Body
from typing import List
import networkx as nx

from ..schemas.flowchart import FlowchartDataSchema, AnalysisResult, CombinedAnalysisResponse
from ..assessment.structural_checks import SingleStartMultipleEndRule, UnconnectedSymbolsRule
from ..assessment.logical_checks import InfiniteLoopRule, UnreachableCodeRule, ParallelBranchBalanceRule, OrphanedIoRule
from ..assessment.pedagogical_heuristics import DecisionNestingDepthRule
from ..assessment.interfaces import AnalysisRule
from ..feedback.generator import generate_feedback_messages
from ..utils.graph_constructor import create_graph_from_flowchart_data

router = APIRouter()

# Initialize rules
analysis_rules: List[AnalysisRule] = [
    SingleStartMultipleEndRule(),
    UnconnectedSymbolsRule(),
    InfiniteLoopRule(),
    UnreachableCodeRule(),
    ParallelBranchBalanceRule(),
    OrphanedIoRule(),
    DecisionNestingDepthRule()
]

@router.post("/analyze_flowchart",
             summary="Analyze Flowchart Data and Generate Feedback",
             description="Receives flowchart data, validates it, converts to a graph, applies analysis rules, and returns structured results and human-readable feedback.",
             response_description="A combined object containing a list of structured analysis results and a list of feedback messages.",
             response_model=CombinedAnalysisResponse,
             status_code=status.HTTP_200_OK,
             responses={
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {
                     "description": "Validation Error. The request body is malformed or missing required fields.",
                     "content": {
                         "application/json": {
                             "example": {
                                 "detail": [
                                     {
                                         "type": "missing",
                                         "loc": ["body", "nodes"],
                                         "msg": "Field required",
                                         "input": {"edges": []}
                                     }
                                 ]
                             }
                         }
                     }
                 },
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {
                     "description": "Internal Server Error during analysis.",
                     "content": {
                         "application/json": {
                             "example": {"detail": {"message": "Error during analysis: Rule 'RuleName' failed unexpectedly.", "code": "ANALYSIS_ERROR"}}
                         }
                     }
                 }
             }
            )
async def analyze_flowchart_endpoint(flowchart_data: FlowchartDataSchema = Body(...)):
    """
    Analyzes the provided flowchart data using a set of predefined rules
    and returns a combined response of structured analysis results and feedback.
    """
    # Early exit for empty or minimal flowcharts that cannot be analyzed.
    if not flowchart_data.nodes or len(flowchart_data.nodes) == 0:
        empty_result = AnalysisResult(
            rule_id="EMPTY_DATA_RECEIVED",
            message="The flowchart is empty or could not be captured correctly. Please ensure your flowchart is not blank and try again.",
            severity="warning",
            elements=[]
        )
        return CombinedAnalysisResponse(
            analysis_results=[empty_result],
            feedback_messages=generate_feedback_messages([empty_result])
        )
        
    all_analysis_results: List[AnalysisResult] = []
    graph: nx.DiGraph

    try:
        # Convert FlowchartData to NetworkX graph
        graph = create_graph_from_flowchart_data(flowchart_data)
        # For debugging or logging graph properties if needed
        # print(f"Created graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    except Exception as e:
        # Handle errors during graph creation itself, though less likely if FlowchartData is valid
        print(f"Error creating graph from flowchart data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={"message": f"Error processing flowchart structure: {str(e)}", "code": "GRAPH_CREATION_FAILED"}
        )

    for rule in analysis_rules:
        try:
            # Pass both Pydantic model and NetworkX graph to the rule
            results = rule.apply(flowchart_data, graph)
            all_analysis_results.extend(results)
        except Exception as e:
            # Log the exception from the rule appropriately in a real application
            print(f"Error during rule execution '{rule.__class__.__name__}': {e}")
            # Add a system error result for this rule failure
            all_analysis_results.append(AnalysisResult(
                rule_id="RULE_EXECUTION_ERROR",
                message=f"Rule '{rule.__class__.__name__}' failed to execute: {str(e)}",
                severity="system_error",
                elements=[] # No specific elements, as it's a rule system error
            ))
            # Optionally, re-raise if you want to halt all analysis on a single rule failure,
            # or continue to process other rules (current behavior).
    
    # Generate human-readable feedback from the analysis results
    feedback_list = generate_feedback_messages(all_analysis_results) 
    
    # Log the feedback for backend monitoring
    print(f"Analyzed flowchart: {len(flowchart_data.nodes)} nodes, {len(flowchart_data.edges)} edges.")
    print(f"Generated feedback (for logging): {feedback_list}")
    
    # Return the combined structured results and feedback messages
    return CombinedAnalysisResponse(
        analysis_results=all_analysis_results,
        feedback_messages=feedback_list
    )

# The old return for reference, now replaced by feedback_list:
    # return {
    #     "message": "Flowchart data received, parsed, and graph created successfully",
    #     "original_nodes_count": len(flowchart_data.nodes),
    #     "original_edges_count": len(flowchart_data.edges),
    #     "graph_nodes_count": graph_nodes_count,
    #     "graph_edges_count": graph_edges_count
    # } 