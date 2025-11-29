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
                                
                                print(f"Risk Analysis: {risk_result.content[0].text}")

if __name__ == "__main__":
    print("Starting Coordinator...")
    try:
        asyncio.run(run_workflow())
    except KeyboardInterrupt:
        print("\nCoordinator stopped.")
