from mcp.server.fastmcp import FastMCP
import os
import json
from typing import Dict, Any
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# Load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

mcp = FastMCP("Communication Agent")

# Initialize Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.5-flash-lite")
except Exception as e:
    print(f"Warning: Vertex AI initialization failed: {e}")
    model = None

@mcp.tool()
def parse_user_intent(user_input: str) -> Dict[str, str]:
    """
    Analyzes natural language input to determine the appropriate data source and location.
    
    Args:
        user_input: The user's query or description of the situation.
        
    Returns:
        A dictionary with 'source' (USGS, MOCK, GDACS) and 'location' (extracted entity or None).
    """
    if not model:
        # Fallback if model fails
        return {"source": "GDACS", "location": None, "error": "Model not initialized"}

    prompt = f"""
    You are an intent classification agent for a crisis intelligence system.
    Your job is to map a user's description of a crisis to a data source and extract the location.

    Data Sources:
    - "USGS": Use for Earthquakes, tremors, shaking, seismic activity.
    - "GDACS": Use for real-world general disasters like Floods, Fires, Cyclones, Hurricanes, and Tsunamis. This is the default for real events that are not earthquakes.
    - "MOCK": Use ONLY when the user explicitly asks for "test", "mock", or "simulation" data. Do NOT use for real event queries like "is there a flood".

    User Input: "{user_input}"

    Extract:
    1. Source (USGS, MOCK, or GDACS)
    2. Location (City, State, Country, or Region). If a US state name is mentioned (e.g., "California"), normalize it to its two-letter abbreviation (e.g., "CA"). If no location is mentioned, return null.

    Return ONLY valid JSON in this format:
    {{
        "source": "...",
        "location": "..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("\n", 1)[0]
        
        return json.loads(text)
    except Exception as e:
        return {"source": "GDACS", "location": None, "error": str(e)}

if __name__ == "__main__":
    mcp.run()
