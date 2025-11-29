import sys
import os
import json
import uuid
import re
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from google.cloud import firestore
from dotenv import load_dotenv

# Imports from the user's snippet and ADK
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.google_search_tool import google_search
from google.genai import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

# Load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# Initialize Vertex AI (Ensure GOOGLE_APPLICATION_CREDENTIALS is set)
# Prioritize GCP_PROJECT_ID from user's .env, fallback to GOOGLE_CLOUD_PROJECT
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Ensure these are set in os.environ for google.genai.Client to pick up
if PROJECT_ID:
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
if LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
# Force Vertex AI usage if using Google Cloud Project
if PROJECT_ID:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

# Initialize Firestore client
db = firestore.Client()
EVENTS_COLLECTION = "crisis_events"

mcp = FastMCP("Risk Assessment Agent")

# Retry configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Define the Risk Assessment Agent
risk_agent = LlmAgent(
    name="risk_assessment_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Analyzes crisis events and determines risk/severity using Google Search.",
    instruction="""
    You are a risk assessment expert. Your goal is to analyze a given crisis event.
    
    1. Use the 'google_search' tool to find real-time information and context about the event. 
       Search for the event description, location, and type. Look for news and official reports.
    2. Based on the event details and the search results, determine the:
       - Severity (Low, Medium, High, Critical)
       - Risk Score (0-100)
       - Detailed Reasoning
    
    3. CRITICAL: You MUST respond with ONLY a valid JSON object. No markdown, no explanations, just JSON:
    {"severity": "High", "risk_score": 85, "reasoning": "your detailed reasoning here"}
    
    Do NOT use markdown formatting like **bold** or code blocks. Return raw JSON only.
    """,
    tools=[google_search]
)

