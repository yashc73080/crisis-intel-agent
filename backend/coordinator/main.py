import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define paths to agents
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.join(os.path.dirname(current_dir), "agents")

async def run_workflow():
    """Run the traditional synchronous workflow (for demonstration/testing)"""
    # Define server parameters for Data Collector
    data_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "data_collector", "main.py")],
        env=os.environ.copy()
    )
    
    # Define server parameters for Risk Assessment
    risk_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "risk_assessment", "main.py")],
        env=os.environ.copy()
    )

    # Define server parameters for Geolocation Safety Agent
    geo_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "geolocation", "main.py")],
        env=os.environ.copy()
    )

    # Define server parameters for Communication Agent
    comm_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "communication", "main.py")],
        env=os.environ.copy()
    )

    # Connect to Communication Agent
    async with stdio_client(comm_server_params) as (comm_read, comm_write):
        async with ClientSession(comm_read, comm_write) as comm_session:
            await comm_session.initialize()

            # Connect to Data Collector
            async with stdio_client(data_server_params) as (data_read, data_write):
                async with ClientSession(data_read, data_write) as data_session:
                    await data_session.initialize()
                    
                    # Connect to Risk Assessment
                    async with stdio_client(risk_server_params) as (risk_read, risk_write):
                        async with ClientSession(risk_read, risk_write) as risk_session:
                            await risk_session.initialize()

                            # Connect to Geolocation Safety Agent
                            async with stdio_client(geo_server_params) as (geo_read, geo_write):
                                async with ClientSession(geo_read, geo_write) as geo_session:
                                    await geo_session.initialize()

                                    print("\n--- Step 1: Fetching Data ---")
                                    
                                    # Prompt user for natural language input
                                    print("Please describe the situation.")
                                    print("Example: 'I think there is an earthquake in NJ' or 'Check for floods near Piscataway'")
                                    user_input = input("Your Input: ").strip()
                                    
                                    # Call Communication Agent to parse intent
                                    print("Analyzing intent...")
                                    intent_result = await comm_session.call_tool("parse_user_intent", arguments={"user_input": user_input})
                                    
                                    # Parse the JSON string returned by the tool
                                    try:
                                        intent_data = json.loads(intent_result.content[0].text)
                                        source = intent_data.get("source", "GDACS")
                                        location = intent_data.get("location")
                                        print(f"Agent Interpretation -> Source: {source}, Location: {location}")
                                    except json.JSONDecodeError:
                                        print("Error: Failed to parse intent from Communication Agent.")
                                        return

                                    # Call the data fetch tool
                                    result = await data_session.call_tool("fetch_disaster_feed", arguments={"source": source, "location": location})
                                    
                                    # Parse the JSON string returned by the tool
                                    raw_data = result.content[0].text
                                    print(f"Events received: {raw_data}")
                                    
                                    try:
                                        events = json.loads(raw_data)
                                    except json.JSONDecodeError:
                                        print("Error: Returned data is not valid JSON")
                                        return

                                    # Ensure we have a list to iterate over
                                    if isinstance(events, dict):
                                        events = [events]

                                    print("\n--- Step 2: Assessing Risk ---")
                                    for event in events:
                                        # Safely get event details
                                        event_type = event.get("type", "Unknown")
                                        description = event.get("description", "")
                                        location = event.get("location", "")
                                        coordinates = event.get("coordinates", None)
                                        
                                        print(f"Analyzing event: {event_type}")
                                        
                                        # Retry logic for risk assessment (max 3 attempts)
                                        max_retries = 3
                                        risk_data = None
                                        
                                        for attempt in range(1, max_retries + 1):
                                            try:
                                                # Call the risk classification tool
                                                risk_result = await risk_session.call_tool(
                                                    "classify_event",
                                                    arguments={
                                                        "event_description": description,
                                                        "event_type": event_type,
                                                        "location": location,
                                                        "coordinates": coordinates
                                                    }
                                                )
                                                
                                                # Parse and check result
                                                risk_data = json.loads(risk_result.content[0].text)
                                                
                                                # Check if we got a valid response
                                                if risk_data.get("risk_score", 0) == 0 and risk_data.get("severity") == "Unknown":
                                                    if attempt < max_retries:
                                                        print(f"  ↻ Retry {attempt}/{max_retries} - Got empty response, retrying...")
                                                        await asyncio.sleep(2)
                                                        continue
                                                    else:
                                                        print(f"  ⚠ All retries exhausted, got empty response")
                                                
                                                # Success - break out of retry loop
                                                break
                                                
                                            except json.JSONDecodeError:
                                                if attempt < max_retries:
                                                    print(f"  ↻ Retry {attempt}/{max_retries} - Parse error, retrying...")
                                                    await asyncio.sleep(2)
                                                    continue
                                                else:
                                                    risk_data = {
                                                        "severity": "Unknown",
                                                        "risk_score": 0,
                                                        "reasoning": "Failed to parse response after retries"
                                                    }
                                            except Exception as e:
                                                if attempt < max_retries:
                                                    print(f"  ↻ Retry {attempt}/{max_retries} - Error: {str(e)}, retrying...")
                                                    await asyncio.sleep(2)
                                                    continue
                                                else:
                                                    risk_data = {
                                                        "severity": "Unknown",
                                                        "risk_score": 0,
                                                        "reasoning": f"Error: {str(e)}"
                                                    }
                                        
                                        # Display result
                                        if risk_data:
                                            print(f"Risk Analysis: {json.dumps(risk_data, indent=2)}")
                                        else:
                                            print(f"Risk Analysis: Failed to get assessment")

                                    print("\n--- Step 3: User Location Safety Analysis ---")
                                    print("Would you like to check your location safety? (y/n)")
                                    check_safety = input().strip().lower()
                                    
                                    if check_safety == 'y':
                                        print("Enter your location as latitude,longitude (e.g., 40.5,-74.4):")
                                        user_loc_input = input().strip()
                                        
                                        try:
                                            lat_str, lon_str = user_loc_input.split(',')
                                            lat = float(lat_str.strip())
                                            lon = float(lon_str.strip())
                                            
                                            # Validate coordinates
                                            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                                                print(f"\n⚠ Invalid coordinates: Latitude must be between -90 and 90, Longitude between -180 and 180.")
                                                print(f"You entered: {lat}, {lon}")
                                                return

                                            user_location = [lat, lon]
                                            
                                            # Get comprehensive safety check
                                            print("\nAnalyzing your location safety...")
                                            safety_result = await geo_session.call_tool(
                                                "get_current_location_safety",
                                                arguments={
                                                    "user_location": user_location,
                                                    "check_radius_km": 30.0
                                                }
                                            )
                                            
                                            try:
                                                safety_data = json.loads(safety_result.content[0].text)
                                            except json.JSONDecodeError:
                                                print(f"\n⚠ Error: Received invalid JSON from Geolocation Agent.")
                                                print(f"Raw response: {safety_result.content[0].text if safety_result.content else 'Empty response'}")
                                                return
                                            
                                            print(f"\n{'='*60}")
                                            print(f"LOCATION SAFETY REPORT")
                                            print(f"{'='*60}")
                                            print(f"Status: {safety_data.get('overall_status', 'Unknown').upper()}")
                                            print(f"Recommendation: {safety_data.get('recommendation')}")
                                            
                                            threats_info = safety_data.get('threats', {})
                                            if threats_info.get('threat_count', 0) > 0:
                                                print(f"\n⚠ Threats Detected: {threats_info['threat_count']}")
                                                for threat in threats_info.get('threats', [])[:3]:
                                                    print(f"  • {threat['type']} - {threat['distance_km']}km away (Risk: {threat['risk_score']})")
                                            
                                            hospitals = safety_data.get('nearby_hospitals', [])
                                            if hospitals:
                                                print(f"\n🏥 Nearest Hospitals:")
                                                for h in hospitals[:2]:
                                                    print(f"  • {h['name']} - {h['distance_km']}km away")
                                            
                                            police = safety_data.get('nearby_police', [])
                                            if police:
                                                print(f"\n👮 Nearest Police Stations:")
                                                for p in police[:2]:
                                                    print(f"  • {p['name']} - {p['distance_km']}km away")
                                            
                                            print(f"\n{'='*60}")
                                            
                                            # Offer route planning for evacuation
                                            if threats_info.get('threat_count', 0) > 0 and safety_data.get('overall_status') in ['caution', 'danger']:
                                                print("\nWould you like to plan an evacuation route to a safe location? (y/n)")
                                                plan_route = input().strip().lower()
                                                
                                                if plan_route == 'y' and hospitals:
                                                    nearest_hospital = hospitals[0]
                                                    destination = nearest_hospital['coordinates']
                                                    
                                                    print(f"\nComputing routes to {nearest_hospital['name']}...")
                                                    route_result = await geo_session.call_tool(
                                                        "compute_routes",
                                                        arguments={
                                                            "origin": user_location,
                                                            "destination": destination,
                                                            "travel_mode": "DRIVE",
                                                            "avoid_threats": True,
                                                            "alternatives": True
                                                        }
                                                    )
                                                    
                                                    try:
                                                        route_data = json.loads(route_result.content[0].text)
                                                        
                                                        if route_data.get('route_count', 0) > 0:
                                                            print(f"\nFound {route_data['route_count']} route(s):")
                                                            for route in route_data.get('routes', [])[:3]:
                                                                threat_analysis = route.get('threat_analysis', {})
                                                                print(f"\nRoute {route['route_index'] + 1}: {route['summary']}")
                                                                print(f"  Distance: {route['distance_text']}")
                                                                print(f"  Duration: {route['duration_text']}")
                                                                if threat_analysis:
                                                                    print(f"  Safety Level: {threat_analysis.get('safety_level', 'unknown').upper()}")
                                                                    if threat_analysis.get('min_threat_distance_km'):
                                                                        print(f"  Closest Threat: {threat_analysis.get('min_threat_distance_km')}km away")
                                                            
                                                            print(f"\n✓ Recommended: Route {route_data['recommended_route_index'] + 1}")
                                                    except json.JSONDecodeError:
                                                        print("Error parsing route data.")
                                        
                                        except ValueError:
                                            print("Invalid location format. Please use: latitude,longitude (e.g., 40.5,-74.4)")
                                        except Exception as e:
                                            print(f"Error analyzing location: {str(e)}")


