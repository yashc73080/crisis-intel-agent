"""
Clear Firestore Collection

This script deletes all documents from the crisis_events collection.
USE WITH CAUTION - This is irreversible!
"""

import os
from dotenv import load_dotenv
from google.cloud import firestore

# Load environment variables
load_dotenv()

def clear_collection(collection_name: str, batch_size: int = 500):
    """
    Delete all documents in a Firestore collection.
    
    Args:
        collection_name: Name of the collection to clear
        batch_size: Number of documents to delete per batch
    """
    db = firestore.Client()
    coll_ref = db.collection(collection_name)
    
    deleted = 0
    
    while True:
        # Get a batch of documents
        docs = coll_ref.limit(batch_size).stream()
        docs_list = list(docs)
        
        if not docs_list:
            break
        
        # Delete in batches
        batch = db.batch()
        for doc in docs_list:
            batch.delete(doc.reference)
            deleted += 1
        
        batch.commit()
        print(f"Deleted {deleted} documents so far...")
    
    return deleted


if __name__ == "__main__":
    collection_name = "crisis_events"
    
    print(f"\n{'='*60}")
    print(f"WARNING: This will delete ALL documents in '{collection_name}'")
    print(f"{'='*60}\n")
    
    confirm = input("Type 'DELETE' to confirm: ").strip()
    
    if confirm != "DELETE":
        print("\nCancelled. No documents were deleted.")
    else:
        print(f"\nDeleting all documents from '{collection_name}'...")
        total = clear_collection(collection_name)
        print(f"\n✓ Successfully deleted {total} document(s)")
