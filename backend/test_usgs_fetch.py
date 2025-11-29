"""
Test script to verify USGS earthquake fetching works
"""
import requests
import datetime
import json

def test_usgs_fetch():
    """Test fetching from USGS API"""
    print("Testing USGS Earthquake Feed...")
    print("=" * 60)
    
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [])
            
            place = props.get("place", "Unknown location")
            
            events.append({
                "event_id": feature.get("id"),
                "type": "Earthquake",
                "location": place,
                "description": f"M {props.get('mag', 'Unknown')} - {place}",
                "timestamp": datetime.datetime.fromtimestamp(
                    props.get("time", 0) / 1000
                ).isoformat() + "Z" if props.get("time") else None,
                "coordinates": [coords[0], coords[1]] if len(coords) >= 2 else None,
                "magnitude": props.get("mag"),
                "source": "USGS"
            })
        
        print(f"✓ Successfully fetched {len(events)} earthquakes")
        
        # Test location filter
        china_events = [e for e in events if "china" in e.get("location", "").lower()]
        print(f"✓ Found {len(china_events)} earthquakes in China")
        
        if china_events:
            print("\nSample China Earthquake:")
            print(json.dumps(china_events[0], indent=2))
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_usgs_fetch()
