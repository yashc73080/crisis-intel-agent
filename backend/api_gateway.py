import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Imports from your existing coordinator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="CrisisNet API Gateway", version="1.0.0")

# --- Agent Configuration (Copied from coordinator/main.py) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.join(current_dir, "agents")

# Define server parameters once
RISK_SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=[os.path.join(agents_dir, "risk_assessment", "main.py")],
    env=os.environ.copy()
)

GEO_SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=[os.path.join(agents_dir, "geolocation", "main.py")],
    env=os.environ.copy()
)

# --- Pydantic Schemas for Request/Response Bodies ---
class QueryEventsRequest(BaseModel):
    status_filter: str = "ASSESSED"
    limit: int = 50

class LocationSafetyRequest(BaseModel):
    user_location: List[float]  # [latitude, longitude]
    check_radius_km: float = 25.0

class ComputeRoutesRequest(BaseModel):
    origin: List[float]
    destination: List[float]
    travel_mode: str = "DRIVE"
    avoid_threats: bool = True
    alternatives: bool = True

# --- Utility Function to Handle MCP Tool Calls ---
async def call_agent_tool(server_params: StdioServerParameters, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Connects to an agent and calls a specified tool, returning the parsed JSON result."""
    try:
        # 1. Connect to the Agent Process
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 2. Call the Tool
                result = await session.call_tool(tool_name, arguments=arguments)
                
                # 3. Parse the JSON result
                if result.content and result.content[0].text:
                    return json.loads(result.content[0].text)
                else:
                    raise HTTPException(status_code=500, detail="Agent returned empty response.")
                    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Agent response was not valid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal MCP Agent error: {e}")

# --- API Endpoints ---

@app.post("/api/events/query", tags=["Risk Assessment"])
async def query_assessed_events(request: QueryEventsRequest):
    """Fetches assessed or new events from Firestore."""
    return await call_agent_tool(
        RISK_SERVER_PARAMS,
        "get_assessed_events",
        request.dict()
    )

@app.get("/api/events/high_risk", tags=["Risk Assessment"])
async def get_high_risk_events(min_risk_score: int = 70, limit: int = 50):
    """Fetches high-risk events (score >= min_risk_score) from Firestore."""
    return await call_agent_tool(
        RISK_SERVER_PARAMS,
        "get_high_risk_events",
        {"min_risk_score": min_risk_score, "limit": limit}
    )

@app.post("/api/safety/check", tags=["Geolocation Safety"])
async def check_location_safety(request: LocationSafetyRequest):
    """Comprehensive safety check for a user's current location."""
    return await call_agent_tool(
        GEO_SERVER_PARAMS,
        "get_current_location_safety",
        request.dict()
    )

@app.post("/api/routes/compute", tags=["Geolocation Safety"])
async def compute_evacuation_routes(request: ComputeRoutesRequest):
    """Computes and analyzes safe evacuation routes."""
    return await call_agent_tool(
        GEO_SERVER_PARAMS,
        "compute_routes",
        request.dict()
    )

# Optional: Endpoint for simple health check
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "CrisisNet API Gateway is running"}

if __name__ == "__main__":
    # You will run this using uvicorn from the command line
    # (Example command below)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # uvicorn api_gateway:app --reload --host 0.0.0.0 --port 8000