# Decoupled Architecture Guide

## Overview

The CrisisNet system now supports a **decoupled, event-driven architecture** that separates data collection from processing. This enables continuous monitoring, scalability, and fault tolerance.

## Architecture Components

### 1. **Data Collection Agent** (`agents/data_collector/main.py`)
- Fetches disaster data from external sources (GDACS, USGS, etc.)
- Persists events to Firestore with `status=NEW`
- Provides two tools:
  - `fetch_disaster_feed` - Original synchronous fetch (for backward compatibility)
  - `fetch_and_persist_events` - New tool that saves to Firestore

### 2. **Risk Assessment Agent** (`agents/risk_assessment/main.py`)
- Analyzes events using Gemini AI with Google Search
- Queries Firestore for events to process
- Updates event status to `ASSESSED` with risk data
- New tools:
  - `get_assessed_events` - Query events by status
  - `get_high_risk_events` - Query high-risk events (score >= threshold)

### 3. **Event Processor Service** (`services/event_processor.py`)
- Continuously monitors Firestore for `NEW` events
- Triggers Risk Assessment Agent for each new event
- Updates event status to `ASSESSED` or `ERROR`
- Configurable polling interval (default: 30 seconds)

### 4. **Data Collection Scheduler** (`services/data_collector_scheduler.py`)
- Periodically fetches data from configured sources
- Persists to Firestore automatically
- Enables continuous monitoring without manual intervention
- Configurable collection interval (default: 5 minutes)

### 5. **Pub/Sub Integration** (`services/pubsub_integration.py`) *(Optional)*
- Replaces polling with event-driven processing
- Publishes events to Google Cloud Pub/Sub when created
- Subscribers process events in real-time
- Better for production at scale

## Data Flow

### Decoupled Architecture (New)

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Data Collector Scheduler (runs every 5 min)                │
│         ↓                                                     │
│  Data Collection Agent                                       │
│         ↓                                                     │
│  Fetch from GDACS/USGS/etc.                                  │
│         ↓                                                     │
│  Save to Firestore (status=NEW)  ─────→ [Pub/Sub Topic]     │
│                                              (optional)       │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓ (Firestore events)
┌─────────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Event Processor Service (polls every 30s)                  │
│    OR                                                         │
│  Pub/Sub Subscriber (real-time)                             │
│         ↓                                                     │
│  Risk Assessment Agent                                       │
│         ↓                                                     │
│  Analyze with Gemini + Google Search                        │
│         ↓                                                     │
│  Update Firestore (status=ASSESSED, add risk_assessment)    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Traditional Architecture (Backward Compatible)

```
User Input → Coordinator → Data Agent → Risk Agent → Output
(synchronous request-response)
```

## Getting Started

### Prerequisites

1. **Google Cloud Setup**:
   ```bash
   # Set environment variables in .env
   GCP_PROJECT_ID=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ```

2. **Firestore Setup**:
   - Enable Firestore in your GCP project
   - Create database in Native mode
   - The `crisis_events` collection will be created automatically

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Decoupled System

#### Option 1: Manual Testing

1. **Start the Coordinator**:
   ```bash
   cd backend
   python coordinator/main.py
   ```
   
2. Select option 2 (Decoupled Architecture Demo)

3. Enter a query (e.g., "Check for earthquakes in California")

4. Events are saved to Firestore with `status=NEW`

#### Option 2: Continuous Monitoring (Recommended)

**Terminal 1 - Data Collection**:
```bash
cd backend
python services/data_collector_scheduler.py
```

**Terminal 2 - Event Processing**:
```bash
cd backend
python services/event_processor.py
```

Now the system runs continuously:
- Every 5 minutes: Fetches new disaster data
- Every 30 seconds: Processes NEW events from Firestore

#### Option 3: Pub/Sub (Production)

1. **Create Pub/Sub resources**:
   ```bash
   gcloud pubsub topics create crisis-events
   gcloud pubsub subscriptions create crisis-events-processor --topic=crisis-events
   ```

2. **Modify Data Collector to publish to Pub/Sub**:
   ```python
   # In agents/data_collector/main.py
   from services.pubsub_integration import PubSubPublisher
   
   publisher = PubSubPublisher()
   
   # In save_event_to_firestore function:
   doc_id = doc_ref.id
   publisher.publish_event(event_data)  # Add this line
   ```

3. **Start Pub/Sub subscriber**:
   ```bash
   python services/pubsub_integration.py listen
   ```

## Configuration

### Environment Variables

