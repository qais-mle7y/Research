from fastapi import APIRouter, HTTPException, Body, Query
from typing import Dict, Type, Literal
import networkx as nx

from app.schemas.flowchart import FlowchartDataSchema
from app.utils.graph_constructor import create_graph_from_flowchart_data
from app.codegen.interfaces import CodeGenerator
from app.codegen.generators import CppCodeGenerator, JavaCodeGenerator, PythonCodeGenerator

router = APIRouter()

GENERATOR_MAP: Dict[str, Type[CodeGenerator]] = {
    "cpp": CppCodeGenerator,
    "c++": CppCodeGenerator,
    "java": JavaCodeGenerator,
    "python": PythonCodeGenerator,
}

class CodeGenerationRequest(FlowchartDataSchema):
    language: str = Query(..., description="Target programming language (e.g., 'python', 'cpp', 'java')")
    style: Literal['educational', 'direct'] = Query('educational', description="The style of code to generate ('educational' or 'direct').")

@router.post("/generate_code", 
             summary="Generate Code from Flowchart Data",
             description="Receives flowchart data, a target language, and a style, then generates the corresponding source code.",
             response_description="JSON object containing the generated source code.",
             responses={
                 200: {"content": {"application/json": {"example": {"code": "def main():..."}}}},
                 400: {"description": "Unsupported language.", "content": {"application/json": {"example": {"detail": {"message": "Unsupported language: lisp", "code": "UNSUPPORTED_LANGUAGE"}}}}},
                 422: {"description": "Validation Error in flowchart data."},
                 500: {"description": "Error during code generation.", "content": {"application/json": {"example": {"detail": {"message": "An error occurred.", "code": "CODE_GENERATION_FAILED"}}}}}
             }
            )
async def generate_code_endpoint(request_data: CodeGenerationRequest = Body(...)):
    language = request_data.language.lower()
    if language not in GENERATOR_MAP:
        raise HTTPException(
            status_code=400, 
            detail={"message": f"Unsupported language: {request_data.language}. Supported: {list(GENERATOR_MAP.keys())}", "code": "UNSUPPORTED_LANGUAGE"}
        )

    graph: nx.DiGraph
    try:
        flowchart_model = FlowchartDataSchema(nodes=request_data.nodes, edges=request_data.edges)
        graph = create_graph_from_flowchart_data(flowchart_model)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={"message": f"Error creating graph from flowchart data: {str(e)}", "code": "GRAPH_CREATION_FAILED"}
        )

    generator_class = GENERATOR_MAP[language]
    generator_instance = generator_class()

    # The 'idiomatic' parameter now maps to whether the style is 'direct'
    should_be_idiomatic = request_data.style == 'direct'

    try:
        generated_code = generator_instance.generate_code(
            flowchart_data=flowchart_model, 
            graph=graph, 
            idiomatic=should_be_idiomatic
        )
        return {"code": generated_code}
    except Exception as e:
        print(f"Error during code generation with {generator_class.__name__} for '{language}': {e}")
        raise HTTPException(
            status_code=500, 
            detail={"message": f"Error during code generation: {str(e)}", "code": "CODE_GENERATION_FAILED"}
        )

# To make FastAPI return plain text for this endpoint specifically when a string is returned:
# We can achieve this by ensuring the @router.post decorator doesn't specify a response_model 
# that would force JSON, and by returning a string. 
# If issues persist, explicitly use Response(content=generated_code, media_type="text/plain")
# For now, relying on FastAPI's default behavior for string returns and the `responses` annotation. 