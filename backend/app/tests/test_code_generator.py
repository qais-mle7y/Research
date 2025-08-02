import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status

from ..main import app

BASE_URL = "/api/v1/codegen/generate_code"

# A standard, simple flowchart for testing all generators
SIMPLE_FLOWCHART_PAYLOAD = {
    "nodes": [
        {"id": "n1", "value": "Start", "style": "ellipse", "type": "start"},
        {"id": "n2", "value": "x = 10", "style": "rect", "type": "process"},
        {"id": "n3", "value": "End", "style": "ellipse", "type": "end"}
    ],
    "edges": [
        {"id": "e1", "sourceId": "n1", "targetId": "n2"},
        {"id": "e2", "sourceId": "n2", "targetId": "n3"}
    ]
}

@pytest.mark.asyncio
@pytest.mark.parametrize("language, expected_keywords", [
    ("python", ["def main():", "STEP 1 of", "STEP 2 of", "STEP 3 of"]),
    ("cpp", ["int main()", "STEP 1 of", "STEP 2 of", "STEP 3 of"]),
    ("java", ["public static void main", "STEP 1 of", "STEP 2 of", "STEP 3 of"])
])
async def test_generate_code_for_all_languages(language, expected_keywords):
    """Test successful code generation for each supported language with linear structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {**SIMPLE_FLOWCHART_PAYLOAD, "language": language}
        response = await ac.post(BASE_URL, json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "code" in data
    generated_code = data["code"]
    
    for keyword in expected_keywords:
        assert keyword in generated_code
    
    # Ensure no per-node functions are generated
    if language == "python":
        assert "def step_" not in generated_code
    elif language == "cpp":
        assert "void flowchart_step_" not in generated_code
    elif language == "java":
        assert "public static void flowchartStep" not in generated_code

@pytest.mark.asyncio
async def test_generate_code_unsupported_language():
    """Test that requesting an unsupported language returns a 400 error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {**SIMPLE_FLOWCHART_PAYLOAD, "language": "cobol"}
        response = await ac.post(BASE_URL, json=payload)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Unsupported language" in data["detail"]["message"]

@pytest.mark.asyncio
async def test_generate_code_with_educational_style():
    """Test that the default 'educational' style includes explanatory comments."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            **SIMPLE_FLOWCHART_PAYLOAD,
            "language": "python",
            "style": "educational"
        }
        response = await ac.post(BASE_URL, json=payload)
        
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Educational comments are a key feature of this style
    assert "EDUCATIONAL PYTHON CODE" in data["code"]
    assert "Program execution starts here" in data["code"]

@pytest.mark.asyncio
async def test_generate_code_with_invalid_flowchart_data():
    """Test that malformed flowchart data returns a 422 error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Malformed payload (nodes is not a list)
        payload = {
            "nodes": {"id": "n1"},
            "edges": [],
            "language": "python"
        }
        response = await ac.post(BASE_URL, json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 