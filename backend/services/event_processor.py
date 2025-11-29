"""
Event Processor Service

This service monitors Firestore for NEW events and triggers risk assessment processing.
It implements the decoupled architecture where data collection is separated from processing.

Usage:
    python services/event_processor.py
"""

import asyncio
import os
import sys
import json
from typing import List, Dict, Any
from google.cloud import firestore
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# Firestore setup
db = firestore.Client()
EVENTS_COLLECTION = "crisis_events"

# Agent paths
agents_dir = os.path.join(backend_dir, "agents")

class EventProcessor:
    """Processes NEW events from Firestore using the Risk Assessment Agent"""
    
    def __init__(self, poll_interval: int = 30, max_retries: int = 3):
        """
        Initialize the event processor.
        
        Args:
            poll_interval: Seconds between polling cycles (default: 30)
            max_retries: Maximum retry attempts for failed assessments (default: 3)
        """
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.risk_agent_path = os.path.join(agents_dir, "risk_assessment", "main.py")
        
    async def process_event(self, event_doc: Dict[str, Any], risk_session: ClientSession) -> bool:
        """
        Process a single event using the Risk Assessment Agent with retry logic.
        
        Args:
            event_doc: Event document from Firestore
            risk_session: Active MCP session with Risk Assessment Agent
            
        Returns:
            True if processing succeeded, False otherwise
        """
        event_id = event_doc.get("event_id", "unknown")
        doc_id = event_doc.get("_doc_id")  # Firestore document ID
        
        print(f"[PROCESSING] Event {event_id} (Doc: {doc_id})")
        
        # Extract event data
        event_type = event_doc.get("type", "Unknown")
        description = event_doc.get("description", "")
        location = event_doc.get("location", "")
        coordinates = event_doc.get("coordinates", None)
        
        # Retry logic for failed assessments
        for attempt in range(1, self.max_retries + 1):
            try:
                # Call Risk Assessment Agent
                risk_result = await risk_session.call_tool(
                    "classify_event",
                    arguments={
                        "event_description": description,
                        "event_type": event_type,
                        "location": location,
                        "coordinates": coordinates
                    }
                )
                
                # Parse the result
                risk_data = json.loads(risk_result.content[0].text)
                
                # Check if we got a valid response (not empty or unknown)
                if risk_data.get("risk_score", 0) == 0 and risk_data.get("severity") == "Unknown":
                    if attempt < self.max_retries:
                        print(f"[RETRY] Attempt {attempt}/{self.max_retries} - Got empty response, retrying...")
                        await asyncio.sleep(2)  # Wait 2 seconds before retry
                        continue
                    else:
                        print(f"[WARNING] {event_id}: All retries exhausted, got empty response")
                
                print(f"[RESULT] {event_id}: {risk_data.get('severity')} (Score: {risk_data.get('risk_score')})")
                
                # Update Firestore with risk assessment results
                doc_ref = db.collection(EVENTS_COLLECTION).document(doc_id)
                doc_ref.update({
                    "status": "ASSESSED",
                    "risk_assessment": risk_data,
                    "assessed_at": firestore.SERVER_TIMESTAMP,
                    "retry_count": attempt - 1  # Track how many retries were needed
                })
                
                return True
                
            except json.JSONDecodeError as je:
                if attempt < self.max_retries:
                    print(f"[RETRY] Attempt {attempt}/{self.max_retries} - JSON parse error, retrying...")
                    await asyncio.sleep(2)
                    continue
                else:
                    print(f"[ERROR] {event_id}: Failed to parse response after {self.max_retries} attempts")
                    # Mark as error
                    doc_ref = db.collection(EVENTS_COLLECTION).document(doc_id)
                    doc_ref.update({
                        "status": "ERROR",
                        "error_message": f"JSON parse error: {str(je)}",
                        "error_at": firestore.SERVER_TIMESTAMP
                    })
                    return False
                    
            except Exception as e:
                if attempt < self.max_retries:
                    print(f"[RETRY] Attempt {attempt}/{self.max_retries} - Error: {str(e)}, retrying...")
                    await asyncio.sleep(2)
                    continue
                else:
                    print(f"[ERROR] Failed to process event {event_id} after {self.max_retries} attempts: {e}")
                    # Mark as error in Firestore
                    try:
                        doc_ref = db.collection(EVENTS_COLLECTION).document(doc_id)
                        doc_ref.update({
                            "status": "ERROR",
                            "error_message": str(e),
                            "error_at": firestore.SERVER_TIMESTAMP
                        })
                    except Exception as update_error:
                        print(f"[ERROR] Failed to update error status: {update_error}")
                    
                    return False
        
        return False
    
    async def get_new_events(self) -> List[Dict[str, Any]]:
        """
        Query Firestore for events with status=NEW.
        
        Returns:
            List of event documents with NEW status
        """
        try:
            query = db.collection(EVENTS_COLLECTION).where("status", "==", "NEW").limit(50)
            docs = query.stream()
            
            events = []
            for doc in docs:
                event_data = doc.to_dict()
                event_data["_doc_id"] = doc.id  # Store Firestore doc ID for updates
                events.append(event_data)
            
            return events
            
        except Exception as e:
            print(f"[ERROR] Failed to query Firestore: {e}")
            return []
    
    async def get_failed_assessments(self) -> List[Dict[str, Any]]:
        """
        Query Firestore for events that were assessed but got Unknown/0 score.
        These need to be reprocessed.
        
        Returns:
            List of event documents with failed assessments
        """
        try:
            # Query for ASSESSED events with risk_score = 0
            query = (db.collection(EVENTS_COLLECTION)
                    .where("status", "==", "ASSESSED")
                    .limit(20))
            docs = query.stream()
            
            failed_events = []
            for doc in docs:
                event_data = doc.to_dict()
                risk_assessment = event_data.get("risk_assessment", {})
                
                # Check if it's a failed assessment (score 0 and Unknown)
                if (risk_assessment.get("risk_score") == 0 and 
                    risk_assessment.get("severity") == "Unknown"):
                    event_data["_doc_id"] = doc.id
                    failed_events.append(event_data)
            
            return failed_events
            
        except Exception as e:
            print(f"[ERROR] Failed to query failed assessments: {e}")
            return []
    
    async def run_processing_cycle(self):
        """Run one cycle of event processing"""
        
        # Get new events from Firestore
        new_events = await self.get_new_events()
        
        # Get failed assessments to retry
        failed_events = await self.get_failed_assessments()
        
        total_to_process = len(new_events) + len(failed_events)
        
        if total_to_process == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No new events to process")
            return
        
        if new_events:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found {len(new_events)} NEW event(s)")
        if failed_events:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(failed_events)} failed assessment(s) to retry")
        
        # Connect to Risk Assessment Agent
        risk_server_params = StdioServerParameters(
            command="python",
            args=[self.risk_agent_path],
            env=os.environ.copy()
        )
        
        async with stdio_client(risk_server_params) as (risk_read, risk_write):
            async with ClientSession(risk_read, risk_write) as risk_session:
                await risk_session.initialize()
                
                success_count = 0
                
                # Process new events first
                for event in new_events:
                    if await self.process_event(event, risk_session):
                        success_count += 1
                
                # Then retry failed assessments
                for event in failed_events:
                    # Reset to NEW status before reprocessing
                    doc_ref = db.collection(EVENTS_COLLECTION).document(event["_doc_id"])
                    doc_ref.update({"status": "NEW"})
                    
                    print(f"[RETRY] Reprocessing failed assessment for {event.get('event_id')}")
                    if await self.process_event(event, risk_session):
                        success_count += 1
                
                print(f"[SUMMARY] Processed {success_count}/{total_to_process} events successfully\n")
    
    async def start_monitoring(self):
        """Start continuous monitoring loop"""
        print(f"Event Processor started (polling every {self.poll_interval}s)")
        print(f"Monitoring Firestore collection: {EVENTS_COLLECTION}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                await self.run_processing_cycle()
                await asyncio.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\nEvent Processor stopped")


async def main():
    """Main entry point"""
    
    # Get poll interval from environment or use default
    poll_interval = int(os.getenv("EVENT_PROCESSOR_POLL_INTERVAL", "30"))
    
    processor = EventProcessor(poll_interval=poll_interval)
    await processor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