@mcp.tool()
def get_assessed_events(status_filter: str = "ASSESSED", limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves events from Firestore by status for monitoring and analysis.
    
    Args:
        status_filter: Filter by status (NEW, ASSESSED, ERROR). Default: ASSESSED.
        limit: Maximum number of events to retrieve. Default: 50.
        
    Returns:
        List of event documents matching the filter.
    """
    try:
        query = db.collection(EVENTS_COLLECTION).where("status", "==", status_filter).limit(limit)
        docs = query.stream()
        
        events = []
        for doc in docs:
            event_data = doc.to_dict()
            event_data["_doc_id"] = doc.id
            # Convert Firestore timestamps to ISO strings for JSON serialization
            if "created_at" in event_data and event_data["created_at"]:
                event_data["created_at"] = event_data["created_at"].isoformat() if hasattr(event_data["created_at"], "isoformat") else str(event_data["created_at"])
            if "assessed_at" in event_data and event_data["assessed_at"]:
                event_data["assessed_at"] = event_data["assessed_at"].isoformat() if hasattr(event_data["assessed_at"], "isoformat") else str(event_data["assessed_at"])
            events.append(event_data)
        
        return events
        
    except Exception as e:
        return [{"error": f"Failed to query Firestore: {str(e)}"}]


@mcp.tool()
def get_high_risk_events(min_risk_score: int = 70, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves high-risk events from Firestore for prioritized response.
    
    Args:
        min_risk_score: Minimum risk score threshold (0-100). Default: 70.
        limit: Maximum number of events to retrieve. Default: 50.
        
    Returns:
        List of high-risk event documents.
    """
    try:
        # Note: Firestore requires an index for this query
        # Query for ASSESSED events with risk score above threshold
        query = (db.collection(EVENTS_COLLECTION)
                .where("status", "==", "ASSESSED")
                .where("risk_assessment.risk_score", ">=", min_risk_score)
                .limit(limit))
        
        docs = query.stream()
        
        events = []
        for doc in docs:
            event_data = doc.to_dict()
            event_data["_doc_id"] = doc.id
            # Convert timestamps
            if "created_at" in event_data and event_data["created_at"]:
                event_data["created_at"] = event_data["created_at"].isoformat() if hasattr(event_data["created_at"], "isoformat") else str(event_data["created_at"])
            if "assessed_at" in event_data and event_data["assessed_at"]:
                event_data["assessed_at"] = event_data["assessed_at"].isoformat() if hasattr(event_data["assessed_at"], "isoformat") else str(event_data["assessed_at"])
            events.append(event_data)
        
        return events
        
    except Exception as e:
        # If index doesn't exist, fall back to client-side filtering
        try:
            query = db.collection(EVENTS_COLLECTION).where("status", "==", "ASSESSED").limit(limit * 2)
            docs = query.stream()
            
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                risk_score = event_data.get("risk_assessment", {}).get("risk_score", 0)
                if risk_score >= min_risk_score:
                    event_data["_doc_id"] = doc.id
                    if "created_at" in event_data and event_data["created_at"]:
                        event_data["created_at"] = event_data["created_at"].isoformat() if hasattr(event_data["created_at"], "isoformat") else str(event_data["created_at"])
                    if "assessed_at" in event_data and event_data["assessed_at"]:
                        event_data["assessed_at"] = event_data["assessed_at"].isoformat() if hasattr(event_data["assessed_at"], "isoformat") else str(event_data["assessed_at"])
                    events.append(event_data)
                    if len(events) >= limit:
                        break
            
            return events
        except Exception as fallback_error:
            return [{"error": f"Failed to query high-risk events: {str(fallback_error)}"}]


@mcp.tool()
def classify_event(event_description: str, event_type: str, location: str = "", coordinates: List[float] = None) -> Dict[str, Any]:
    """
    Analyzes an event description and determines its severity and risk category using an AI agent with Google Search access.
    
    Args:
        event_description: Detailed description of the event.
        event_type: The reported type of the event (e.g., Flood, Fire).
        location: The location of the event.
        coordinates: The [longitude, latitude] of the event.
        
    Returns:
        A dictionary containing severity (Low, Medium, High, Critical), risk_score (0-100), and reasoning.
    """
    
    prompt = f"""
    Analyze this event:
    - Type: {event_type}
    - Description: {event_description}
    - Location: {location}
    - Coordinates: {coordinates}
    """
    
    try:
        # Initialize Runner and Session Service with UNIQUE session ID
        session_id = f"mcp_session_{uuid.uuid4()}"
        session_service = InMemorySessionService()
        session_service.create_session_sync(app_name="risk_assessment_app", user_id="mcp_user", session_id=session_id)
        runner = Runner(agent=risk_agent, app_name="risk_assessment_app", session_service=session_service)
        
        # Create content object
        content = types.Content(parts=[types.Part(text=prompt)])
        
        # Run the agent with the unique session
        events = runner.run(user_id="mcp_user", session_id=session_id, new_message=content)
        
        final_text = ""
        # Consume ALL events to allow agent to complete tool calls
        for event in events:
            print(f"DEBUG: Event type: {type(event).__name__}", file=sys.stderr)
            
            # Try to get content from event.content first (ADK Event structure)
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_text += part.text
                        print(f"DEBUG: Extracted text from event.content: {part.text[:100]}...", file=sys.stderr)
            
            # Fallback: Try event.response (direct LLM response structure)
            elif getattr(event, "response", None):
                for candidate in getattr(event.response, "candidates", []) or []:
                    for part in getattr(candidate.content, "parts", []) or []:
                        if getattr(part, "text", ""):
                            final_text += part.text
                            print(f"DEBUG: Extracted text from event.response: {part.text[:100]}...", file=sys.stderr)

        # Debug: Print what we got
        print(f"DEBUG: final_text = '{final_text}'", file=sys.stderr)
        print(f"DEBUG: final_text length = {len(final_text)}", file=sys.stderr)
        
        text = final_text.strip()
        
        if not text:
             return {
                "severity": "Unknown",
                "risk_score": 0,
                "reasoning": "Agent returned empty response."
            }

        print(f"DEBUG: About to parse: '{text}'", file=sys.stderr)
        # Try to parse as JSON directly
        try:
            return json.loads(text)
        except json.JSONDecodeError as je:
            print(f"DEBUG: JSON parse failed: {je}, trying to extract from markdown...", file=sys.stderr)
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Extract structured data from markdown-style response
            severity_match = re.search(r'\*\*(?:Severity|severity)(?:\*\*:|:)\*\*\s*(\w+)', text)
            risk_match = re.search(r'\*\*(?:Risk Score|risk[_ ]score)(?:\*\*:|:)\*\*\s*(\d+)', text)
            reasoning_match = re.search(r'\*\*(?:Reasoning|reasoning)(?:\*\*:|:)\*\*\s*(.+)', text, re.DOTALL)
            
            if severity_match and risk_match:
                return {
                    "severity": severity_match.group(1),
                    "risk_score": int(risk_match.group(1)),
                    "reasoning": reasoning_match.group(1).strip() if reasoning_match else text
                }
            
            # Last resort: return the full text as reasoning
            return {
                "severity": "Unknown",
                "risk_score": 0,
                "reasoning": f"Could not parse response. Raw output: {text[:500]}"
            }

    except Exception as e:
        return {
            "severity": "Unknown",
            "risk_score": 0,
            "reasoning": f"Agent analysis failed: {str(e)}"
        }

if __name__ == "__main__":
    mcp.run()
