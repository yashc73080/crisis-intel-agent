import sys
import os
import json
import math
import datetime
from typing import Dict, Any, List, Optional, Tuple
from mcp.server.fastmcp import FastMCP
from google.cloud import firestore
from dotenv import load_dotenv
import requests

# Imports from ADK
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

# Load .env
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# Initialize Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Ensure these are set in os.environ
if PROJECT_ID:
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
if LOCATION:
    os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
if PROJECT_ID:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

# Initialize Firestore client
db = firestore.Client()
EVENTS_COLLECTION = "crisis_events"

mcp = FastMCP("Geolocation Safety Agent")

# Retry configuration
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Define the Geolocation Analysis Agent
geolocation_agent = LlmAgent(
    name="geolocation_analysis_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Analyzes location safety and provides guidance based on threat proximity.",
    instruction="""
    You are a geolocation safety expert. Your goal is to help users understand their safety 
    relative to crisis events and provide actionable guidance.
    
    Analyze threat proximity, route safety, and recommend actions based on:
    - Distance from threats
    - Severity of events
    - Available safe locations
    - Route characteristics
    
    Provide clear, concise, actionable safety recommendations.
    """,
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points on the earth.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Radius of the Earth in kilometers
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    try:
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        # Clamp a to [0, 1] to avoid domain errors due to floating point precision
        a = max(0.0, min(1.0, a))
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    except ValueError:
        # Fallback for extreme edge cases
        return 0.0


@mcp.tool()
def map_threat_radius(
    user_location: List[float],
    threat_radius_km: float = 50.0,
    min_risk_score: int = 50
) -> Dict[str, Any]:
    """
    Maps all threats within a specified radius of the user's location.
    Queries Firestore for assessed events and filters by distance and risk.
    
    Args:
        user_location: [latitude, longitude] of the user
        threat_radius_km: Radius in kilometers to check for threats (default: 50km)
        min_risk_score: Minimum risk score to consider (0-100, default: 50)
        
    Returns:
        Dictionary containing nearby threats with distances and risk info.
    """
    if not user_location or len(user_location) != 2:
        return {"error": "Invalid user_location. Must be [latitude, longitude]"}
    
    user_lat, user_lon = user_location
    
    try:
        # Query Firestore for assessed events
        query = db.collection(EVENTS_COLLECTION).where("status", "==", "ASSESSED").limit(100)
        docs = query.stream()
        
        nearby_threats = []
        
        for doc in docs:
            event_data = doc.to_dict()
            
            # Check risk score
            risk_score = event_data.get("risk_assessment", {}).get("risk_score", 0)
            if risk_score < min_risk_score:
                continue
            
            # Get event coordinates
            coords = event_data.get("coordinates")
            if not coords or len(coords) != 2:
                continue
            
            # Note: Some APIs use [lon, lat], others use [lat, lon]
            # GDACS typically uses [lon, lat], so we'll handle both
            event_lon, event_lat = coords[0], coords[1]
            
            # Check if this looks like [lat, lon] instead (lat is typically -90 to 90)
            if abs(coords[0]) <= 90 and abs(coords[1]) > 90:
                event_lat, event_lon = coords[0], coords[1]
            
            # Calculate distance
            distance_km = haversine_distance(user_lat, user_lon, event_lat, event_lon)
            
            # Check if within radius
            if distance_km <= threat_radius_km:
                nearby_threats.append({
                    "event_id": event_data.get("event_id"),
                    "type": event_data.get("type"),
                    "location": event_data.get("location"),
                    "coordinates": [event_lat, event_lon],
                    "distance_km": round(distance_km, 2),
                    "severity": event_data.get("risk_assessment", {}).get("severity"),
                    "risk_score": risk_score,
                    "description": event_data.get("description", "")[:200]  # Truncate for brevity
                })
        
        # Sort by distance
        nearby_threats.sort(key=lambda x: x["distance_km"])
        
        return {
            "user_location": user_location,
            "search_radius_km": threat_radius_km,
            "threat_count": len(nearby_threats),
            "threats": nearby_threats,
            "status": "safe" if len(nearby_threats) == 0 else "threats_detected"
        }
        
    except Exception as e:
        return {"error": f"Failed to map threat radius: {str(e)}"}


@mcp.tool()
def find_safe_locations(
    user_location: List[float],
    location_type: str = "hospital",
    radius_km: float = 10.0,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Finds safe locations (shelters, hospitals, police stations) near the user using Google Places API.
    
    Args:
        user_location: [latitude, longitude] of the user
        location_type: Type of place to search for. Options: 'hospital', 'police', 'fire_station', 
                      'shelter' (note: shelter searches for 'emergency_shelter' or 'community_center')
        radius_km: Search radius in kilometers (default: 10km, max: 50km)
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        Dictionary containing safe locations with distances, addresses, and ratings.
    """
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY not configured. Please set it in .env file."}
    
    if not user_location or len(user_location) != 2:
        return {"error": "Invalid user_location. Must be [latitude, longitude]"}
    
    user_lat, user_lon = user_location
    
    # Map location types to Google Places types
    type_mapping = {
        "hospital": "hospital",
        "police": "police",
        "fire_station": "fire_station",
        "shelter": "community_center",  # Closest approximation
        "pharmacy": "pharmacy",
        "gas_station": "gas_station"
    }
    
    place_type = type_mapping.get(location_type.lower(), location_type)
    
    # Convert km to meters (Places API uses meters)
    radius_meters = min(radius_km * 1000, 50000)  # Cap at 50km
    
    try:
        # Google Places API Nearby Search
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{user_lat},{user_lon}",
            "radius": radius_meters,
            "type": place_type,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            return {"error": f"Google Places API error: {data.get('status')} - {data.get('error_message', '')}"}
        
        safe_locations = []
        
        for place in data.get("results", [])[:max_results]:
            place_lat = place["geometry"]["location"]["lat"]
            place_lon = place["geometry"]["location"]["lng"]
            
            distance_km = haversine_distance(user_lat, user_lon, place_lat, place_lon)
            
            safe_locations.append({
                "name": place.get("name"),
                "address": place.get("vicinity", "Address not available"),
                "coordinates": [place_lat, place_lon],
                "distance_km": round(distance_km, 2),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
                "place_id": place.get("place_id"),
                "types": place.get("types", []),
                "is_open": place.get("opening_hours", {}).get("open_now")
            })
        
        # Sort by distance
        safe_locations.sort(key=lambda x: x["distance_km"])
        
        return {
            "user_location": user_location,
            "location_type": location_type,
            "search_radius_km": radius_km,
            "found_count": len(safe_locations),
            "locations": safe_locations
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to query Google Places API: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to find safe locations: {str(e)}"}


@mcp.tool()
def compute_routes(
    origin: List[float],
    destination: List[float],
    travel_mode: str = "DRIVE",
    avoid_threats: bool = True,
    alternatives: bool = True
) -> Dict[str, Any]:
    """
    Computes routes from origin to destination using Google Routes API (v2).
    Optionally considers threat zones to suggest safer routes.
    
    Args:
        origin: [latitude, longitude] of starting point
        destination: [latitude, longitude] of destination
        travel_mode: Travel mode - 'DRIVE', 'WALK', 'BICYCLE', 'TRANSIT' (default: 'DRIVE')
        avoid_threats: If True, analyzes route proximity to known threats (default: True)
        alternatives: Request alternative routes (default: True)
        
    Returns:
        Dictionary containing route details including distance, duration, and threat analysis.
    """
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY not configured. Please set it in .env file."}
    
    if not origin or len(origin) != 2 or not destination or len(destination) != 2:
        return {"error": "Invalid origin or destination. Must be [latitude, longitude]"}
    
    origin_lat, origin_lon = origin
    dest_lat, dest_lon = destination
    
    try:
        # Use Google Directions API (simpler than Routes API v2 for basic routing)
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin_lat},{origin_lon}",
            "destination": f"{dest_lat},{dest_lon}",
            "mode": travel_mode.lower(),
            "alternatives": "true" if alternatives else "false",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK":
            return {"error": f"Google Directions API error: {data.get('status')} - {data.get('error_message', '')}"}
        
        routes = []
        
        for idx, route in enumerate(data.get("routes", [])):
            leg = route["legs"][0]  # First leg (we're doing single-leg routes)
            
            route_info = {
                "route_index": idx,
                "summary": route.get("summary", "Route"),
                "distance_km": round(leg["distance"]["value"] / 1000, 2),
                "distance_text": leg["distance"]["text"],
                "duration_minutes": round(leg["duration"]["value"] / 60, 1),
                "duration_text": leg["duration"]["text"],
                "start_address": leg["start_address"],
                "end_address": leg["end_address"],
                "steps_count": len(leg["steps"]),
                "polyline": route["overview_polyline"]["points"]
            }
            
            # If avoid_threats is enabled, analyze route proximity to threats
            if avoid_threats:
                threat_analysis = analyze_route_threats(route["overview_polyline"]["points"])
                route_info["threat_analysis"] = threat_analysis
            
            routes.append(route_info)
        
        # Sort routes: safest first (if threat analysis), then by duration
        if avoid_threats and routes:
            routes.sort(key=lambda r: (
                r.get("threat_analysis", {}).get("max_threat_proximity_km", 999),
                r["duration_minutes"]
            ))
        
        return {
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "route_count": len(routes),
            "routes": routes,
            "recommended_route_index": 0 if routes else None
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to query Google Directions API: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to compute routes: {str(e)}"}


def analyze_route_threats(encoded_polyline: str) -> Dict[str, Any]:
    """
    Analyzes a route (encoded polyline) for proximity to known threats.
    Samples points along the route and checks distance to threats in Firestore.
    
    Args:
        encoded_polyline: Google Maps encoded polyline string
        
    Returns:
        Dictionary with threat analysis results
    """
    try:
        # Decode polyline to get route coordinates
        route_points = decode_polyline(encoded_polyline)
        
        if not route_points:
            return {"error": "Failed to decode route polyline"}
        
        # Sample every 10th point to reduce computation (or all if < 50 points)
        sample_interval = max(1, len(route_points) // 50)
        sampled_points = route_points[::sample_interval]
        
        # Query threats from Firestore
        query = db.collection(EVENTS_COLLECTION).where("status", "==", "ASSESSED").where(
            "risk_assessment.risk_score", ">=", 50
        ).limit(50)
        
        docs = query.stream()
        threats = []
        
        for doc in docs:
            event_data = doc.to_dict()
            coords = event_data.get("coordinates")
            if coords and len(coords) == 2:
                # Handle coordinate order
                event_lon, event_lat = coords[0], coords[1]
                if abs(coords[0]) <= 90 and abs(coords[1]) > 90:
                    event_lat, event_lon = coords[0], coords[1]
                
                threats.append({
                    "lat": event_lat,
                    "lon": event_lon,
                    "type": event_data.get("type"),
                    "risk_score": event_data.get("risk_assessment", {}).get("risk_score", 0)
                })
        
        # Calculate minimum distance from route to each threat
        min_threat_distance = float('inf')
        closest_threat = None
        threat_proximities = []
        
        for threat in threats:
            min_dist = min(
                haversine_distance(point[0], point[1], threat["lat"], threat["lon"])
                for point in sampled_points
            )
            
            threat_proximities.append({
                "threat_type": threat["type"],
                "distance_km": round(min_dist, 2),
                "risk_score": threat["risk_score"]
            })
            
            if min_dist < min_threat_distance:
                min_threat_distance = min_dist
                closest_threat = threat["type"]
        
        # Sort by distance
        threat_proximities.sort(key=lambda x: x["distance_km"])
        
        # Determine safety level
        if min_threat_distance > 50:
            safety_level = "safe"
        elif min_threat_distance > 20:
            safety_level = "moderate"
        elif min_threat_distance > 5:
            safety_level = "caution"
        else:
            safety_level = "danger"
        
        return {
            "safety_level": safety_level,
            "closest_threat_type": closest_threat,
            "min_threat_distance_km": round(min_threat_distance, 2) if min_threat_distance != float('inf') else None,
            "threats_analyzed": len(threats),
            "threat_proximities": threat_proximities[:5]  # Top 5 closest
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze route threats: {str(e)}"}


def decode_polyline(encoded: str) -> List[Tuple[float, float]]:
    """
    Decodes a Google Maps encoded polyline string into a list of (lat, lon) tuples.
    
    Args:
        encoded: Encoded polyline string
        
    Returns:
        List of (latitude, longitude) tuples
    """
    points = []
    index = 0
    lat = 0
    lng = 0
    
    while index < len(encoded):
        # Decode latitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat
        
        # Decode longitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng
        
        points.append((lat / 1e5, lng / 1e5))
    
    return points


@mcp.tool()
def get_current_location_safety(
    user_location: List[float],
    check_radius_km: float = 25.0
) -> Dict[str, Any]:
    """
    Comprehensive safety check for a user's current location.
    Combines threat mapping and nearby safe location finding.
    
    Args:
        user_location: [latitude, longitude] of the user
        check_radius_km: Radius to check for threats and resources (default: 25km)
        
    Returns:
        Dictionary with comprehensive safety assessment and recommendations.
    """
    if not user_location or len(user_location) != 2:
        return {"error": "Invalid user_location. Must be [latitude, longitude]"}
    
    # Get nearby threats
    threats_result = map_threat_radius(
        user_location=user_location,
        threat_radius_km=check_radius_km,
        min_risk_score=50
    )
    
    # Get nearby hospitals
    hospitals_result = find_safe_locations(
        user_location=user_location,
        location_type="hospital",
        radius_km=check_radius_km,
        max_results=3
    )
    
    # Get nearby police stations
    police_result = find_safe_locations(
        user_location=user_location,
        location_type="police",
        radius_km=check_radius_km,
        max_results=3
    )
    
    # Determine overall safety status
    threat_count = threats_result.get("threat_count", 0)
    closest_threat_distance = None
    
    if threat_count > 0:
        threats = threats_result.get("threats", [])
        if threats:
            closest_threat_distance = threats[0]["distance_km"]
    
    if threat_count == 0:
        overall_status = "safe"
        recommendation = "No immediate threats detected in your area."
    elif closest_threat_distance and closest_threat_distance > 20:
        overall_status = "monitor"
        recommendation = f"Threats detected {closest_threat_distance}km away. Stay alert and monitor the situation."
    elif closest_threat_distance and closest_threat_distance > 5:
        overall_status = "caution"
        recommendation = f"Threats within {closest_threat_distance}km. Prepare evacuation plan and stay informed."
    else:
        overall_status = "danger"
        recommendation = "Immediate threats detected nearby. Consider evacuation if safe to do so."
    
    return {
        "user_location": user_location,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "overall_status": overall_status,
        "recommendation": recommendation,
        "threats": threats_result,
        "nearby_hospitals": hospitals_result.get("locations", [])[:3],
        "nearby_police": police_result.get("locations", [])[:3]
    }


if __name__ == "__main__":
    mcp.run()
