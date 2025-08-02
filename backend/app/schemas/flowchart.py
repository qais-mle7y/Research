from pydantic import BaseModel
from typing import List, Optional

class FlowchartNodeSchema(BaseModel):
    id: str
    value: Optional[str] = None
    style: Optional[str] = None
    type: Optional[str] = None
    vertex: Optional[bool] = None
    parentId: Optional[str] = None
    color: Optional[str] = None  # Hex color for the node
    # TODO: Add geometry if needed later, matching the frontend TODO

class FlowchartEdgeSchema(BaseModel):
    id: str
    value: Optional[str] = None
    style: Optional[str] = None
    edge: Optional[bool] = None
    parentId: Optional[str] = None
    sourceId: Optional[str] = None
    targetId: Optional[str] = None

class FlowchartDataSchema(BaseModel):
    nodes: List[FlowchartNodeSchema]
    edges: List[FlowchartEdgeSchema]

class AnalysisResult(BaseModel):
    rule_id: str
    message: str
    severity: str # e.g., "error", "warning", "info"
    elements: Optional[List[str]] = None # IDs of flowchart elements involved

class CombinedAnalysisResponse(BaseModel):
    analysis_results: List[AnalysisResult]
    feedback_messages: List[str] 