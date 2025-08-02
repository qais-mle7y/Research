from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import flowchart_analyzer, code_generator_router

app = FastAPI(
    title="Flowchart Learning & Analysis Tool API",
    description="API for analyzing flowcharts and generating code.",
    version="0.2.0"
)

# CORS (Cross-Origin Resource Sharing) Middleware
# This allows the frontend (running on a different domain/port) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend's domain
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard HTTP methods
    allow_headers=["*"], # Allows all headers
)

# Include the flowchart_analyzer router
# All routes in flowchart_analyzer will be prefixed with /api/v1
app.include_router(
    flowchart_analyzer.router, 
    prefix="/api/v1/analysis",
    tags=["Flowchart Analysis"]
)

# Include the code_generator_router
app.include_router(
    code_generator_router.router, 
    prefix="/api/v1/codegen", 
    tags=["Code Generation"]
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Flowchart Learning & Analysis Tool API"}

@app.get("/health", tags=["Health Check"])
async def read_health():
    """
    Health check endpoint to verify that the API is running.
    """
    return {"status": "ok"} 