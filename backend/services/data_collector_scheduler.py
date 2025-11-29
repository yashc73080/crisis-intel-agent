"""
Data Collection Scheduler

This service periodically fetches disaster data from external sources and persists it to Firestore.
It decouples data collection from processing, enabling continuous monitoring.

Usage:
    python services/data_collector_scheduler.py
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# Agent paths
agents_dir = os.path.join(backend_dir, "agents")

class DataCollectionScheduler:
    """Periodically fetches disaster data and saves to Firestore"""
    
    def __init__(self, sources: list = None, collection_interval: int = 300):
        """
        Initialize the data collection scheduler.
        
        Args:
            sources: List of data sources to collect from (default: ["GDACS"])
            collection_interval: Seconds between collection cycles (default: 300 = 5 minutes)
        """
        self.sources = sources or ["GDACS"]
        self.collection_interval = collection_interval
        self.data_agent_path = os.path.join(agents_dir, "data_collector", "main.py")
        
    async def collect_from_source(self, source: str, data_session: ClientSession) -> Dict[str, Any]:
        """
        Collect data from a specific source.
        
        Args:
            source: Data source identifier (e.g., "GDACS", "MOCK")
            data_session: Active MCP session with Data Collection Agent
            
        Returns:
            Collection result summary
        """
        try:
            print(f"[COLLECTING] Fetching data from {source}...")
            
            # Call the fetch_and_persist_events tool
            result = await data_session.call_tool(
                "fetch_and_persist_events",
                arguments={"source": source, "location": None}
            )
            
            # Parse the result
            result_data = json.loads(result.content[0].text)
            
            saved_count = result_data.get("saved_count", 0)
            status = result_data.get("status", "unknown")
            
            if status == "success":
                print(f"[SUCCESS] {source}: {saved_count} event(s) saved to Firestore")
            elif status == "no_events":
                print(f"[INFO] {source}: No new events available")
            else:
                print(f"[WARNING] {source}: Unexpected status - {result_data}")
            
            return result_data
            
        except Exception as e:
            print(f"[ERROR] Failed to collect from {source}: {e}")
            return {"status": "error", "source": source, "error": str(e)}
    
    async def run_collection_cycle(self):
        """Run one cycle of data collection"""
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting collection cycle")
        
        # Connect to Data Collection Agent
        data_server_params = StdioServerParameters(
            command="python",
            args=[self.data_agent_path],
            env=os.environ.copy()
        )
        
        async with stdio_client(data_server_params) as (data_read, data_write):
            async with ClientSession(data_read, data_write) as data_session:
                await data_session.initialize()
                
                # Collect from each source
                total_saved = 0
                for source in self.sources:
                    result = await self.collect_from_source(source, data_session)
                    total_saved += result.get("saved_count", 0)
                
                print(f"[CYCLE COMPLETE] Total events saved: {total_saved}\n")
    
    async def start_scheduled_collection(self):
        """Start continuous collection loop"""
        print(f"Data Collection Scheduler started")
        print(f"Sources: {', '.join(self.sources)}")
        print(f"Collection interval: {self.collection_interval}s ({self.collection_interval // 60} minutes)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                await self.run_collection_cycle()
                
                # Calculate next run time
                next_run = datetime.now().timestamp() + self.collection_interval
                next_run_str = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
                print(f"Next collection at: {next_run_str}")
                
                await asyncio.sleep(self.collection_interval)
                
        except KeyboardInterrupt:
            print("\n\nData Collection Scheduler stopped")


async def main():
    """Main entry point"""
    
    # Get configuration from environment variables
    sources_str = os.getenv("DATA_SOURCES", "GDACS")
    sources = [s.strip() for s in sources_str.split(",")]
    
    collection_interval = int(os.getenv("COLLECTION_INTERVAL", "300"))  # 5 minutes default
    
    scheduler = DataCollectionScheduler(
        sources=sources,
        collection_interval=collection_interval
    )
    
    await scheduler.start_scheduled_collection()


if __name__ == "__main__":
    asyncio.run(main())
