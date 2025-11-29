"""
Test Firestore connectivity and permissions
"""
import os
import sys
from dotenv import load_dotenv
from google.cloud import firestore

# Load environment variables
load_dotenv()

def test_firestore_connection():
    """Test Firestore connection and write permissions"""
    print("Testing Firestore Connection...")
    print("=" * 60)
    
    # Check environment variables
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"Project ID: {project_id or 'NOT SET'}")
    print(f"Credentials: {creds_path or 'NOT SET'}")
    
    if not project_id:
        print("\n✗ ERROR: GCP_PROJECT_ID not set in .env")
        return False
    
    if not creds_path:
        print("\n✗ ERROR: GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.path.exists(creds_path):
        print(f"\n✗ ERROR: Credentials file not found: {creds_path}")
        return False
    
    print("\n✓ Environment variables configured")
    
    # Try to initialize Firestore
    try:
        db = firestore.Client()
        print("✓ Firestore client initialized")
    except Exception as e:
        print(f"\n✗ ERROR: Failed to initialize Firestore client: {e}")
        return False
    
    # Try to write a test document
    try:
        test_collection = "crisis_events_test"
        test_doc_id = "test_doc_123"
        
        doc_ref = db.collection(test_collection).document(test_doc_id)
        doc_ref.set({
            "test": "data",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
        print(f"✓ Successfully wrote test document to {test_collection}/{test_doc_id}")
        
        # Read it back
        doc = doc_ref.get()
        if doc.exists:
            print(f"✓ Successfully read test document: {doc.to_dict()}")
        
        # Clean up
        doc_ref.delete()
        print("✓ Test document deleted")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to write to Firestore: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_firestore_connection()
    sys.exit(0 if success else 1)
