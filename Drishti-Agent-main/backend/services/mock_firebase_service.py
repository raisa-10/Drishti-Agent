"""
Project Drishti - Mock Firebase Service for Development
Provides the same interface as Firebase service but uses in-memory storage
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MockFirebaseService:
    """
    Mock Firebase service for development without external dependencies
    """
    
    def __init__(self):
        """Initialize mock Firebase connection"""
        try:
            # In-memory storage
            self.collections = {
                "incidents": [],
                "alerts": [],
                "security_units": [
                    {
                        "id": "unit-001",
                        "type": "security_patrol",
                        "status": "available",
                        "location": {"lat": 40.7589, "lng": -73.9851},
                        "assigned_area": "main_entrance"
                    },
                    {
                        "id": "unit-002", 
                        "type": "emergency_response",
                        "status": "busy",
                        "location": {"lat": 40.7614, "lng": -73.9776},
                        "assigned_area": "food_court"
                    }
                ],
                "chat_history": [],
                "system": []
            }
            
            logger.info("✅ Mock Firebase service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Mock Firebase: {e}")
            raise

    def get_server_timestamp(self):
        """Get server timestamp for consistent time handling"""
        return datetime.now().isoformat()

    # ===== DOCUMENT OPERATIONS =====

    def add_document(self, collection: str, data: Dict[str, Any], custom_id: Optional[str] = None) -> str:
        """Add a new document to collection"""
        try:
            # Generate a unique ID or use custom_id
            doc_id = custom_id or str(uuid.uuid4())
            
            # Process the data
            processed_data = data.copy()
            processed_data["id"] = doc_id
            processed_data["created_at"] = datetime.now().isoformat()
            
            # Add to in-memory collection
            if collection not in self.collections:
                self.collections[collection] = []
            
            self.collections[collection].append(processed_data)
            
            logger.info(f"Document added to {collection}: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document to {collection}: {e}")
            raise

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        try:
            if collection not in self.collections:
                return None
                
            for doc in self.collections[collection]:
                if doc.get("id") == doc_id:
                    return doc
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from {collection}: {e}")
            return None

    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document"""
        try:
            if collection not in self.collections:
                return False
                
            for i, doc in enumerate(self.collections[collection]):
                if doc.get("id") == doc_id:
                    # Update the document
                    self.collections[collection][i].update(data)
                    self.collections[collection][i]["updated_at"] = datetime.now().isoformat()
                    logger.info(f"Document {doc_id} updated in {collection}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update document {doc_id} in {collection}: {e}")
            return False

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document"""
        try:
            if collection not in self.collections:
                return False
                
            for i, doc in enumerate(self.collections[collection]):
                if doc.get("id") == doc_id:
                    del self.collections[collection][i]
                    logger.info(f"Document {doc_id} deleted from {collection}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from {collection}: {e}")
            return False

    # ===== COLLECTION OPERATIONS =====

    def get_collection(self, collection: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all documents from a collection"""
        try:
            if collection not in self.collections:
                return []
            
            return self.collections[collection][:limit]
            
        except Exception as e:
            logger.error(f"Failed to get collection {collection}: {e}")
            return []

    def get_collection_with_filters(
        self, 
        collection: str, 
        filters: Dict[str, Any] = None,
        limit: int = 100,
        order_by: Tuple[str, str] = None
    ) -> List[Dict[str, Any]]:
        """Get collection with filters"""
        try:
            if collection not in self.collections:
                return []
            
            docs = self.collections[collection]
            
            # Apply filters
            if filters:
                filtered_docs = []
                for doc in docs:
                    match = True
                    for key, value in filters.items():
                        if key not in doc or doc[key] != value:
                            match = False
                            break
                    if match:
                        filtered_docs.append(doc)
                docs = filtered_docs
            
            # Apply ordering (simple implementation)
            if order_by:
                field, direction = order_by
                reverse = direction.lower() == "desc"
                docs = sorted(docs, key=lambda x: x.get(field, ""), reverse=reverse)
            
            return docs[:limit]
            
        except Exception as e:
            logger.error(f"Failed to query collection {collection}: {e}")
            return []

    def count_documents(self, collection: str, filters: Dict[str, Any] = None) -> int:
        """Count documents in collection with optional filters"""
        try:
            docs = self.get_collection_with_filters(collection, filters)
            return len(docs)
            
        except Exception as e:
            logger.error(f"Failed to count documents in {collection}: {e}")
            return 0

    # ===== BATCH OPERATIONS =====

    def batch_write(self, operations: List[Dict[str, Any]]) -> bool:
        """Perform batch write operations"""
        try:
            for operation in operations:
                op_type = operation.get("type")
                collection = operation.get("collection")
                doc_id = operation.get("doc_id")
                data = operation.get("data", {})
                
                if op_type == "add":
                    self.add_document(collection, data)
                elif op_type == "update":
                    self.update_document(collection, doc_id, data)
                elif op_type == "delete":
                    self.delete_document(collection, doc_id)
            
            logger.info(f"Batch write completed: {len(operations)} operations")
            return True
            
        except Exception as e:
            logger.error(f"Batch write failed: {e}")
            return False

    # ===== STORAGE OPERATIONS (Mock) =====

    def upload_file(self, file_path: str, destination: str) -> str:
        """Mock file upload"""
        try:
            # In a real implementation, this would upload to Firebase Storage
            # For mock, we'll just return a fake URL
            fake_url = f"https://mock-storage.example.com/{destination}"
            logger.info(f"Mock file upload: {file_path} -> {fake_url}")
            return fake_url
            
        except Exception as e:
            logger.error(f"Mock file upload failed: {e}")
            raise

    def download_file(self, file_path: str, destination: str) -> bool:
        """Mock file download"""
        try:
            # Mock implementation
            logger.info(f"Mock file download: {file_path} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Mock file download failed: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """Mock file deletion"""
        try:
            logger.info(f"Mock file deletion: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Mock file deletion failed: {e}")
            return False
