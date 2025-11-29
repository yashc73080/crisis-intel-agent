# Services - Decoupled Architecture Components

This directory contains background services that enable continuous monitoring and event-driven processing.

## Services Overview

### 1. `event_processor.py` - Event Processing Service

**Purpose**: Monitors Firestore for new events and triggers risk assessment.

**How it works**:
1. Polls Firestore every 30 seconds (configurable)
2. Queries for events with `status=NEW`
3. Calls Risk Assessment Agent for each event
4. Updates event with risk assessment results
5. Changes status to `ASSESSED` or `ERROR`

**Usage**:
```bash
# Run with defaults
python services/event_processor.py

# Configure via environment
export EVENT_PROCESSOR_POLL_INTERVAL=60
python services/event_processor.py
```

**Configuration**:
- `EVENT_PROCESSOR_POLL_INTERVAL` - Polling interval in seconds (default: 30)

---

### 2. `data_collector_scheduler.py` - Data Collection Scheduler

**Purpose**: Periodically fetches disaster data from external sources.

**How it works**:
1. Runs collection cycle every 5 minutes (configurable)
2. Calls Data Collection Agent for each configured source
3. Events are automatically persisted to Firestore
4. Logs summary of collection results

**Usage**:
```bash
# Run with defaults (GDACS only)
python services/data_collector_scheduler.py

# Configure via environment
export DATA_SOURCES=GDACS,USGS
export COLLECTION_INTERVAL=600
python services/data_collector_scheduler.py
```

**Configuration**:
- `DATA_SOURCES` - Comma-separated list of sources (default: GDACS)
- `COLLECTION_INTERVAL` - Collection interval in seconds (default: 300)

---

### 3. `pubsub_integration.py` - Google Cloud Pub/Sub Integration

**Purpose**: Provides event-driven processing alternative to polling.

**Components**:
- `PubSubPublisher` - Publishes events to Pub/Sub topic
- `PubSubSubscriber` - Subscribes and processes messages

**Setup**:
```bash
# Create Pub/Sub resources
gcloud pubsub topics create crisis-events
gcloud pubsub subscriptions create crisis-events-processor --topic=crisis-events
```

**Usage**:
```bash
# Start subscriber (processes events in real-time)
python services/pubsub_integration.py listen

# Test publishing
python services/pubsub_integration.py test
```

**Configuration**:
- `PUBSUB_TOPIC_NAME` - Topic name (default: crisis-events)
- `PUBSUB_SUBSCRIPTION_NAME` - Subscription name (default: crisis-events-processor)

**Integration**:
To enable Pub/Sub in Data Collection Agent, modify `save_event_to_firestore()`:
```python
from services.pubsub_integration import PubSubPublisher

publisher = PubSubPublisher()

def save_event_to_firestore(event_data):
    # ... save to Firestore ...
    doc_id = doc_ref.id
    
    # Publish to Pub/Sub
    event_data_with_id = event_data.copy()
    event_data_with_id["_doc_id"] = doc_id
    publisher.publish_event(event_data_with_id)
    
    return doc_id
```

---

## Running Services Together

### Development/Testing (Polling)
```bash
# Terminal 1: Data Collection
python services/data_collector_scheduler.py

# Terminal 2: Event Processing
python services/event_processor.py
```

### Production (Pub/Sub)
```bash
# Terminal 1: Data Collection (publishes to Pub/Sub)
python services/data_collector_scheduler.py

# Terminal 2: Event Processing (subscribes to Pub/Sub)
python services/pubsub_integration.py listen
```

---

## Service Monitoring

### Check Service Health

**Data Collector Scheduler**:
- Look for: "Starting collection cycle" every N minutes
- Check: "Total events saved" count

**Event Processor**:
- Look for: "Found X new event(s)" messages
- Check: "Processed X/Y events successfully"

### Check Firestore
```bash
# Via gcloud CLI
gcloud firestore collections list

# Via Console
https://console.cloud.google.com/firestore
```

### Check Pub/Sub (if enabled)
```bash
# List topics
gcloud pubsub topics list

# List subscriptions
gcloud pubsub subscriptions list

# View metrics
gcloud monitoring dashboards list
```

---

## Troubleshooting

### Event Processor not finding events
1. Check Data Collector is running and saving events
2. Verify Firestore has documents with `status=NEW`
3. Check GCP credentials and project ID

### Data Collector not fetching data
1. Check internet connection
2. Verify external API endpoints are accessible
3. Check source configuration (GDACS, USGS, etc.)

### Pub/Sub messages not received
1. Verify topic and subscription exist
2. Check IAM permissions for Pub/Sub
3. Verify publisher is enabled in Data Collector

### High costs
1. Increase polling intervals:
   - `COLLECTION_INTERVAL=600` (10 minutes)
   - `EVENT_PROCESSOR_POLL_INTERVAL=60` (1 minute)
2. Switch to Pub/Sub for production efficiency
3. Limit data sources to only needed feeds

---

## Production Deployment

### Deploy to Cloud Run

**Event Processor**:
```dockerfile
# Dockerfile.processor
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "services/event_processor.py"]
```

```bash
docker build -t gcr.io/YOUR_PROJECT/event-processor -f Dockerfile.processor .
docker push gcr.io/YOUR_PROJECT/event-processor

gcloud run deploy event-processor \
  --image gcr.io/YOUR_PROJECT/event-processor \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --timeout 3600
```

**Data Collector**:
```bash
# Use Cloud Scheduler to trigger
gcloud scheduler jobs create http collect-data \
  --schedule="*/5 * * * *" \
  --uri="https://YOUR_SERVICE_URL/collect" \
  --http-method=POST
```

### Deploy with Pub/Sub

```bash
# Event Processor with Pub/Sub trigger
gcloud run deploy event-processor \
  --image gcr.io/YOUR_PROJECT/event-processor \
  --platform managed \
  --trigger-topic crisis-events \
  --memory 512Mi
```

---

## Architecture Benefits

| Feature | Polling (Current) | Pub/Sub (Production) |
|---------|-------------------|----------------------|
| Latency | 30 seconds | <1 second |
| Scaling | Manual | Automatic |
| Cost | Predictable | Pay per message |
| Complexity | Simple | Moderate |
| Best For | Development | Production |

---

## Next Steps

1. **Test services locally**: Run both services and verify events flow through
2. **Monitor Firestore**: Check event status transitions
3. **Set up Pub/Sub**: For production deployment
4. **Deploy to Cloud Run**: For 24/7 operation
5. **Add monitoring**: Set up Cloud Monitoring dashboards
6. **Add alerting**: Configure alerts for high-risk events

---

## Additional Resources

- [Google Cloud Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
