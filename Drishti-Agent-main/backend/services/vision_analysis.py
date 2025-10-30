"""
Project Drishti - Vision Analysis Service
Handles video analysis using Google Cloud Vision API
"""
import os
import cv2
import logging
from typing import Dict, List
import numpy as np

# Google Cloud imports
from google.cloud import vision
from google.cloud import storage
import vertexai

from utils.data_models import VideoAnalysisResult, IncidentType, SeverityLevel

logger = logging.getLogger(__name__)

class VisionAnalysisService:
    """
    Simplified and robust video analysis service using only Google Cloud Vision API.
    """

    def __init__(self):
        """Initialize Vision Analysis service"""
        try:
            # Initialize Vertex AI - needed for project context
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT') # Use the standard GOOGLE_CLOUD_PROJECT
            if not project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set.")
            vertexai.init(project=project_id, location=os.getenv('VERTEX_AI_REGION', 'us-central1'))

            # Initialize Vision API client for image analysis
            self.vision_client = vision.ImageAnnotatorClient()
            # Initialize Storage client for GCS video access
            self.storage_client = storage.Client()

            self.suspicious_keywords = [
                'weapon', 'gun', 'knife', 'fight', 'riot', 'protest', 'violence'
            ]
            self.emergency_keywords = [
                'fire', 'smoke', 'flame', 'ambulance', 'paramedic', 'injury', 'evacuation', 'accident', 'fallen person'
            ]
            logger.info("✅ Vision Analysis service initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vision Analysis Service: {e}")
            raise

    async def analyze_video_for_anomalies(
        self,
        video_path: str,
        detection_types: List[str] = None
    ) -> Dict[str, any]:
        """
        Main method to analyze video for anomalies by processing its frames.
        """
        try:
            logger.info(f"Starting video analysis for: {video_path}")
            # Extract a few representative frames from the video
            frames = await self._extract_video_frames(video_path, max_frames=5)
            if not frames:
                raise ValueError("Could not extract any frames from the video.")

            # Analyze the most representative frame (e.g., the middle one)
            # For a hackathon, analyzing one high-quality frame is faster and more reliable than many.
            middle_frame_index = len(frames) // 2
            target_frame = frames[middle_frame_index]

            # Convert frame to bytes for the API call
            image_bytes = self._frame_to_bytes(target_frame)

            # Perform a comprehensive analysis on the single frame
            analysis_result = await self._analyze_single_frame(image_bytes)

            logger.info(f"Video analysis completed for: {video_path}")
            return analysis_result.dict()

        except Exception as e:
            logger.error(f"Video analysis failed for {video_path}: {e}", exc_info=True)
            # Return a structured error response
            return VideoAnalysisResult(
                anomaly_detected=False,
                description=f"Error during analysis: {e}",
                severity=SeverityLevel.LOW,
                anomaly_type=None, # Explicitly set to None on error
                confidence=0.0,
                detected_objects=[]
            ).dict()

    async def _analyze_single_frame(self, image_bytes: bytes) -> VideoAnalysisResult:
        """
        Analyzes a single image using multiple features of the Vision API.
        This is the core analysis function.
        """
        image = vision.Image(content=image_bytes)

        # Define the features we want to request from the Vision API in one go
        features = [
            {"type_": vision.Feature.Type.OBJECT_LOCALIZATION},
            {"type_": vision.Feature.Type.LABEL_DETECTION, "max_results": 20},
        ]
        request = {"image": image, "features": features}

        # Make a single, efficient API call
        response = self.vision_client.annotate_image(request=request)

        if response.error.message:
            raise Exception(f"Vision API returned an error: {response.error.message}")

        # Extract results
        objects = response.localized_object_annotations
        labels = response.label_annotations

        # --- ANOMALY DETECTION LOGIC ---
        detected_objects_info = [{"name": obj.name.lower(), "score": obj.score} for obj in objects]
        detected_labels_info = [{"name": lbl.description.lower(), "score": lbl.score} for lbl in labels]

        # Combine all detected terms
        all_terms = detected_objects_info + detected_labels_info

        # 1. Check for Emergencies (highest priority)
        for term in all_terms:
            if any(keyword in term["name"] for keyword in self.emergency_keywords):
                return VideoAnalysisResult(
                    anomaly_detected=True,
                    anomaly_type=self._get_emergency_type(term["name"]),
                    confidence=term["score"],
                    description=f"Emergency situation detected: {term['name'].title()}.",
                    severity=self._determine_severity(term["score"], is_emergency=True),
                    detected_objects=self._format_objects(objects)
                )

        # 2. Check for Suspicious Activity
        for term in all_terms:
            if any(keyword in term["name"] for keyword in self.suspicious_keywords):
                return VideoAnalysisResult(
                    anomaly_detected=True,
                    anomaly_type=IncidentType.SUSPICIOUS_ACTIVITY,
                    confidence=term["score"],
                    description=f"Suspicious activity detected: {term['name'].title()}.",
                    severity=self._determine_severity(term["score"]),
                    detected_objects=self._format_objects(objects)
                )

        # 3. Check for Crowd Density
        person_count = sum(1 for obj in objects if obj.name.lower() in ['person', 'man', 'woman'])
        # A simple density check: >10 people detected is considered a high-density crowd for this demo
        if person_count > 2:
            crowd_confidence = max([obj.score for obj in objects if obj.name.lower() in ['person', 'man', 'woman']], default=0.5)
            return VideoAnalysisResult(
                anomaly_detected=True,
                anomaly_type=IncidentType.CROWD_SURGE,
                confidence=crowd_confidence,
                description=f"High crowd density detected with approximately {person_count} people visible.",
                severity=self._determine_severity(crowd_confidence, person_count=person_count),
                crowd_density=float(person_count), # Use person count as a proxy for density
                detected_objects=self._format_objects(objects)
            )

        # If no anomalies are found
        return VideoAnalysisResult(
            anomaly_detected=False,
            description="Normal activity detected. No specific anomalies found.",
            severity=SeverityLevel.LOW,
            anomaly_type=None,
            confidence=1.0, # High confidence in "normal"
            detected_objects=self._format_objects(objects)
        )

    async def _extract_video_frames(self, video_path: str, max_frames: int) -> List[np.ndarray]:
        """Extracts frames from a local or GCS video path."""
        path_to_process = video_path
        if video_path.startswith('gs://'):
            path_to_process = await self._download_video_from_gcs(video_path)

        cap = cv2.VideoCapture(path_to_process)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")

        frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames < 1:
            cap.release()
            return []
            
        frame_indices = [int(i * total_frames / max_frames) for i in range(max_frames)]

        for i in sorted(list(set(frame_indices))):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        cap.release()
        logger.info(f"Extracted {len(frames)} frames from video.")
        return frames

    def _frame_to_bytes(self, frame: np.ndarray) -> bytes:
        """Converts an OpenCV frame (numpy array) to JPEG bytes."""
        is_success, buffer = cv2.imencode(".jpg", frame)
        if not is_success:
            raise ValueError("Could not encode frame to JPG")
        return buffer.tobytes()

    async def _download_video_from_gcs(self, gcs_path: str) -> str:
        """Downloads a video from GCS to a temporary local path."""
        try:
            bucket_name, blob_name = gcs_path.replace("gs://", "").split("/", 1)
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Create a temporary file path
            local_path = f"/tmp/{os.path.basename(blob_name)}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            blob.download_to_filename(local_path)
            logger.info(f"Downloaded GCS file {gcs_path} to {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"GCS download failed for {gcs_path}: {e}")
            raise

    def _determine_severity(self, confidence: float, is_emergency: bool = False, person_count: int = 0) -> SeverityLevel:
        """Determines the severity of an incident."""
        if is_emergency and confidence > 0.6:
            return SeverityLevel.CRITICAL
        if person_count > 20:
             return SeverityLevel.HIGH
        if confidence > 0.8:
            return SeverityLevel.HIGH
        if confidence > 0.6:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    def _get_emergency_type(self, term_name: str) -> IncidentType:
        """Categorizes an emergency based on the detected term."""
        if any(keyword in term_name for keyword in ['fire', 'smoke']):
            return IncidentType.FIRE_HAZARD
        if any(keyword in term_name for keyword in ['ambulance', 'injury', 'fallen person']):
            return IncidentType.MEDICAL_EMERGENCY
        return IncidentType.EMERGENCY_SITUATION

    def _format_objects(self, object_annotations) -> List[Dict]:
        """Formats the Vision API object annotations into a simpler dictionary."""
        return [
            {
                "name": obj.name,
                "confidence": obj.score,
            }
            for obj in object_annotations
        ]