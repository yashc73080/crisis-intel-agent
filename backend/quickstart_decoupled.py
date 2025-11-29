"""
Quick Start Script for Decoupled Architecture

This script helps you quickly test the decoupled architecture.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data_collector_scheduler import DataCollectionScheduler
from services.event_processor import EventProcessor

async def run_single_collection():
    """Run one data collection cycle"""
    print("=" * 60)
    print("STEP 1: COLLECTING DATA")
    print("=" * 60)
    
    scheduler = DataCollectionScheduler(sources=["MOCK"], collection_interval=60)
    await scheduler.run_collection_cycle()
    
    print("\n" + "=" * 60)
    print("STEP 2: PROCESSING EVENTS")
    print("=" * 60)
    
    processor = EventProcessor(poll_interval=30)
    await processor.run_processing_cycle()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nTo run continuously:")
    print("  Terminal 1: python services/data_collector_scheduler.py")
    print("  Terminal 2: python services/event_processor.py")

if __name__ == "__main__":
    print("\nCrisis Intel - Decoupled Architecture Quick Start")
    print("=" * 60)
    print("\nThis will:")
    print("1. Fetch mock disaster data")
    print("2. Save to Firestore (status=NEW)")
    print("3. Process events with Risk Assessment Agent")
    print("4. Update Firestore (status=ASSESSED)")
    print("\n" + "=" * 60)
    
    try:
        asyncio.run(run_single_collection())
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("1. GOOGLE_APPLICATION_CREDENTIALS is set")
        print("2. GCP_PROJECT_ID is set in .env")
        print("3. Firestore is enabled in your GCP project")
