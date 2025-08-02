from abc import ABC, abstractmethod
from typing import Any
import networkx as nx
from app.schemas.flowchart import FlowchartDataSchema

class CodeGenerator(ABC):
    '''
    Interface for a code generator that translates a flowchart into a specific programming language.
    '''

    @abstractmethod
    def generate_code(
        self, 
        flowchart_data: FlowchartDataSchema, 
        graph: nx.DiGraph,
        idiomatic: bool = False
    ) -> str:
        '''
        Generates code from the flowchart.

        Args:
            flowchart_data: The structured Pydantic representation of the flowchart.
            graph: The NetworkX DiGraph representation of the flowchart.
            idiomatic: If True, attempt to generate more idiomatic code for the target language,
                       otherwise perform a more direct symbol-to-code translation.

        Returns:
            A string containing the generated code.
        '''
        pass 