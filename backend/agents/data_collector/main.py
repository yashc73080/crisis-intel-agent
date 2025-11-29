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
    
    Args:
        source: The source of the data. Options:
                - "GDACS": General international disasters (floods, cyclones).
                - "USGS": Earthquakes only.
                - "MOCK": Test data.
        location: Optional. If provided, filters results to events occurring in this location (e.g., "NJ", "California").
        
    Returns:
        A list of normalized event dictionaries.
    """
    
    events = []

    if source == "USGS":
        # USGS Earthquake Feed (Past Hour, All Earthquakes)
        # Note: Unix timestamp (ms) is returned and should ideally be converted to ISO 8601 string.
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                
                # Convert Unix timestamp (ms) to ISO 8601 string for consistency
                time_ms = props.get("time")
                timestamp_iso = datetime.datetime.fromtimestamp(time_ms / 1000.0, datetime.timezone.utc).isoformat().replace("+00:00", "Z") if time_ms else None
                
                events.append({
                    "event_id": feature.get("id"),
                    "type": "Earthquake",
                    "location": props.get("place", ""),
                    "description": props.get("title"),
                    "timestamp": timestamp_iso, 
                    "source": "USGS"
                })
        except Exception as e:
            return [{"error": f"Failed to fetch USGS data: {str(e)}"}]

    elif source == "GDACS":
        # GDACS Events for Application feed (returns a list of current alert events)
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/events4app"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for event in data.get("features", []):
                props = event.get("properties", {})
                events.append({
                    "event_id": event.get("id"),
                    "type": props.get("eventtype"),
                    "location": props.get("country"),
                    "description": props.get("name"),
                    "timestamp": props.get("fromdate"),
                    "source": "GDACS"
                })
        except Exception as e:
            return [{"error": f"Failed to fetch GDACS data: {str(e)}"}]
        
    elif source == "MOCK":
        events = [
            {
                "event_id": "evt_001",
                "type": "Flood",
                "location": "New Brunswick, NJ",
                "description": "Rising water levels reported near George Street.",
                "timestamp": "2025-11-28T10:00:00Z",
                "source": "MOCK_FEED"
            },
            {
                "event_id": "evt_002",
                "type": "Fire",
                "location": "Piscataway, NJ",
                "description": "Brush fire reported in ecological preserve.",
                "timestamp": "2025-11-28T10:15:00Z",
                "source": "MOCK_FEED"
            }
        ]
    
    else:
        return [{"error": f"Source {source} not yet implemented"}]

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
def fetch_weather(location: str) -> Dict[str, Any]:
    """
    Fetches current weather for a specific location.
    """
    return {
        "location": location,
        "condition": "Rainy",
        "temperature": 15,
        "wind_speed": 25,
        "unit": "C"
    }

if __name__ == "__main__":
    # Run the server using the FastMCP CLI or directly
    mcp.run()