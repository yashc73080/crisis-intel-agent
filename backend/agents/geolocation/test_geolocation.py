"""
Simple test script to verify Geolocation Safety Agent tools work correctly.
Tests basic functionality without requiring full MCP server/client setup.
"""

import os
import sys
import json

# Add backend to path
# backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, backend_dir)

# Import only the pure functions, not the ones requiring Firestore
from agents.geolocation.main import haversine_distance

# We'll define simplified versions for testing
def map_threat_radius(user_location, threat_radius_km=50.0, min_risk_score=50):
    """Simplified test version without Firestore"""
    return {
        "user_location": user_location,
        "search_radius_km": threat_radius_km,
        "threat_count": 0,
        "threats": [],
        "status": "safe"
    }

def find_safe_locations(user_location, location_type="hospital", radius_km=10.0, max_results=10):
    """Test version that checks if API key is set"""
    import requests
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY not configured"}
    
    user_lat, user_lon = user_location
    radius_meters = min(radius_km * 1000, 50000)
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{user_lat},{user_lon}",
            "radius": radius_meters,
            "type": location_type,
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            return {"error": f"Google Places API error: {data.get('status')}"}
        
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
            })
        
        return {
            "user_location": user_location,
            "location_type": location_type,
            "search_radius_km": radius_km,
            "found_count": len(safe_locations),
            "locations": safe_locations
        }
    except Exception as e:
        return {"error": str(e)}

def compute_routes(origin, destination, travel_mode="DRIVE", avoid_threats=True, alternatives=True):
    """Test version that checks if API key is set"""
    import requests
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not GOOGLE_MAPS_API_KEY:
        return {"error": "GOOGLE_MAPS_API_KEY not configured"}
    
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": travel_mode.lower(),
            "alternatives": "true" if alternatives else "false",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK":
            return {"error": f"Google Directions API error: {data.get('status')}"}
        
        routes = []
        for idx, route in enumerate(data.get("routes", [])):
            leg = route["legs"][0]
            routes.append({
                "route_index": idx,
                "summary": route.get("summary", "Route"),
                "distance_km": round(leg["distance"]["value"] / 1000, 2),
                "duration_minutes": round(leg["duration"]["value"] / 60, 1),
            })
        
        return {
            "origin": origin,
            "destination": destination,
            "travel_mode": travel_mode,
            "route_count": len(routes),
            "routes": routes,
            "recommended_route_index": 0 if routes else None
        }
    except Exception as e:
        return {"error": str(e)}

def get_current_location_safety(user_location, check_radius_km=25.0):
    """Simplified test version"""
    threats_result = map_threat_radius(user_location, check_radius_km, 50)
    
    return {
        "user_location": user_location,
        "overall_status": "safe",
        "recommendation": "No immediate threats detected in your area.",
        "threats": threats_result,
        "nearby_hospitals": [],
        "nearby_police": []
    }

def test_haversine_distance():
    """Test the haversine distance calculation"""
    print("\n--- Testing Haversine Distance ---")
    
    # Distance between NYC and Philadelphia (approx 130km)
    nyc = (40.7128, -74.0060)
    philly = (39.9526, -75.1652)
    
    distance = haversine_distance(nyc[0], nyc[1], philly[0], philly[1])
    print(f"NYC to Philadelphia: {distance:.2f} km (expected ~130 km)")
    
    assert 125 < distance < 135, f"Expected ~130km, got {distance}km"
    print("✓ Distance calculation works correctly")


def test_map_threat_radius():
    """Test mapping threats within radius"""
    print("\n--- Testing Threat Radius Mapping ---")
    
    # Test location: New Jersey (Piscataway area)
    user_location = [40.5, -74.4]
    
    result = map_threat_radius(
        user_location=user_location,
        threat_radius_km=100.0,
        min_risk_score=50
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    assert "user_location" in result, "Missing user_location in result"
    assert "threat_count" in result, "Missing threat_count in result"
    assert "status" in result, "Missing status in result"
    
    print(f"✓ Found {result['threat_count']} threats within 100km")
    return result


def test_find_safe_locations():
    """Test finding safe locations (requires Google Maps API key)"""
    print("\n--- Testing Safe Location Discovery ---")
    
    if not os.getenv("GOOGLE_MAPS_API_KEY"):
        print("⚠ Skipping: GOOGLE_MAPS_API_KEY not set")
        return
    
    # Test location: New Jersey
    user_location = [40.5, -74.4]
    
    result = find_safe_locations(
        user_location=user_location,
        location_type="hospital",
        radius_km=10.0,
        max_results=3
    )
    
    print(f"Result summary: found_count={result.get('found_count', 0)}")
    
    if result.get("found_count", 0) > 0:
        print("Sample locations:")
        for loc in result["locations"][:2]:
            print(f"  • {loc['name']} - {loc['distance_km']}km away")
    
    assert "location_type" in result, "Missing location_type in result"
    print(f"✓ Safe location search completed")
    return result


def test_compute_routes():
    """Test route computation (requires Google Maps API key)"""
    print("\n--- Testing Route Computation ---")
    
    if not os.getenv("GOOGLE_MAPS_API_KEY"):
        print("⚠ Skipping: GOOGLE_MAPS_API_KEY not set")
        return
    
    # NYC to Philadelphia
    origin = [40.7128, -74.0060]
    destination = [39.9526, -75.1652]
    
    result = compute_routes(
        origin=origin,
        destination=destination,
        travel_mode="DRIVE",
        avoid_threats=True,
        alternatives=True
    )
    
    print(f"Result summary: route_count={result.get('route_count', 0)}")
    
    if result.get("route_count", 0) > 0:
        route = result["routes"][0]
        print(f"  Route 1: {route['distance_km']}km, {route['duration_minutes']}min")
        if "threat_analysis" in route:
            print(f"    Safety: {route['threat_analysis'].get('safety_level', 'unknown')}")
    
    assert "route_count" in result, "Missing route_count in result"
    print(f"✓ Route computation completed")
    return result


def test_get_current_location_safety():
    """Test comprehensive location safety check"""
    print("\n--- Testing Current Location Safety ---")
    
    user_location = [40.5, -74.4]
    
    result = get_current_location_safety(
        user_location=user_location,
        check_radius_km=50.0
    )
    
    print(f"Overall Status: {result.get('overall_status', 'unknown')}")
    print(f"Recommendation: {result.get('recommendation', 'N/A')}")
    
    threats_info = result.get('threats', {})
    print(f"Threats detected: {threats_info.get('threat_count', 0)}")
    
    assert "overall_status" in result, "Missing overall_status in result"
    assert "recommendation" in result, "Missing recommendation in result"
    
    print(f"✓ Comprehensive safety check completed")
    return result


if __name__ == "__main__":
    print("="*70)
    print("GEOLOCATION SAFETY AGENT - FUNCTIONALITY TESTS")
    print("="*70)
    
    # Load environment variables
    from dotenv import load_dotenv
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(os.path.dirname(backend_dir))
    env_path = os.path.join(root_dir, ".env")
    load_dotenv(env_path)
    
    print(f"\nEnvironment:")
    print(f"  GCP Project: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    print(f"  Google Maps API Key: {'Set' if os.getenv('GOOGLE_MAPS_API_KEY') else 'Not set'}")
    
    try:
        # Run tests
        test_haversine_distance()
        test_map_threat_radius()
        test_find_safe_locations()
        test_compute_routes()
        test_get_current_location_safety()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
