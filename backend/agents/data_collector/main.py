from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Any
import datetime
import os
from dotenv import load_dotenv
from google.cloud import firestore

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# --- FIRESTORE SETUP ---
db = firestore.Client()
EVENTS_COLLECTION = "crisis_events"

# Initialize the MCP server
mcp = FastMCP("Data Collection Agent")

@mcp.tool()
def fetch_disaster_feed(source: str = "GDACS", location: str = None) -> List[Dict[str, Any]]:
    """
    Fetches live disaster data from a specified source.
    This is the primary source for all real-time event data.
    
    Args:
        source: The source of the data. "GDACS" for general disasters, "USGS" for earthquakes, "MOCK" for testing.
        location: Optional. If provided, filters results to events occurring in this location (e.g., "NJ", "California", "China").
        
    Returns:
        A list of normalized event dictionaries, including coordinates.
    """
    
    events = []

    if source == "MOCK":
        events = [
            {
                "event_id": "evt_001",
                "type": "Flood",
                "location": "New Brunswick, NJ",
                "description": "Rising water levels reported near George Street.",
                "timestamp": "2025-11-28T10:00:00Z",
                "coordinates": [-74.4474, 40.4974],
                "source": "MOCK_FEED"
            },
            {
                "event_id": "evt_002",
                "type": "Fire",
                "location": "Piscataway, NJ",
                "description": "Brush fire reported in ecological preserve.",
                "timestamp": "2025-11-28T10:15:00Z",
                "coordinates": [-74.4631, 40.523],
                "source": "MOCK_FEED"
            }
        ]
    
    elif source == "USGS":
        # USGS Earthquake feed (past 30 days, magnitude 2.5+)
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [])
                
                # Extract location from place string (e.g., "10 km E of San Francisco, CA")
                place = props.get("place", "Unknown location")
                
                events.append({
                    "event_id": feature.get("id"),
                    "type": "Earthquake",
                    "location": place,
                    "description": f"M {props.get('mag', 'Unknown')} - {place}",
                    "timestamp": datetime.datetime.fromtimestamp(
                        props.get("time", 0) / 1000
                    ).isoformat() + "Z" if props.get("time") else None,
                    "coordinates": [coords[0], coords[1]] if len(coords) >= 2 else None,  # [longitude, latitude]
                    "magnitude": props.get("mag"),
                    "source": "USGS"
                })
        except Exception as e:
            return [{"error": f"Failed to fetch USGS data: {str(e)}"}]
        
    else:  # Default to GDACS
        # GDACS Events for Application feed (returns a list of current alert events)
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/events4app"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for event in data.get("features", []):
                props = event.get("properties", {})
                geom = event.get("geometry", {})
                
                events.append({
                    "event_id": props.get("eventid"),
                    "type": props.get("eventtype"),
                    "location": props.get("country"),
                    "description": props.get("name"),
                    "timestamp": props.get("fromdate"),
                    "coordinates": geom.get("coordinates"), # [longitude, latitude]
                    "source": "GDACS"
                })
        except Exception as e:
            return [{"error": f"Failed to fetch GDACS data: {str(e)}"}]

    # Filter by location if provided
    if location:
        filtered_events = [
            e for e in events 
            if location.lower() in str(e.get("location", "")).lower()
        ]
        if not filtered_events and events:
            # Only return this message if we successfully fetched data but found no matches
            return [{"message": f"No events found in {location} from source {source}"}]
        
        # If no events were fetched (e.g., API returned empty list) and location is specified, return the empty list.
        if filtered_events:
             return filtered_events

    return events

@mcp.tool()
def fetch_and_persist_events(source: str = "GDACS", location: str = None) -> Dict[str, Any]:
    """
    Fetches disaster data and persists it to Firestore for asynchronous processing.
    This enables decoupled, event-driven architecture for continuous monitoring.
    
    Args:
        source: The source of the data. "GDACS" for real events, "MOCK" for testing.
        location: Optional. If provided, filters results to events occurring in this location.
        
    Returns:
        A summary of the persistence operation with counts of saved events.
    """
    events = fetch_disaster_feed(source=source, location=location)
    
    # Handle error or empty results
    if not events or (len(events) == 1 and ("error" in events[0] or "message" in events[0])):
        return {
            "status": "no_events",
            "message": events[0] if events else "No events fetched",
            "saved_count": 0
        }
    
    saved_ids = []
    errors = []
    
    for event in events:
        try:
            doc_id = save_event_to_firestore(event)
            if doc_id:
                saved_ids.append(doc_id)
            else:
                errors.append(f"Failed to save event {event.get('event_id', 'unknown')}")
        except Exception as e:
            errors.append(f"Error saving event {event.get('event_id', 'unknown')}: {str(e)}")
    
    return {
        "status": "success",
        "saved_count": len(saved_ids),
        "saved_event_ids": saved_ids,
        "errors": errors if errors else None,
        "source": source,
        "location_filter": location
    }

def save_event_to_firestore(event_data: Dict[str, Any]) -> str:
    """Helper function to save an event, using event_id as the document ID."""
    
    # Add status and timestamp for processing workflow
    data_to_save = event_data.copy()
    data_to_save["status"] = "NEW"  # Status for Risk Agent to pick up
    data_to_save["created_at"] = firestore.SERVER_TIMESTAMP
    
    # Use event_id as the document ID for deduplication
    doc_id = data_to_save.get("event_id", None)
    
    try:
        if doc_id:
            # Use string version of doc_id, handle special characters
            doc_id_str = str(doc_id).replace("/", "_").replace("\\", "_")
            doc_ref = db.collection(EVENTS_COLLECTION).document(doc_id_str)
            
            # Use merge=True to avoid overwriting assessed events
            # Check if document exists and is already assessed
            existing_doc = doc_ref.get()
            if existing_doc.exists:
                existing_data = existing_doc.to_dict()
                if existing_data.get("status") == "ASSESSED":
                    # Don't overwrite already assessed events
                    print(f"Skipping event {doc_id} - already assessed")
                    return None
            
            # Save new event or update existing NEW event
            doc_ref.set(data_to_save, merge=True)
            return doc_ref.id
        else:
            # For events without IDs, let Firestore generate an ID
            doc_ref = db.collection(EVENTS_COLLECTION).document()
            doc_ref.set(data_to_save)
            return doc_ref.id
    except Exception as e:
        print(f"Error saving event {doc_id}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run the server using the FastMCP CLI or directly
    mcp.run()