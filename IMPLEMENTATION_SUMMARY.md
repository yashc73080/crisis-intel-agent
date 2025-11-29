# Crisis Intel Agent - Decoupled Architecture Implementation

## Summary of Changes

Your CrisisNet system has been successfully upgraded to support a **decoupled, event-driven architecture** that enables continuous monitoring and scalable processing. The system now separates data collection from processing using Firestore as the persistence layer.

## What Was Changed

### 1. **Data Collection Agent** (`agents/data_collector/main.py`)
- ✅ Added `fetch_and_persist_events()` tool
- ✅ Saves events to Firestore with `status=NEW`
- ✅ Maintains backward compatibility with original `fetch_disaster_feed()`

### 2. **Risk Assessment Agent** (`agents/risk_assessment/main.py`)
- ✅ Added `get_assessed_events()` - Query events by status
- ✅ Added `get_high_risk_events()` - Query high-risk events
- ✅ Original `classify_event()` tool unchanged (backward compatible)

### 3. **Event Processor Service** (`services/event_processor.py`) - NEW
- ✅ Continuously monitors Firestore for `NEW` events
- ✅ Triggers Risk Assessment Agent automatically
- ✅ Updates event status to `ASSESSED` or `ERROR`
- ✅ Configurable polling interval (default: 30 seconds)

### 4. **Data Collection Scheduler** (`services/data_collector_scheduler.py`) - NEW
- ✅ Periodically fetches disaster data
- ✅ Persists to Firestore automatically
- ✅ Enables continuous monitoring
- ✅ Configurable collection interval (default: 5 minutes)

### 5. **Pub/Sub Integration** (`services/pubsub_integration.py`) - NEW
- ✅ Optional replacement for polling
- ✅ Event-driven processing via Google Cloud Pub/Sub
- ✅ Publisher and Subscriber classes ready to use
- ✅ Better for production at scale

### 6. **Enhanced Coordinator** (`coordinator/main.py`)
- ✅ Added interactive menu with two modes:
  - Option 1: Traditional request-response workflow
  - Option 2: Decoupled architecture demo
- ✅ Demonstrates Firestore persistence and querying
- ✅ Backward compatible with existing workflows

### 7. **Documentation & Tools**
- ✅ `DECOUPLED_ARCHITECTURE.md` - Complete guide
- ✅ `quickstart_decoupled.py` - Quick demo script
- ✅ Updated `requirements.txt` with Pub/Sub dependency

## Architecture Comparison

### Before (Synchronous)
```
User Input → Coordinator → Data Agent → Risk Agent → Output
```

### After (Decoupled)
```
Data Collector Scheduler (every 5 min)
    ↓
Fetch & Save to Firestore (status=NEW)
    ↓
Event Processor (every 30 sec)
    ↓
Risk Assessment Agent
    ↓
Update Firestore (status=ASSESSED)
```

## How to Use

### Quick Demo
```bash
cd backend
python quickstart_decoupled.py
```

### Interactive Coordinator
```bash
cd backend
python coordinator/main.py
# Select option 2 for decoupled demo
```

### Continuous Monitoring (Recommended)

**Terminal 1 - Data Collection:**
```bash
cd backend
python services/data_collector_scheduler.py
```

**Terminal 2 - Event Processing:**
```bash
cd backend
python services/event_processor.py
```

### Configuration (Optional)
Add to your `.env` file:
```bash
# Data collection
DATA_SOURCES=GDACS,USGS
COLLECTION_INTERVAL=300

# Event processing
EVENT_PROCESSOR_POLL_INTERVAL=30

# Pub/Sub (optional)
PUBSUB_TOPIC_NAME=crisis-events
PUBSUB_SUBSCRIPTION_NAME=crisis-events-processor
```

## Key Benefits

1. ✅ **Decoupled**: Data collection runs independently from processing
2. ✅ **Continuous**: Monitors for events 24/7 automatically
3. ✅ **Scalable**: Can scale data collection and processing independently
4. ✅ **Fault Tolerant**: Failed events can be retried
5. ✅ **Persistent**: All events stored in Firestore for audit trail
6. ✅ **Backward Compatible**: Original workflow still works

## Firestore Schema

Events are stored in the `crisis_events` collection:

```json
{
  "event_id": "1234567",
  "type": "Earthquake",
  "location": "California, USA",
  "description": "M 6.5 earthquake",
  "timestamp": "2025-11-29T10:00:00Z",
  "coordinates": [-122.4194, 37.7749],
  "source": "GDACS",
  "status": "ASSESSED",
  "created_at": "<timestamp>",
  "assessed_at": "<timestamp>",
  "risk_assessment": {
    "severity": "High",
    "risk_score": 85,
    "reasoning": "..."
  }
}
```

## Next Steps

### Immediate Testing
1. Run `quickstart_decoupled.py` to see the flow
2. Check Firestore Console to see stored events
3. Run coordinator in decoupled mode (option 2)

### Production Deployment
1. Set up Google Cloud Pub/Sub:
   ```bash
   gcloud pubsub topics create crisis-events
   gcloud pubsub subscriptions create crisis-events-processor --topic=crisis-events
   ```

2. Modify data collector to publish to Pub/Sub (see `DECOUPLED_ARCHITECTURE.md`)

3. Deploy services to Cloud Run (see deployment guide)

### Future Enhancements
- Add Geolocation Agent to process assessed events
- Add Communication Agent to generate alerts
- Add webhooks for high-risk event notifications
- Add monitoring dashboards
- Implement user-specific location tracking

## Files Created/Modified

### New Files
- `backend/services/event_processor.py`
- `backend/services/data_collector_scheduler.py`
- `backend/services/pubsub_integration.py`
- `backend/DECOUPLED_ARCHITECTURE.md`
- `backend/quickstart_decoupled.py`
- `backend/IMPLEMENTATION_SUMMARY.md` (this file)

### Modified Files
- `backend/agents/data_collector/main.py` - Added persistence tool
- `backend/agents/risk_assessment/main.py` - Added query tools
- `backend/coordinator/main.py` - Added menu and decoupled demo
- `backend/requirements.txt` - Added Pub/Sub dependency

## Troubleshooting

### Events not appearing in Firestore
- Check `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Verify `GCP_PROJECT_ID` in `.env`
- Ensure Firestore is enabled in GCP Console

### Processing not working
- Check Event Processor logs for errors
- Verify Risk Assessment Agent credentials
- Check Firestore for events with `status=NEW`

### High API costs
- Increase polling intervals in `.env`
- Switch to Pub/Sub for production
- Limit data sources to only what's needed

## Support

For detailed documentation, see:
- `DECOUPLED_ARCHITECTURE.md` - Complete architecture guide
- `project.md` - Original project design
- `README.md` - General project information

Your system is now ready for continuous monitoring! 🚀
