# CrisisNet Decoupled Architecture - Visual Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL DATA SOURCES                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│    GDACS API         USGS API         Weather API        MOCK Data  │
│    (Disasters)     (Earthquakes)      (Future)          (Testing)   │
│                                                                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ HTTP Requests
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────┐         │
│  │   Data Collection Scheduler Service                     │         │
│  │   - Runs every 5 minutes (configurable)                │         │
│  │   - Triggers data collection from all sources          │         │
│  └────────────────┬───────────────────────────────────────┘         │
│                   │                                                  │
│                   ↓ MCP Tool Call                                    │
│  ┌────────────────────────────────────────────────────────┐         │
│  │   Data Collection Agent (MCP Server)                   │         │
│  │   Tools:                                                │         │
│  │   - fetch_disaster_feed() [backward compatible]        │         │
│  │   - fetch_and_persist_events() [new]                   │         │
│  └────────────────┬───────────────────────────────────────┘         │
│                   │                                                  │
└───────────────────┼──────────────────────────────────────────────────┘
                    │
                    │ Write Events
                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        PERSISTENCE LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────┐         │
│  │   Google Cloud Firestore                               │         │
│  │   Collection: crisis_events                            │         │
│  │                                                          │         │
│  │   Documents:                                            │         │
│  │   {                                                     │         │
│  │     event_id: "12345",                                 │         │
│  │     type: "Earthquake",                                │         │
│  │     location: "California",                            │         │
│  │     status: "NEW" → "ASSESSED" → "ERROR",              │         │
│  │     risk_assessment: { ... }                           │         │
│  │   }                                                     │         │
│  └────────────────┬───────────────────────────────────────┘         │
│                   │                                                  │
│                   │ Optional: Publish to Pub/Sub                     │
│                   ↓                                                  │
│  ┌────────────────────────────────────────────────────────┐         │
│  │   Google Cloud Pub/Sub (Optional)                      │         │
│  │   Topic: crisis-events                                 │         │
│  │   - Real-time event streaming                          │         │
│  │   - Replaces polling for production                    │         │
│  └────────────────┬───────────────────────────────────────┘         │
│                   │                                                  │
└───────────────────┼──────────────────────────────────────────────────┘
                    │
                    │ Poll/Subscribe for NEW events
                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────┐         │
│  │   Event Processor Service                              │         │
│  │   - Polls Firestore every 30 seconds                   │         │
│  │   - OR subscribes to Pub/Sub topic                     │         │
│  │   - Queries for status=NEW events                      │         │
│  └────────────────┬───────────────────────────────────────┘         │
│                   │                                                  │
│                   ↓ MCP Tool Call                                    │
│  ┌────────────────────────────────────────────────────────┐         │
│  │   Risk Assessment Agent (MCP Server)                   │         │
│  │   Tools:                                                │         │
│  │   - classify_event() [AI-powered analysis]             │         │
│  │   - get_assessed_events()                              │         │
│  │   - get_high_risk_events()                             │         │
│  │                                                          │         │
│  │   Uses:                                                 │         │
│  │   - Google Gemini 2.5 Flash Lite                       │         │
│  │   - Google Search Tool (ADK)                           │         │
│  └────────────────┬───────────────────────────────────────┘         │
│                   │                                                  │
│                   ↓ Returns: {severity, risk_score, reasoning}       │
│                   │                                                  │
└───────────────────┼──────────────────────────────────────────────────┘
                    │
                    │ Update Event
                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    UPDATED PERSISTENCE LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Firestore Document Updated:                                        │
│  {                                                                   │
│    event_id: "12345",                                               │
│    status: "ASSESSED",                ← Updated                     │
│    risk_assessment: {                 ← Added                       │
│      severity: "High",                                              │
│      risk_score: 85,                                                │
│      reasoning: "..."                                               │
│    },                                                                │
│    assessed_at: "2025-11-29T10:05:00Z"  ← Added                     │
│  }                                                                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Event State Flow

