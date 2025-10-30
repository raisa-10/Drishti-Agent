"""
Project Drishti - Firebase Service
Handles all Firebase operations including Firestore, Storage, and FCM
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, storage, messaging
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud import firestore as gfirestore

logger = logging.getLogger(__name__)

class FirebaseService:
    """
    Centralized Firebase service for all database operations
    """
    
    def __init__(self):
        """Initialize Firebase connection"""
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                # Try to get credentials from environment or service account file
                cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    # Fallback to default credentials
                    cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'drishti-aegis-agent.appspot.com')
                })
            
            # Get Firestore client
            self.db = firestore.client()
            
            # Get Storage bucket
            self.bucket = storage.bucket()
            
            logger.info("✅ Firebase service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase: {e}")
            raise

    def get_server_timestamp(self):
        """Get server timestamp for consistent time handling"""
        return firestore.SERVER_TIMESTAMP

    # ===== DOCUMENT OPERATIONS =====

    def add_document(self, collection: str, data: Dict[str, Any], custom_id: Optional[str] = None) -> str:
        """
        Add a new document to a collection.
        If custom_id is provided, it uses that as the document ID.
        Otherwise, Firestore generates a random ID.
        """
        try:
            processed_data = self._process_data_for_firestore(data)
            
            collection_ref = self.db.collection(collection)
            
            if custom_id:
                # Use the provided custom ID
                doc_ref = collection_ref.document(custom_id)
                doc_ref.set(processed_data)
                doc_id = custom_id
            else:
                # Let Firestore generate an ID
                timestamp, doc_ref = collection_ref.add(processed_data)
                doc_id = doc_ref.id

            logger.info(f"Document added to {collection}: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document to {collection}: {e}")
            raise

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return self._process_data_from_firestore(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {doc_id} from {collection}: {e}")
            raise

    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing document"""
        try:
            processed_data = self._process_data_for_firestore(data)
            
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(processed_data)
            
            logger.info(f"Document updated in {collection}: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {doc_id} in {collection}: {e}")
            raise

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document"""
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            
            logger.info(f"Document deleted from {collection}: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from {collection}: {e}")
            raise

    # ===== COLLECTION OPERATIONS =====

    def get_collection(self, collection: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all documents from a collection"""
        try:
            query = self.db.collection(collection)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(self._process_data_from_firestore(data))
            
            logger.info(f"Retrieved {len(results)} documents from {collection}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get collection {collection}: {e}")
            raise

    def get_collection_with_filters(
        self, 
        collection: str, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Tuple[str, str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get documents with filters and ordering"""
        try:
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if isinstance(value, tuple) and len(value) == 2:
                        # Handle comparison operators like ('>=', datetime)
                        operator, filter_value = value
                        query = query.where(filter=FieldFilter(field, operator, filter_value))
                    else:
                        # Simple equality filter - use FieldFilter for new library
                        query = query.where(filter=FieldFilter(field, "==", value))
            
            # Apply ordering
            if order_by:
                field, direction = order_by
                if direction.lower() == 'desc':
                    query = query.order_by(field, direction=firestore.Query.DESCENDING)
                else:
                    query = query.order_by(field, direction=firestore.Query.ASCENDING)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(self._process_data_from_firestore(data))
            
            logger.info(f"Retrieved {len(results)} filtered documents from {collection}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get filtered collection {collection}: {e}")
            raise

    def listen_to_collection(
        self, 
        collection: str, 
        callback,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Set up real-time listener for collection changes"""
        try:
            query = self.db.collection(collection)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    query = query.where(field, '==', value)
            
            def on_snapshot(col_snapshot, changes, read_time):
                for change in changes:
                    doc_data = change.document.to_dict()
                    doc_data['id'] = change.document.id
                    
                    if change.type.name == 'ADDED':
                        callback('added', self._process_data_from_firestore(doc_data))
                    elif change.type.name == 'MODIFIED':
                        callback('modified', self._process_data_from_firestore(doc_data))
                    elif change.type.name == 'REMOVED':
                        callback('removed', self._process_data_from_firestore(doc_data))
            
            # Set up the listener
            listener = query.on_snapshot(on_snapshot)
            
            logger.info(f"Real-time listener set up for {collection}")
            return listener
            
        except Exception as e:
            logger.error(f"Failed to set up listener for {collection}: {e}")
            raise

    # ===== BATCH OPERATIONS =====

    def batch_write(self, operations: List[Tuple[str, str, str, Dict[str, Any]]]) -> bool:
        """Perform batch write operations"""
        try:
            batch = self.db.batch()
            
            for operation, collection, doc_id, data in operations:
                doc_ref = self.db.collection(collection).document(doc_id)
                processed_data = self._process_data_for_firestore(data)
                
                if operation == 'set':
                    batch.set(doc_ref, processed_data)
                elif operation == 'update':
                    batch.update(doc_ref, processed_data)
                elif operation == 'delete':
                    batch.delete(doc_ref)
            
            batch.commit()
            
            logger.info(f"Batch operation completed with {len(operations)} operations")
            return True
            
        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            raise

    # ===== STORAGE OPERATIONS =====

    def upload_file(self, file_path: str, blob_name: str) -> str:
        """Upload file to Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(file_path)
            
            # Make the blob publicly readable
            blob.make_public()
            
            logger.info(f"File uploaded to Storage: {blob_name}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise

    def upload_file_from_memory(self, file_data: bytes, blob_name: str, content_type: str = None) -> str:
        """Upload file from memory to Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_string(file_data)
            blob.make_public()
            
            logger.info(f"File uploaded from memory to Storage: {blob_name}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file from memory: {e}")
            raise

    def download_file(self, blob_name: str, destination_path: str) -> bool:
        """Download file from Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.download_to_filename(destination_path)
            
            logger.info(f"File downloaded from Storage: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file {blob_name}: {e}")
            raise

    def get_file_url(self, blob_name: str) -> Optional[str]:
        """Get public URL for a file in Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            
            if blob.exists():
                return blob.public_url
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get URL for {blob_name}: {e}")
            raise

    # ===== MESSAGING OPERATIONS =====

    def send_notification(
        self, 
        title: str, 
        body: str, 
        tokens: List[str] = None,
        topic: str = None,
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send push notification via FCM"""
        try:
            message_data = {
                'notification': messaging.Notification(
                    title=title,
                    body=body
                )
            }
            
            if data:
                message_data['data'] = data
            
            if tokens:
                # Send to specific tokens
                message_data['tokens'] = tokens
                message = messaging.MulticastMessage(**message_data)
                response = messaging.send_multicast(message)
                
                logger.info(f"Notification sent to {len(tokens)} tokens: {response.success_count} successful")
                
            elif topic:
                # Send to topic
                message_data['topic'] = topic
                message = messaging.Message(**message_data)
                response = messaging.send(message)
                
                logger.info(f"Notification sent to topic {topic}: {response}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise

    # ===== UTILITY METHODS =====

    def _process_data_for_firestore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data before storing in Firestore"""
        processed = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                processed[key] = value
            elif isinstance(value, dict):
                processed[key] = self._process_data_for_firestore(value)
            elif isinstance(value, list):
                processed[key] = [
                    self._process_data_for_firestore(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                processed[key] = value
        
        return processed

    def _process_data_from_firestore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data after retrieving from Firestore"""
        processed = {}
        
        for key, value in data.items():
            if hasattr(value, 'timestamp'):  # Firestore timestamp
                processed[key] = value.timestamp()
            elif isinstance(value, dict):
                processed[key] = self._process_data_from_firestore(value)
            elif isinstance(value, list):
                processed[key] = [
                    self._process_data_from_firestore(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                processed[key] = value
        
        return processed

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Firebase services"""
        try:
            # Test Firestore
            test_doc = self.db.collection('system').document('health_check')
            test_doc.set({'timestamp': self.get_server_timestamp()})
            
            # Test Storage
            storage_healthy = self.bucket.exists()
            
            return {
                'firestore': 'healthy',
                'storage': 'healthy' if storage_healthy else 'unhealthy',
                'overall': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'firestore': 'unhealthy',
                'storage': 'unknown',
                'overall': 'unhealthy',
                'error': str(e)
            }