async def run_decoupled_demo():
    """
    Demonstrate the new decoupled architecture:
    1. Fetch data and persist to Firestore
    2. Show that events are stored with NEW status
    3. Query and display stored events
    """
    print("\n=== DECOUPLED ARCHITECTURE DEMONSTRATION ===\n")
    
    # Define server parameters for Data Collector
    data_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "data_collector", "main.py")],
        env=os.environ.copy()
    )
    
    # Define server parameters for Risk Assessment
    risk_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "risk_assessment", "main.py")],
        env=os.environ.copy()
    )
    
    # Define server parameters for Geolocation Safety Agent
    geo_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "geolocation", "main.py")],
        env=os.environ.copy()
    )
    
    # Define server parameters for Communication Agent
    comm_server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(agents_dir, "communication", "main.py")],
        env=os.environ.copy()
    )
    
    # Connect to Communication Agent
    async with stdio_client(comm_server_params) as (comm_read, comm_write):
        async with ClientSession(comm_read, comm_write) as comm_session:
            await comm_session.initialize()
            
            # Connect to Data Collector
            async with stdio_client(data_server_params) as (data_read, data_write):
                async with ClientSession(data_read, data_write) as data_session:
                    await data_session.initialize()
                    
                    # Connect to Risk Assessment
                    async with stdio_client(risk_server_params) as (risk_read, risk_write):
                        async with ClientSession(risk_read, risk_write) as risk_session:
                            await risk_session.initialize()
                            
                            # Connect to Geolocation Safety Agent
                            async with stdio_client(geo_server_params) as (geo_read, geo_write):
                                async with ClientSession(geo_read, geo_write) as geo_session:
                                    await geo_session.initialize()
                            
                                    print("--- Step 1: Data Collection (Persist to Firestore) ---")
                                    
                                    # Prompt user for natural language input
                                    print("\nPlease describe the situation.")
                                    print("Example: 'I think there is an earthquake in NJ' or 'Check for floods near Piscataway'")
                                    user_input = input("Your Input: ").strip()
                                    
                                    # Call Communication Agent to parse intent
                                    print("\nAnalyzing intent...")
                                    intent_result = await comm_session.call_tool("parse_user_intent", arguments={"user_input": user_input})
                                    
                                    try:
                                        intent_data = json.loads(intent_result.content[0].text)
                                        source = intent_data.get("source", "GDACS")
                                        location = intent_data.get("location")
                                        print(f"Agent Interpretation -> Source: {source}, Location: {location}")
                                    except json.JSONDecodeError:
                                        print("Error: Failed to parse intent from Communication Agent.")
                                        return
                                    
                                    # Fetch and persist events to Firestore
                                    print("\nFetching and persisting events to Firestore...")
                                    persist_result = await data_session.call_tool(
                                        "fetch_and_persist_events",
                                        arguments={"source": source, "location": location}
                                    )
                                    
                                    persist_data = json.loads(persist_result.content[0].text)
                                    print(f"Persistence Result: {json.dumps(persist_data, indent=2)}")
                                    
                                    if persist_data.get("saved_count", 0) > 0:
                                        print(f"\n✓ {persist_data['saved_count']} event(s) saved to Firestore with status=NEW")
                                        print("✓ These events are now available for asynchronous processing")
                                        
                                        print("\n--- Step 2: Query Firestore for NEW Events ---")
                                        
                                        # Query for NEW events
                                        new_events_result = await risk_session.call_tool(
                                            "get_assessed_events",
                                            arguments={"status_filter": "NEW", "limit": 10}
                                        )
                                        
                                        new_events = json.loads(new_events_result.content[0].text)
                                        
                                        # Handle both list and dict responses
                                        if isinstance(new_events, dict):
                                            if "error" in new_events:
                                                print(f"\n✗ Error querying events: {new_events['error']}")
                                            else:
                                                # Might be a single event wrapped in dict
                                                new_events = [new_events]
                                        
                                        if isinstance(new_events, list) and len(new_events) > 0:
                                            print(f"\nFound {len(new_events)} NEW event(s) in Firestore:")
                                            for i, event in enumerate(new_events[:5], 1):  # Show first 5
                                                print(f"{i}. {event.get('type')} in {event.get('location')} (ID: {event.get('event_id')})")
                                        else:
                                            print("\nNo NEW events found in Firestore")
                                        
                                        # Add geolocation safety check
                                        print("\n--- Step 3: Location Safety Check (Optional) ---")
                                        print("Would you like to check your location safety? (y/n)")
                                        check_safety = input().strip().lower()
                                        
                                        if check_safety == 'y':
                                            print("Enter your location as latitude,longitude (e.g., 40.5,-74.4):")
                                            user_loc_input = input().strip()
                                            
                                            try:
                                                lat, lon = map(float, user_loc_input.split(','))
                                                user_location = [lat, lon]
                                                
                                                # Get comprehensive safety check
                                                print("\nAnalyzing your location safety...")
                                                safety_result = await geo_session.call_tool(
                                                    "get_current_location_safety",
                                                    arguments={
                                                        "user_location": user_location,
                                                        "check_radius_km": 30.0
                                                    }
                                                )
                                                
                                                safety_data = json.loads(safety_result.content[0].text)
                                                
                                                print(f"\n{'='*60}")
                                                print(f"LOCATION SAFETY REPORT")
                                                print(f"{'='*60}")
                                                print(f"Status: {safety_data.get('overall_status', 'Unknown').upper()}")
                                                print(f"Recommendation: {safety_data.get('recommendation')}")
                                                
                                                threats_info = safety_data.get('threats', {})
                                                if threats_info.get('threat_count', 0) > 0:
                                                    print(f"\n⚠ Threats Detected: {threats_info['threat_count']}")
                                                    for threat in threats_info.get('threats', [])[:3]:
                                                        print(f"  • {threat['type']} - {threat['distance_km']}km away (Risk: {threat['risk_score']})")
                                                
                                                hospitals = safety_data.get('nearby_hospitals', [])
                                                if hospitals:
                                                    print(f"\n🏥 Nearest Hospitals:")
                                                    for h in hospitals[:2]:
                                                        print(f"  • {h['name']} - {h['distance_km']}km away")
                                                
                                                print(f"\n{'='*60}")
                                            
                                            except ValueError:
                                                print("Invalid location format. Please use: latitude,longitude")
                                            except Exception as e:
                                                print(f"Error analyzing location: {str(e)}")
                                        
                                        print("\n--- Next Steps ---")
                                        print("1. Run the Event Processor to process NEW events:")
                                        print("   python backend/services/event_processor.py")
                                        print("\n2. Run the Data Collection Scheduler for continuous monitoring:")
                                        print("   python backend/services/data_collector_scheduler.py")
                                        print("\n3. Query assessed events:")
                                        print("   Use the risk agent's get_assessed_events tool")
                                    else:
                                        print("\nNo new events to persist.")


def print_menu():
    """Print the coordinator menu"""
    print("\n" + "="*60)
    print("CRISIS INTEL COORDINATOR")
    print("="*60)
    print("\n1. Run Traditional Workflow (Request-Response)")
    print("   → Fetch data and process immediately")
    print("\n2. Run Decoupled Architecture Demo")
    print("   → Fetch data, persist to Firestore, and query")
    print("\n3. Exit")
    print("\n" + "="*60)

if __name__ == "__main__":
    print("Starting Coordinator...")
    try:
        while True:
            print_menu()
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == "1":
                print("\n[Running Traditional Workflow]\n")
                asyncio.run(run_workflow())
            elif choice == "2":
                print("\n[Running Decoupled Architecture Demo]\n")
                asyncio.run(run_decoupled_demo())
            elif choice == "3":
                print("\nExiting Coordinator.")
                break
            else:
                print("\nInvalid choice. Please select 1, 2, or 3.")
                
    except KeyboardInterrupt:
        print("\n\nCoordinator stopped.")
