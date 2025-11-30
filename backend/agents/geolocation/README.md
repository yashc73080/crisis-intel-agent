# Geolocation Safety Agent

The Geolocation Safety Agent transforms CrisisNet from a passive intelligence tool to an **active guidance system**. It provides real-time location safety analysis, threat proximity mapping, safe location discovery, and evacuation route planning using Google Maps APIs.

## Features

### 🗺️ Threat Proximity Mapping
- **Tool**: `map_threat_radius`
- Maps all assessed crisis events within a specified radius of user location
- Calculates precise distances using Haversine formula
- Filters by risk score and severity
- Returns sorted list of nearby threats with details

### 🏥 Safe Location Discovery
- **Tool**: `find_safe_locations`
- Finds hospitals, police stations, fire stations, shelters, and other emergency facilities
- Uses Google Places API for real-time data
- Includes ratings, addresses, and distance information
- Respects user-specified search radius

### 🚗 Route Planning & Threat Analysis
- **Tool**: `compute_routes`
- Computes multiple routes between origin and destination
- Analyzes route proximity to known threats
- Provides safety levels: safe, moderate, caution, danger
- Returns distance, duration, and step-by-step directions
- Recommends safest route based on threat analysis

### ✅ Comprehensive Safety Check
- **Tool**: `get_current_location_safety`
- All-in-one location safety assessment
- Combines threat mapping with nearby resource discovery
- Provides actionable recommendations based on threat proximity
- Status levels: safe, monitor, caution, danger

## Architecture

### Data Flow
1. **User Location Input** → [lat, lon]
2. **Firestore Query** → Assessed events with risk scores
3. **Distance Calculation** → Haversine distance to each threat
4. **Google Maps APIs** → Safe locations & routes
5. **Threat Analysis** → Route safety scoring
6. **Recommendations** → Actionable guidance

### Integration with System
```
Data Collector → Risk Assessment → Geolocation Safety → Communication
     ↓                   ↓                    ↓                ↓
  Firestore         Risk Scores      Location Intel    User Alerts
```

## MCP Tools

### `map_threat_radius`
```python
Arguments:
  - user_location: [latitude, longitude]
  - threat_radius_km: Search radius (default: 50km)
  - min_risk_score: Minimum risk to include (default: 50)

Returns:
  {
    "user_location": [lat, lon],
    "threat_count": int,
    "threats": [
      {
        "event_id": str,
        "type": str,
        "distance_km": float,
        "severity": str,
        "risk_score": int
      }
    ],
    "status": "safe" | "threats_detected"
  }
```

### `find_safe_locations`
```python
Arguments:
  - user_location: [latitude, longitude]
  - location_type: "hospital" | "police" | "fire_station" | "shelter"
  - radius_km: Search radius (default: 10km, max: 50km)
  - max_results: Maximum locations to return (default: 10)

Returns:
  {
    "location_type": str,
    "found_count": int,
    "locations": [
      {
        "name": str,
        "address": str,
        "coordinates": [lat, lon],
        "distance_km": float,
        "rating": float,
        "is_open": bool
      }
    ]
  }
```

### `compute_routes`
```python
Arguments:
  - origin: [latitude, longitude]
  - destination: [latitude, longitude]
  - travel_mode: "DRIVE" | "WALK" | "BICYCLE" | "TRANSIT"
  - avoid_threats: bool (default: True)
  - alternatives: bool (default: True)

Returns:
  {
    "route_count": int,
    "routes": [
      {
        "route_index": int,
        "distance_km": float,
        "duration_minutes": float,
        "summary": str,
        "threat_analysis": {
          "safety_level": "safe" | "moderate" | "caution" | "danger",
          "min_threat_distance_km": float,
          "closest_threat_type": str
        }
      }
    ],
    "recommended_route_index": int
  }
```

### `get_current_location_safety`
```python
Arguments:
  - user_location: [latitude, longitude]
  - check_radius_km: Radius for analysis (default: 25km)

Returns:
  {
    "overall_status": "safe" | "monitor" | "caution" | "danger",
    "recommendation": str,
    "threats": {...},
    "nearby_hospitals": [...],
    "nearby_police": [...]
  }
```

## Configuration

### Required Environment Variables
```bash
# Google Maps API Key (required for safe location & route features)
GOOGLE_MAPS_API_KEY=your_api_key_here

# Google Cloud (required for Firestore)
GCP_PROJECT_ID=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Google Cloud APIs to Enable
1. **Maps Places API** - For finding safe locations
2. **Maps Directions API** - For route computation
3. **Firestore API** - For threat data access

### Getting a Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the required APIs listed above
3. Create credentials → API Key
4. Restrict the key to your required APIs for security
5. Add to `.env` file as `GOOGLE_MAPS_API_KEY`

## Usage Examples

### Standalone Testing
```bash
# Start the agent as MCP server
cd backend/agents/geolocation
python main.py

# In another terminal, test with MCP client
# (Use the coordinator for integrated testing)
```

### Integrated with Coordinator
The Geolocation Safety Agent is integrated into both workflows:

**Traditional Workflow (Option 1)**
- After risk assessment, prompts user for location
- Provides comprehensive safety analysis
- Offers evacuation route planning if threats detected

**Decoupled Workflow (Option 2)**
- Optional location safety check after data persistence
- Analyzes threats from Firestore against user location
- Displays nearby emergency resources

## Safety Levels

| Level | Distance from Threat | Recommendation |
|-------|---------------------|----------------|
| **Safe** | >50km | No immediate action needed |
| **Monitor** | 20-50km | Stay alert, monitor updates |
| **Caution** | 5-20km | Prepare evacuation plan |
| **Danger** | <5km | Consider immediate evacuation |

## Technical Details

### Distance Calculation
Uses the **Haversine formula** for great-circle distance:
```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    # ... formula implementation
    return distance_km
```

### Polyline Decoding
Decodes Google Maps encoded polylines to analyze route paths:
- Samples points along route for threat proximity checks
- Reduces computation by sampling every Nth point
- Maintains accuracy while optimizing performance

### Coordinate Handling
Handles both coordinate conventions:
- `[longitude, latitude]` (GeoJSON/GDACS standard)
- `[latitude, longitude]` (Google Maps standard)
- Auto-detects based on value ranges

## Integration Points

### Firestore Schema
Queries `crisis_events` collection:
```javascript
{
  event_id: string,
  type: string,
  location: string,
  coordinates: [lon, lat],
  status: "ASSESSED",
  risk_assessment: {
    severity: string,
    risk_score: number,
    reasoning: string
  }
}
```

### Coordinator Workflow
1. User provides location as `lat,lon`
2. Agent queries Firestore for threats
3. Calls Google Maps APIs for resources
4. Computes and ranks routes
5. Returns comprehensive safety report

## Future Enhancements

### Planned Features
- [ ] Real-time traffic integration
- [ ] Weather overlay on routes
- [ ] Multi-destination optimization
- [ ] Shelter capacity data
- [ ] Push notifications for changing threat levels
- [ ] Historical route safety trends

### API Additions
- [ ] Google Maps Roads API - Road-specific data
- [ ] Geocoding API - Address to coordinates
- [ ] Distance Matrix API - Bulk distance calculations
- [ ] Elevation API - Terrain analysis for flooding

## Dependencies

```
google-cloud-firestore  # Threat data access
requests                # HTTP client for Google Maps APIs
mcp                     # Model Context Protocol
google-adk              # Agent Development Kit
google-genai            # Gemini integration
```

## License

Part of the CrisisNet Multi-Agent System.
