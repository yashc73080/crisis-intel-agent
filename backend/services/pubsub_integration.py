"""
Google Cloud Pub/Sub Integration Module

This module provides Pub/Sub integration for event-driven architecture.
It enables real-time processing by publishing events when they're created
and triggering processing via subscriptions.

Setup:
1. Create a Pub/Sub topic: gcloud pubsub topics create crisis-events
2. Create a subscription: gcloud pubsub subscriptions create crisis-events-processor --topic=crisis-events
3. Set GOOGLE_CLOUD_PROJECT in your .env file
4. Run: python services/pubsub_processor.py

For production deployment:
- Deploy as a Cloud Run service or Cloud Function
- Configure Pub/Sub push subscription to your endpoint
- Enable autoscaling based on message queue depth
"""

import os
import json
import asyncio
from typing import Dict, Any
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(backend_dir)
load_dotenv(os.path.join(root_dir, ".env"))

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
TOPIC_NAME = os.getenv("PUBSUB_TOPIC_NAME", "crisis-events")
SUBSCRIPTION_NAME = os.getenv("PUBSUB_SUBSCRIPTION_NAME", "crisis-events-processor")


class PubSubPublisher:
    """Publishes events to Pub/Sub topic"""
    
    def __init__(self, project_id: str = PROJECT_ID, topic_name: str = TOPIC_NAME):
        """
        Initialize the Pub/Sub publisher.
        
        Args:
            project_id: Google Cloud project ID
            topic_name: Pub/Sub topic name
        """
        self.project_id = project_id
        self.topic_name = topic_name
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
    
    def publish_event(self, event_data: Dict[str, Any]) -> str:
        """
        Publish an event to Pub/Sub.
        
        Args:
            event_data: Event document to publish
            
        Returns:
            Message ID from Pub/Sub
        """
        try:
            # Convert event to JSON bytes
            message_data = json.dumps(event_data).encode("utf-8")
            
            # Add attributes for filtering
            attributes = {
                "event_type": str(event_data.get("type", "Unknown")),
                "source": str(event_data.get("source", "Unknown")),
                "status": str(event_data.get("status", "NEW"))
            }
            
            # Publish message
            future = self.publisher.publish(
                self.topic_path,
                data=message_data,
                **attributes
            )
            
            message_id = future.result()
            return message_id
            
        except Exception as e:
            print(f"Error publishing event: {e}")
            raise
    
    def publish_batch(self, events: list) -> list:
        """
        Publish multiple events to Pub/Sub.
        
        Args:
            events: List of event documents
            
        Returns:
            List of message IDs
        """
        message_ids = []
        for event in events:
            try:
                message_id = self.publish_event(event)
                message_ids.append(message_id)
            except Exception as e:
                print(f"Failed to publish event {event.get('event_id')}: {e}")
        
        return message_ids


class PubSubSubscriber:
    """Subscribes to Pub/Sub topic and processes events"""
    
    def __init__(self, project_id: str = PROJECT_ID, subscription_name: str = SUBSCRIPTION_NAME):
        """
        Initialize the Pub/Sub subscriber.
        
        Args:
            project_id: Google Cloud project ID
            subscription_name: Pub/Sub subscription name
        """
        self.project_id = project_id
        self.subscription_name = subscription_name
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(project_id, subscription_name)
    
    def process_message(self, message):
        """
        Process a single Pub/Sub message.
        
        Args:
            message: Pub/Sub message object
        """
        try:
            # Parse event data
            event_data = json.loads(message.data.decode("utf-8"))
            
            print(f"[RECEIVED] Event {event_data.get('event_id')} - {event_data.get('type')}")
            
            # TODO: Call Risk Assessment Agent here
            # This would be similar to the EventProcessor but triggered by Pub/Sub
            # For now, just acknowledge the message
            
            message.ack()
            print(f"[ACK] Message acknowledged")
            
        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")
            message.nack()  # Requeue message for retry
    
    def start_listening(self):
        """Start listening for messages"""
        print(f"Listening for messages on {self.subscription_path}...")
        print("Press Ctrl+C to stop\n")
        
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.process_message
        )
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print("\n\nSubscriber stopped")


# Integration with Data Collector Agent
def create_pubsub_enabled_saver():
    """
    Returns a save function that persists to Firestore AND publishes to Pub/Sub.
    
    Usage in data_collector/main.py:
        from services.pubsub_integration import create_pubsub_enabled_saver
        
        publisher = PubSubPublisher()
        
        def save_event_to_firestore(event_data):
            # ... existing Firestore save logic ...
            doc_id = doc_ref.id
            
            # Publish to Pub/Sub
            try:
                event_data_with_id = event_data.copy()
                event_data_with_id["_doc_id"] = doc_id
                publisher.publish_event(event_data_with_id)
            except Exception as e:
                print(f"Warning: Failed to publish to Pub/Sub: {e}")
            
            return doc_id
    """
    publisher = PubSubPublisher()
    
    def save_and_publish(event_data: Dict[str, Any], firestore_save_func) -> str:
        """
        Save to Firestore and publish to Pub/Sub.
        
        Args:
            event_data: Event to save
            firestore_save_func: Original Firestore save function
            
        Returns:
            Document ID
        """
        # Save to Firestore first
        doc_id = firestore_save_func(event_data)
        
        # Publish to Pub/Sub
        try:
            event_with_id = event_data.copy()
            event_with_id["_doc_id"] = doc_id
            publisher.publish_event(event_with_id)
            print(f"Published event {event_data.get('event_id')} to Pub/Sub")
        except Exception as e:
            print(f"Warning: Failed to publish to Pub/Sub: {e}")
        
        return doc_id
    
    return save_and_publish


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pubsub_integration.py listen    # Start subscriber")
        print("  python pubsub_integration.py test      # Publish test message")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "listen":
        subscriber = PubSubSubscriber()
        subscriber.start_listening()
    
    elif command == "test":
        publisher = PubSubPublisher()
        
        test_event = {
            "event_id": "test_001",
            "type": "Test",
            "location": "Test Location",
            "description": "Test event for Pub/Sub",
            "timestamp": "2025-11-29T00:00:00Z",
            "source": "TEST",
            "status": "NEW"
        }
        
        print("Publishing test event...")
        message_id = publisher.publish_event(test_event)
        print(f"Published with message ID: {message_id}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
