from abc import ABC, abstractmethod
from typing import List
import networkx as nx

# from typing import Any, Dict # No longer needed for these specific types
from app.schemas.flowchart import FlowchartDataSchema, AnalysisResult

class AnalysisRule(ABC):
    """
    Interface for an analysis rule that can be applied to flowchart data.
    """

    @abstractmethod
    def apply(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> List[AnalysisResult]:
        """
        Applies the analysis rule to the given flowchart data and its graph representation.

        Args:
            flowchart_data: The structured Pydantic representation of the flowchart.
            graph: The NetworkX DiGraph representation of the flowchart.

        Returns:
            A list of analysis results (e.g., errors, warnings, suggestions).
            An empty list if no issues are found by this rule.
        """
        pass 