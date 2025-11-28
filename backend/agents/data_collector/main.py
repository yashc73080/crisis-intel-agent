from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Any

# Initialize the MCP server
mcp = FastMCP("Data Collection Agent")

@mcp.tool()
def fetch_disaster_feed(source: str = "GDACS") -> List[Dict[str, Any]]:
    """
    Fetches live disaster data from a specified source.
    
    Args:
        source: The source of the data (e.g., "GDACS", "USGS", "MOCK").
        
    Returns:
        A list of normalized event dictionaries.
    """
    # In a real implementation, this would call external APIs.
    # For now, we return mock data to establish the pipeline.
    
    if source == "MOCK":
        return [
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
    
    # Placeholder for real API calls
    return [{"error": f"Source {source} not yet implemented"}]

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
