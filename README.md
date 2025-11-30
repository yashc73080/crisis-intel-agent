# CrisisNet  
A Multi-Agent System for Real-Time Crisis Intelligence

CrisisNet is a multi-agent platform designed to provide real-time, actionable safety advice, threat detection, and evacuation guidance during global emergencies, conflicts, and natural disasters. It converts passive threat feeds into live geographic safety intelligence using Google Gemini, Google Maps APIs, and an event-driven decoupled architecture.

---

## Features

- Real-time global disaster monitoring  
- Severity classification and risk scoring (0 to 100)  
- Threat mapping with evacuation route generation  
- Natural language querying for crisis information  
- Fully decoupled multi-agent pipeline with Firestore persistence  

---

## System Architecture

CrisisNet uses autonomous agents that communicate through the Model Context Protocol (MCP).  
The system supports continuous background operation through decoupled scheduling and processing loops.

### Agent Overview

| Agent               | Function                                                                 | Key Tools                                 | Technologies                             |
|---------------------|---------------------------------------------------------------------------|-------------------------------------------|-------------------------------------------|
| Data Collection     | Fetches live disaster data (GDACS, USGS) and writes events to Firestore. | fetch_disaster_feed, fetch_and_persist_events | GDACS API, Firestore |
| Risk Assessment     | Computes severity and a 0 to 100 risk score.                             | classify_event, get_assessed_events       | Gemini 2.5 Flash Lite, Google Search |
| Geolocation Safety  | Maps threats, finds hospitals and shelters, computes safe routes.         | map_threat_radius, compute_routes, get_current_location_safety | Google Maps Places and Directions |
| Communication       | Parses natural language user intent and query location or source.         | parse_user_intent                         | Gemini 2.5 Flash Lite |

---

## Installation

### Prerequisites

- Python 3.9+
- Google Cloud Project with:
  - Firestore API enabled
  - Maps Places API enabled
  - Maps Directions API enabled
- Required credentials:
  - Service Account JSON
  - Google Maps API Key
  - Gemini API Key

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yashc73080/crisis-intel-agent
cd crisis-intel-agent
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Authentication & Project Setup
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-gcp-project-id
GCP_PROJECT_NUMBER=your-gcp-project-number

# API Keys
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_API_KEY=your_gemini_api_key_or_vertex_setup_required

# Optional Decoupled Config
COLLECTION_INTERVAL=300
EVENT_PROCESSOR_POLL_INTERVAL=30
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## Running the System

### Option 1: Continuous Decoupled Monitoring  
Recommended for real-time background operation.

| Component        | Command                                                  | Description |
|------------------|----------------------------------------------------------|-------------|
| Data Scheduler   | `python backend/services/data_collector_scheduler.py`    | Fetches disaster feeds and writes events with status=NEW. |
| Event Processor  | `python backend/services/event_processor.py`             | Processes NEW events and updates to ASSESSED. |

---

### Option 2: Interactive Coordinator (Demo or Testing)

```bash
python backend/coordinator/main.py
```

Coordinator features:

- Traditional synchronous workflow  
- Decoupled workflow demo  
- Event inspection utilities  

---

### Option 3: API Gateway (Frontend Integration)

Start the FastAPI server:

```bash
uvicorn backend.api_gateway:app --reload --host 0.0.0.0 --port 8000
```

API documentation:

```
http://localhost:8000/docs
```

---

## Maintenance and Testing

### Quick Start (MOCK data)

```bash
python backend/quickstart_decoupled.py
```

### Clear Firestore (dangerous)

```bash
python backend/clear_firestore.py
```

### Test Geolocation Agent (requires Maps API key)

```bash
python backend/agents/geolocation/test_geolocation.py
```

---

### Future Work

- Integrate additional data sources for other threats (e.g. civil unrest, pandemics, violence).
- Build a user-friendly frontend interface for broader accessibility.