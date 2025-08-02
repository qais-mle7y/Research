import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status

from ..main import app

# The base URL is now pointing to the new prefixed path
BASE_URL = "/api/v1/analysis/analyze_flowchart"

@pytest.mark.asyncio
async def test_analyze_flowchart_valid_simple():
    """Test analysis of a basic, valid flowchart."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nodes": [
                {"id": "n1", "value": "Start", "style": "ellipse", "type": "start"},
                {"id": "n2", "value": "Do something", "style": "rect", "type": "process"},
                {"id": "n3", "value": "End", "style": "ellipse", "type": "end"}
            ],
            "edges": [
                {"id": "e1", "sourceId": "n1", "targetId": "n2"},
                {"id": "e2", "sourceId": "n2", "targetId": "n3"}
            ]
        }
        response = await ac.post(BASE_URL, json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "analysis_results" in data
    assert "feedback_messages" in data
    # For a valid chart, we expect no error/warning results. Info messages are okay.
    assert not any(r['severity'] in ['error', 'warning'] for r in data['analysis_results'])
    assert len(data['feedback_messages']) > 0

@pytest.mark.asyncio
async def test_analyze_flowchart_no_start_symbol():
    """Test for 'NO_START_SYMBOL' error when no start node is present."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nodes": [{"id": "n1", "value": "Process", "style": "rect"}],
            "edges": []
        }
        response = await ac.post(BASE_URL, json=payload)
        
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(r['rule_id'] == 'NO_START_SYMBOL' for r in data['analysis_results'])
    assert any("must have exactly one start symbol, but none was found" in msg for msg in data['feedback_messages'])

@pytest.mark.asyncio
async def test_analyze_flowchart_multiple_start_symbols():
    """Test for 'MULTIPLE_START_SYMBOLS' error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nodes": [
                {"id": "n1", "value": "Start 1", "style": "ellipse"},
                {"id": "n2", "value": "Start 2", "style": "ellipse"}
            ],
            "edges": []
        }
        response = await ac.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(r['rule_id'] == 'MULTIPLE_START_SYMBOLS' for r in data['analysis_results'])
    assert any("must have exactly one start symbol, but 2 were found" in msg for msg in data['feedback_messages'])

@pytest.mark.asyncio
async def test_analyze_flowchart_unreachable_code():
    """Test for 'UNREACHABLE_CODE' warning."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nodes": [
                {"id": "n1", "value": "Start", "style": "ellipse"},
                {"id": "n2", "value": "End", "style": "ellipse"},
                {"id": "n3", "value": "Unreachable", "style": "rect"} # This node is not connected
            ],
            "edges": [{"id": "e1", "sourceId": "n1", "targetId": "n2"}]
        }
        response = await ac.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(r['rule_id'] == 'UNREACHABLE_CODE' for r in data['analysis_results'])
    assert any("is unreachable from any start node" in msg for msg in data['feedback_messages'])

@pytest.mark.asyncio
async def test_analyze_flowchart_infinite_loop():
    """Test for 'MISSING_LOOP_EXIT' error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nodes": [
                {"id": "n1", "value": "Start", "style": "ellipse"},
                {"id": "n2", "value": "Process 1", "style": "rect"},
                {"id": "n3", "value": "Process 2", "style": "rect"}
            ],
            "edges": [
                {"id": "e1", "sourceId": "n1", "targetId": "n2"},
                {"id": "e2", "sourceId": "n2", "targetId": "n3"},
                {"id": "e3", "sourceId": "n3", "targetId": "n2"} # Loop back with no decision
            ]
        }
        response = await ac.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(r['rule_id'] == 'MISSING_LOOP_EXIT' for r in data['analysis_results'])
    assert any("potential infinite loop was detected" in msg for msg in data['feedback_messages'])

@pytest.mark.asyncio
async def test_analyze_flowchart_empty_data_payload():
    """Test server response for a completely empty request body."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {} # Empty JSON object
        response = await ac.post(BASE_URL, json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_analyze_flowchart_empty_nodes_list():
    """Test server response for request with empty nodes list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"nodes": [], "edges": []}
        response = await ac.post(BASE_URL, json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert any(r['rule_id'] == 'EMPTY_DATA_RECEIVED' for r in data['analysis_results'])

@pytest.mark.asyncio
async def test_analyze_flowchart_type_normalization():
    """Test that shape-based type normalization correctly identifies nodes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "nodes": [
                # No 'type' field, should be inferred from style
                {"id": "n1", "value": "Start", "style": "ellipse"},
                {"id": "n2", "value": "Is it valid?", "style": "rhombus"},
                {"id": "n3", "value": "End", "style": "ellipse"},
            ],
            "edges": [
                {"id": "e1", "sourceId": "n1", "targetId": "n2"},
                {"id": "e2", "sourceId": "n2", "targetId": "n3"}
            ]
        }
        response = await ac.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # No 'MULTIPLE_START_SYMBOLS' error means n1 was seen as start, n3 as end.
    # No 'DECISION_SINGLE_BRANCH' means n2 was seen as a decision.
    assert not any(r['rule_id'] == 'MULTIPLE_START_SYMBOLS' for r in data['analysis_results'])
    assert any(r['rule_id'] == 'DECISION_SINGLE_BRANCH' for r in data['analysis_results'])
