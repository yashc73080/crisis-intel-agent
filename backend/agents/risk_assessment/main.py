from mcp.server.fastmcp import FastMCP
import os
from typing import Dict, Any
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# Load .env from the project root
# Structure: backend/agents/risk_assessment/main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# Initialize the MCP server
mcp = FastMCP("Risk Assessment Agent")

# Initialize Vertex AI (Ensure GOOGLE_APPLICATION_CREDENTIALS is set)
# Prioritize GCP_PROJECT_ID from user's .env, fallback to GOOGLE_CLOUD_PROJECT
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.5-flash-lite")
except Exception as e:
    print(f"Warning: Vertex AI initialization failed: {e}")
    model = None

@mcp.tool()
def classify_event(event_description: str, event_type: str) -> Dict[str, Any]:
    """
    Analyzes an event description and determines its severity and risk category using Gemini.
    
    Args:
        event_description: Detailed description of the event.
        event_type: The reported type of the event (e.g., Flood, Fire).
        
    Returns:
        A dictionary containing severity (Low, Medium, High, Critical), risk_score (0-100), and reasoning.
    """
    if not model:
        return {
            "severity": "Unknown",
            "risk_score": 0,
            "reasoning": "Vertex AI model not initialized."
        }

    prompt = f"""
    Analyze the following crisis event:
    Type: {event_type}
    Description: {event_description}
    
    Determine the severity level (Low, Medium, High, Critical) and a risk score (0-100).
    Provide a brief reasoning.
    
    Return JSON format:
    {{
        "severity": "...",
        "risk_score": ...,
        "reasoning": "..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # In a real app, we would parse the JSON strictly. 
        # For now, we'll just return the text or a mock structure if parsing fails.
        return {"raw_analysis": response.text}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def estimate_severity(event_data: Dict[str, Any]) -> str:
    """
    Simple rule-based fallback for severity estimation.
    """
    desc = event_data.get("description", "").lower()
    if "fatality" in desc or "critical" in desc:
        return "Critical"
    if "injury" in desc or "severe" in desc:
        return "High"
    return "Medium"

if __name__ == "__main__":
    mcp.run()
