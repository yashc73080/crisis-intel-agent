from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Any
import datetime

# Initialize the MCP server
mcp = FastMCP("Data Collection Agent")

@mcp.tool()
def fetch_disaster_feed(source: str = "GDACS", location: str = None) -> List[Dict[str, Any]]:
    """
    Fetches live disaster data from a specified source.
    This is the primary source for all real-time event data.
    
    Args:
        source: The source of the data. "GDACS" for real events, "MOCK" for testing.
        location: Optional. If provided, filters results to events occurring in this location (e.g., "NJ", "California", "Malaysia").
        
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
        
    else: # Default to GDACS
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

if __name__ == "__main__":
    # Run the server using the FastMCP CLI or directly
    mcp.run()