```
┌──────────┐
│  Source  │
│  (GDACS) │
└────┬─────┘
     │
     ↓ Data Collection Scheduler fetches
┌──────────────────┐
│   Firestore      │
│  status: "NEW"   │
└────┬─────────────┘
     │
     ↓ Event Processor queries
┌─────────────────────┐
│  Risk Assessment    │
│  Agent analyzes     │
└────┬────────────────┘
     │
     ↓ Updates
┌───────────────────────┐
│   Firestore           │
│  status: "ASSESSED"   │
│  + risk_assessment    │
└───────────────────────┘
     │
     ↓ Future: Query by apps
┌────────────────────────┐
│  User Interface        │
│  - Mobile App          │
│  - Web Dashboard       │
│  - Alert System        │
└────────────────────────┘
```

## Two Operating Modes

### Mode 1: Traditional (Synchronous)
```
User Input
  ↓
Coordinator
  ↓
Data Agent → Risk Agent
  ↓
Output to User
```

**Use Case**: Interactive queries, testing, demos

**How to Run**:
```bash
python coordinator/main.py
# Select option 1
```

---

### Mode 2: Decoupled (Asynchronous)
```
Schedule (5 min)        Poll (30 sec)
  ↓                        ↓
Data Collector    Event Processor
  ↓                        ↓
Firestore (NEW)  →  Risk Agent
  ↓                        ↓
     (Firestore ASSESSED)
```

**Use Case**: Continuous monitoring, production deployment

**How to Run**:
```bash
# Terminal 1
python services/data_collector_scheduler.py

# Terminal 2
python services/event_processor.py
```

## Component Communication

### MCP (Model Context Protocol)
- All agents are MCP servers
- Services act as MCP clients
- Tools are invoked via `ClientSession.call_tool()`

### Firestore Queries
```python
# Query NEW events
db.collection("crisis_events").where("status", "==", "NEW")

# Query ASSESSED events
db.collection("crisis_events").where("status", "==", "ASSESSED")

# Query high-risk events
db.collection("crisis_events")
  .where("status", "==", "ASSESSED")
  .where("risk_assessment.risk_score", ">=", 70)
```

## Scalability Considerations

### Current (Polling)
- Single instance of each service
- Polls Firestore every 30 seconds
- Good for: Development, testing, small-scale

### Production (Pub/Sub)
- Multiple instances can process in parallel
- Event-driven (no polling delay)
- Auto-scales based on message queue
- Good for: Production, high-volume

## Directory Structure

```
crisis-intel-agent/
├── backend/
│   ├── agents/                    # MCP Servers
│   │   ├── data_collector/
│   │   │   └── main.py           # Data Collection Agent
│   │   ├── risk_assessment/
│   │   │   └── main.py           # Risk Assessment Agent
│   │   └── communication/
│   │       └── main.py           # Communication Agent
│   │
│   ├── services/                  # Background Services (NEW)
│   │   ├── event_processor.py        # Processes NEW events
│   │   ├── data_collector_scheduler.py  # Periodic data fetch
│   │   └── pubsub_integration.py     # Pub/Sub publisher/subscriber
│   │
│   ├── coordinator/
│   │   └── main.py               # Interactive coordinator
│   │
│   ├── quickstart_decoupled.py   # Quick demo script
│   └── DECOUPLED_ARCHITECTURE.md # Full documentation
│
├── launch.bat                     # Windows launcher
└── IMPLEMENTATION_SUMMARY.md      # This summary
```

## Configuration Files

### `.env` (Required)
```bash
GCP_PROJECT_ID=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### `.env` (Optional)
```bash
# Data Collection
DATA_SOURCES=GDACS,USGS
COLLECTION_INTERVAL=300

# Event Processing
EVENT_PROCESSOR_POLL_INTERVAL=30

# Pub/Sub
PUBSUB_TOPIC_NAME=crisis-events
PUBSUB_SUBSCRIPTION_NAME=crisis-events-processor
```

## Getting Started Checklist

- [ ] Install dependencies: `pip install -r backend/requirements.txt`
- [ ] Set up GCP credentials and `.env` file
- [ ] Enable Firestore in GCP Console
- [ ] Run quick demo: `python backend/quickstart_decoupled.py`
- [ ] Test coordinator: `python backend/coordinator/main.py` (option 2)
- [ ] Start continuous monitoring:
  - [ ] Terminal 1: Data Collector Scheduler
  - [ ] Terminal 2: Event Processor
- [ ] (Optional) Set up Pub/Sub for production

---

**System Status**: ✅ Ready for continuous monitoring!