```bash
# Required
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Optional - Data Collection
DATA_SOURCES=GDACS,USGS              # Comma-separated sources
COLLECTION_INTERVAL=300               # Seconds (default: 300 = 5 min)

# Optional - Event Processing
EVENT_PROCESSOR_POLL_INTERVAL=30      # Seconds (default: 30)

# Optional - Pub/Sub
PUBSUB_TOPIC_NAME=crisis-events
PUBSUB_SUBSCRIPTION_NAME=crisis-events-processor
```

## Firestore Schema

### Event Document Structure

```json
{
  "event_id": "1234567",
  "type": "Earthquake",
  "location": "California, USA",
  "description": "M 6.5 earthquake near San Francisco",
  "timestamp": "2025-11-29T10:00:00Z",
  "coordinates": [-122.4194, 37.7749],
  "source": "GDACS",
  
  "status": "ASSESSED",
  "created_at": "2025-11-29T10:05:00Z",
  "assessed_at": "2025-11-29T10:05:30Z",
  
  "risk_assessment": {
    "severity": "High",
    "risk_score": 85,
    "reasoning": "Major earthquake with significant impact potential..."
  }
}
```

### Event Status Values

- `NEW` - Event fetched and persisted, awaiting risk assessment
- `ASSESSED` - Risk assessment completed successfully
- `ERROR` - Processing failed (check `error_message` field)

## Querying Events

### From Python (using Risk Assessment Agent tools)

```python
# Query NEW events
new_events = await risk_session.call_tool(
    "get_assessed_events",
    arguments={"status_filter": "NEW", "limit": 50}
)

# Query high-risk events
high_risk = await risk_session.call_tool(
    "get_high_risk_events",
    arguments={"min_risk_score": 70, "limit": 50}
)
```

### From Firestore Console

1. Go to [Firestore Console](https://console.cloud.google.com/firestore)
2. Select `crisis_events` collection
3. Filter by status: `status == "ASSESSED"`
4. Sort by: `risk_assessment.risk_score` descending

## Production Deployment

### Deploy to Cloud Run

1. **Event Processor**:
   ```bash
   # Build container
   docker build -t gcr.io/YOUR_PROJECT/event-processor -f Dockerfile.processor .
   
   # Deploy
   gcloud run deploy event-processor \
     --image gcr.io/YOUR_PROJECT/event-processor \
     --platform managed \
     --region us-central1
   ```

2. **Data Collector Scheduler**:
   ```bash
   # Use Cloud Scheduler to trigger Cloud Run service
   gcloud scheduler jobs create http collect-data \
     --schedule="*/5 * * * *" \
     --uri="https://YOUR_COLLECTOR_URL/collect" \
     --http-method=POST
   ```

### Deploy with Pub/Sub Triggers

```bash
# Deploy event processor with Pub/Sub trigger
gcloud run deploy event-processor \
  --image gcr.io/YOUR_PROJECT/event-processor \
  --platform managed \
  --trigger-topic crisis-events
```

## Benefits of Decoupled Architecture

1. **Scalability**: Process events in parallel across multiple instances
2. **Fault Tolerance**: Failed events are retried automatically
3. **Flexibility**: Add new processors without changing data collection
4. **Monitoring**: Track event status and processing metrics in Firestore
5. **Continuous Operation**: System runs 24/7 without manual intervention
6. **Rate Limiting**: Control processing rate independently of data collection

## Troubleshooting

### Events not being processed

1. Check Event Processor logs
2. Verify Firestore has events with `status=NEW`
3. Check GCP credentials and project ID
4. Ensure Risk Assessment Agent is accessible

### Pub/Sub messages not received

1. Verify topic and subscription exist:
   ```bash
   gcloud pubsub topics list
   gcloud pubsub subscriptions list
   ```

2. Check IAM permissions:
   - Service account needs `pubsub.publisher` role
   - Service account needs `pubsub.subscriber` role

### High API costs

1. Increase polling intervals:
   ```bash
   export COLLECTION_INTERVAL=600  # 10 minutes
   export EVENT_PROCESSOR_POLL_INTERVAL=60  # 1 minute
   ```

2. Use Pub/Sub instead of polling for production

## Next Steps

1. **Add Geolocation Agent**: Process assessed events to find nearby threats
2. **Add Communication Agent**: Generate alerts for high-risk events
3. **Add Webhooks**: Send notifications to external systems
4. **Add Monitoring**: Set up Cloud Monitoring dashboards
5. **Add Testing**: Unit tests for event processing logic

## Migration from Synchronous to Decoupled

The coordinator supports both modes:

- **Option 1 (Traditional)**: Synchronous request-response workflow
- **Option 2 (Decoupled)**: Persist to Firestore and query

Existing code using `fetch_disaster_feed` continues to work. New code should use `fetch_and_persist_events` for decoupled architecture.
