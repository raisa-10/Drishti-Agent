import cv2
import os
import time
import requests
import uuid
from ultralytics import YOLO
import numpy as np
from dotenv import load_dotenv
from collections import deque
import math
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, firestore

# --- Configuration ---
load_dotenv()

# --- NEW: Location Configuration for this specific camera/video ---
# This data should match the camera's real-world location.
# It will be sent to the backend with every anomaly trigger.
LOCATION_DATA = {
    "name": "Main Stage Area",
    "latitude": 13.0603,
    "longitude": 77.4744
}

# Backend API endpoint URL
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://127.0.0.1:8000/api/v1/trigger-anomaly')
VIDEO_SOURCE = os.getenv('VIDEO_SOURCE', '0')  # Use '0' for webcam, or path to video file
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
if not GCS_BUCKET_NAME:
    raise ValueError("CRITICAL: GCS_BUCKET_NAME is not set in your .env file. This is required for uploading clips.")

CLIP_DURATION_SECONDS = 10  # Record 10-second clips for anomalies
VIDEO_FPS = 10  # Process at 10 FPS for efficiency
MIN_DETECTION_CONFIDENCE = 0.80
YOLO_MODEL = YOLO('yolov8n.pt')

# --- Video Clip Recording Config ---
FRAME_BUFFER_SIZE = VIDEO_FPS * CLIP_DURATION_SECONDS  # Keep buffer of recent frames
COOLDOWN_PERIOD_SECONDS = 30  # Wait before reporting same anomaly type again

# --- Existing Anomaly Detection Criteria ---
# Unattended Objects
UNATTENDED_OBJECT_CLASSES = ['backpack', 'suitcase', 'handbag']
UNATTENDED_THRESHOLD_SECONDS = 5
PERSON_PROXIMITY_THRESHOLD_PX = 100

# Crowd Density
CROWD_DENSITY_ZONE_THRESHOLD = 2
CROWD_DENSITY_ROI_NORMALIZED = (0.2, 0.5, 0.8, 0.9)

# Fall Detection
FALL_ASPECT_RATIO_THRESHOLD = 1.2
FALL_RATIO_CHANGE_THRESHOLD = 0.5
FALL_DETECTION_WINDOW_FRAMES = 5

# Object Tracking Configuration
OBJECT_TRACKING_MAX_DISTANCE_PX = 75
OBJECT_TRACKING_GRACE_PERIOD_SECONDS = 2

# --- NEW: Additional Anomaly Detection Criteria ---

# Loitering Detection
LOITERING_THRESHOLD_SECONDS = 60
STATIONARY_MOVEMENT_THRESHOLD_PX = 15
STATIONARY_CHECK_WINDOW_FRAMES = 10

# Wrong-Way Detection - REMOVED

# Fighting Detection
FIGHTING_PROXIMITY_THRESHOLD_PX = 50
FIGHTING_VELOCITY_THRESHOLD = 30
FIGHTING_DISTANCE_CHANGE_THRESHOLD = 25
FIGHTING_SCORE_THRESHOLD = 100
FIGHTING_DETECTION_WINDOW_FRAMES = 15

# Asset Removal Detection
CRITICAL_ASSETS = {
    "fire_extinguisher_1": {
        "roi": (0.05, 0.1, 0.15, 0.3),  # normalized coordinates
        "class_name": "fire extinguisher",
        "present": None  # Will be set during initialization
    },
    "emergency_exit_sign": {
        "roi": (0.85, 0.05, 0.95, 0.15),
        "class_name": "sign",
        "present": None
    }
}
ASSET_MISSING_THRESHOLD_SECONDS = 10

# --- State Management ---
reported_anomalies = {
    "crowd_density": False
}

# Video clip recording state
frame_buffer = deque(maxlen=FRAME_BUFFER_SIZE)
last_anomaly_timestamps = {}
gcs_storage_client = storage.Client()

# --- NEW: Stateful Anomaly Tracking ---
active_anomalies = {}  # Tracks currently active anomalies to prevent re-triggering
ANOMALY_STATE_CHECK_INTERVAL = 60  # Check Firebase for resolved incidents every 60 seconds
last_state_check = 0

# --- Firebase Initialization for Stateful Alerts ---
db = None
try:
    if not firebase_admin._apps:
        # Use default credentials (gcloud auth or service account)
        firebase_admin.initialize_app()
    db = firestore.client()
    print("[✅] Firebase initialized successfully for stateful anomaly tracking.")
except Exception as e:
    print(f"[⚠️] WARNING: Could not initialize Firebase for stateful tracking: {e}")
    print("[INFO] Continuing with basic anomaly detection (no state management)")
    db = None

# Frame count for processing
frame_count = 0

# --- Helper Functions ---

def is_anomaly_active_in_backend(anomaly_type: str) -> bool:
    """
    Intelligent anomaly state checking to prevent alert spam.
    Combines local state tracking with optional Firebase backend checks.
    """
    # First check local state for immediate response
    if active_anomalies.get(anomaly_type, False):
        return True
    
    # If Firebase is available, periodically check for resolved incidents
    global last_state_check
    current_time = time.time()
    
    if db and (current_time - last_state_check) > ANOMALY_STATE_CHECK_INTERVAL:
        try:
            # Check for active incidents of this type from this camera
            camera_id = os.getenv('CAMERA_ID', 'EdgeCam-01')
            incidents_ref = db.collection('incidents')
            
            # Query for recent active incidents (simplified for hackathon)
            # In production, you'd use compound indexes for complex queries
            docs = incidents_ref.where('type', '==', anomaly_type).limit(10).get()
            
            # Check if any recent incidents from this camera are still active
            for doc in docs:
                incident_data = doc.to_dict()
                if (incident_data.get('cameraId') == camera_id and 
                    incident_data.get('status') == 'active' and
                    (current_time - incident_data.get('timestamp', 0)) < 600):  # 10 minutes
                    print(f"[INFO] Found active incident in Firebase for {anomaly_type}")
                    active_anomalies[anomaly_type] = True
                    return True
            
            last_state_check = current_time
        except Exception as e:
            print(f"[WARN] Could not check Firebase for incident status: {e}")
    
    return False

def check_and_resolve_anomalies():
    """
    Periodically checks if anomalies have been resolved in the backend
    and updates local state accordingly.
    """
    global active_anomalies, last_state_check
    current_time = time.time()
    
    if db and (current_time - last_state_check) > ANOMALY_STATE_CHECK_INTERVAL:
        try:
            camera_id = os.getenv('CAMERA_ID', 'EdgeCam-01')
            incidents_ref = db.collection('incidents')
            
            # Check status of our currently tracked active anomalies
            for anomaly_type in list(active_anomalies.keys()):
                if active_anomalies[anomaly_type]:  # If we think it's active
                    # Check if it's been resolved in Firebase
                    docs = incidents_ref.where('type', '==', anomaly_type).limit(5).get()
                    
                    all_resolved = True
                    for doc in docs:
                        incident_data = doc.to_dict()
                        if (incident_data.get('cameraId') == camera_id and 
                            incident_data.get('status') == 'active' and
                            (current_time - incident_data.get('timestamp', 0)) < 600):
                            all_resolved = False
                            break
                    
                    if all_resolved:
                        print(f"[✅] Anomaly '{anomaly_type}' has been resolved. Resuming alerts.")
                        active_anomalies[anomaly_type] = False
            
            last_state_check = current_time
        except Exception as e:
            print(f"[WARN] Could not check resolution status: {e}")

def upload_clip_to_gcs(local_path: str, destination_blob_name: str) -> str:
    """Uploads a video clip to Google Cloud Storage and returns the GCS path."""
    try:
        bucket = gcs_storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        gcs_path = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        print(f"[+] Successfully uploaded clip to {gcs_path}")
        return gcs_path
    except Exception as e:
        print(f"[X] ERROR: Failed to upload clip to GCS: {e}")
        return None
    finally:
        # Clean up the local clip file
        if os.path.exists(local_path):
            os.remove(local_path)

def save_clip_from_buffer(buffer, output_path, fps, frame_size):
    """Saves the frames in the buffer to a video file."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
    for frame in buffer:
        out.write(frame)
    out.release()
    print(f"[INFO] Anomaly clip saved to {output_path}")

def trigger_backend_analysis(anomaly_data):
    """Sends anomaly data to the backend API with intelligent state management."""
    anomaly_type = anomaly_data.get('anomalyType', 'Generic Anomaly')
    current_time = time.time()
    
    # STATEFUL CHECK: Don't trigger if this anomaly type is already active
    if is_anomaly_active_in_backend(anomaly_type):
        print(f"[🔄] Anomaly '{anomaly_type}' is already active. Suppressing duplicate alert to prevent spam.")
        return False
    
    # Check cooldown for this specific anomaly type (additional protection)
    if current_time - last_anomaly_timestamps.get(anomaly_type, 0) < COOLDOWN_PERIOD_SECONDS:
        print(f"[⏱️] Skipping trigger for {anomaly_type} due to cooldown period.")
        return False
    
    print(f"\n[🚨] NEW ANOMALY DETECTED: {anomaly_type}")
    print(f"[📹] Initiating clip recording and backend analysis...")
    
    # If this anomaly should trigger clip recording, check if we have a GCS path
    if anomaly_data.get('record_clip', False):
        gcs_path = record_and_upload_clip(anomaly_type)
        if not gcs_path:
            print(f"[❌] Failed to record/upload clip for {anomaly_type}, skipping backend trigger")
            return False
        anomaly_data['sourceVideo'] = gcs_path
    
    # Add the standard data the backend expects to every payload.
    full_payload = {
        "anomalyId": anomaly_data.get("anomalyId", f"edge-anomaly-{uuid.uuid4()}"),
        "anomalyType": anomaly_type,
        "details": anomaly_data.get("details", "No details provided."),
        "timestamp": current_time,
        
        # --- Standard fields the backend requires for deep analysis ---
        "sourceVideo": anomaly_data.get("sourceVideo", "live_stream"),
        "cameraId": os.getenv('CAMERA_ID', 'EdgeCam-01'),
        "location": LOCATION_DATA
    }
    
    print(f"    📤 Payload: {full_payload}")
    try:
        response = requests.post(BACKEND_API_URL, json=full_payload, timeout=15)
        response.raise_for_status()
        print(f"[✅] Backend API triggered successfully! Status: {response.status_code}")
        print(f"    📋 Response: {response.json()}")
        
        # Mark this anomaly as active to prevent duplicate alerts
        active_anomalies[anomaly_type] = True
        last_anomaly_timestamps[anomaly_type] = current_time
        
        print(f"[🔒] Anomaly '{anomaly_type}' marked as active. Future alerts suppressed until resolved.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[❌] ERROR: Could not trigger backend API. {e}")
        return False

def record_and_upload_clip(anomaly_type: str) -> str:
    """Records a clip from the frame buffer and uploads it to GCS."""
    try:
        clip_filename = f"{anomaly_type.lower().replace(' ', '_').replace('/', '_')}_{int(time.time())}.mp4"
        local_clip_path = os.path.join("/tmp", clip_filename)
        
        # Ensure /tmp directory exists
        os.makedirs("/tmp", exist_ok=True)
        
        # Use a copy of the buffer to avoid modification during save
        buffer_copy = list(frame_buffer)
        if not buffer_copy:
            print("[X] Frame buffer is empty, cannot record clip")
            return None
            
        # Get frame dimensions from the first frame
        frame_height, frame_width = buffer_copy[0].shape[:2]
        save_clip_from_buffer(buffer_copy, local_clip_path, VIDEO_FPS, (frame_width, frame_height))
        
        # Upload to GCS
        gcs_path = upload_clip_to_gcs(local_clip_path, f"anomaly_clips/{clip_filename}")
        return gcs_path
    except Exception as e:
        print(f"[X] ERROR: Failed to record and upload clip: {e}")
        return None

def calculate_movement_vector(current_pos, previous_pos):
    """Calculate normalized movement vector between two positions."""
    if previous_pos is None:
        return (0, 0)
    
    dx = current_pos[0] - previous_pos[0]
    dy = current_pos[1] - previous_pos[1]
    magnitude = math.sqrt(dx*dx + dy*dy)
    
    if magnitude == 0:
        return (0, 0)
    
    return (dx/magnitude, dy/magnitude)

# REMOVED: dot_product function (was only used for wrong-way detection)

# --- Existing Anomaly Detection Functions ---

def check_unattended_objects(tracked_objects, current_persons, current_time):
    for obj_id, obj_info in tracked_objects.items():
        if obj_info['class_name'] in UNATTENDED_OBJECT_CLASSES:
            obj_centroid = obj_info['last_seen_centroid']
            
            person_is_near = any(np.linalg.norm(np.array(obj_centroid) - np.array(p_cen)) < PERSON_PROXIMITY_THRESHOLD_PX for p_cen in current_persons)
            if person_is_near:
                obj_info['last_person_near_time'] = current_time

            is_unattended = (current_time - obj_info['last_person_near_time']) > UNATTENDED_THRESHOLD_SECONDS
            
            if is_unattended and not obj_info.get('backend_notified', False):
                anomaly_id = f"unattended_{obj_id}"
                data = {
                    "anomalyId": anomaly_id,
                    "anomalyType": "Unattended Object",
                    "timestamp": time.time(),
                    "details": f"Unattended {obj_info['class_name']} detected.",
                    "record_clip": False  # Less critical - no clip recording
                }
                if trigger_backend_analysis(data):
                    obj_info['backend_notified'] = True

def check_crowd_density(current_persons, roi_abs):
    global reported_anomalies
    persons_in_roi = sum(1 for px, py in current_persons if roi_abs[0] <= px <= roi_abs[2] and roi_abs[1] <= py <= roi_abs[3])
    
    if persons_in_roi > CROWD_DENSITY_ZONE_THRESHOLD:
        # Check if we already have an active incident for this anomaly type
        if not is_anomaly_active_in_backend("High Crowd Density"):
            anomaly_id = f"crowd_density_{uuid.uuid4()}"
            data = {
                "anomalyId": anomaly_id,
                "anomalyType": "High Crowd Density",
                "timestamp": time.time(),
                "details": f"Detected {persons_in_roi} persons in designated zone (threshold: {CROWD_DENSITY_ZONE_THRESHOLD}).",
                "record_clip": True  # This anomaly should trigger clip recording
            }
            if trigger_backend_analysis(data):
                reported_anomalies["crowd_density"] = True
    else:
        # Crowd density returned to normal - reset local state
        if reported_anomalies["crowd_density"]:
            print("[✅] Crowd density has returned to normal levels.")
            reported_anomalies["crowd_density"] = False
            # Allow the stateful system to detect when the incident is formally resolved

def check_fall_detection(tracked_objects):
    for obj_id, obj_info in tracked_objects.items():
        if obj_info['class_name'] == 'person' and len(obj_info['aspect_ratio_history']) >= FALL_DETECTION_WINDOW_FRAMES:
            current_ar = obj_info['aspect_ratio_history'][-1]
            previous_ar = obj_info['aspect_ratio_history'][0]

            is_fallen = (previous_ar > FALL_ASPECT_RATIO_THRESHOLD and
                         current_ar < 1.0 and
                         (previous_ar - current_ar) > FALL_RATIO_CHANGE_THRESHOLD)

            if is_fallen and not obj_info.get('backend_notified_fall', False):
                anomaly_id = f"fall_{obj_id}"
                data = {
                    "anomalyId": anomaly_id,
                    "anomalyType": "Fall Detection",
                    "timestamp": time.time(),
                    "details": f"Potential fall detected for person ID {obj_id}. Aspect ratio changed from {previous_ar:.2f} to {current_ar:.2f}.",
                    "record_clip": True  # Critical anomaly - record clip
                }
                if trigger_backend_analysis(data):
                    obj_info['backend_notified_fall'] = True

# --- NEW: Additional Anomaly Detection Functions ---

def check_loitering(tracked_objects, current_time):
    """Detect persons who remain stationary for too long in non-designated areas."""
    for obj_id, obj_info in tracked_objects.items():
        if obj_info['class_name'] == 'person':
            # Check if person has been relatively stationary
            position_history = obj_info.get('position_history', deque(maxlen=STATIONARY_CHECK_WINDOW_FRAMES))
            
            if len(position_history) >= STATIONARY_CHECK_WINDOW_FRAMES:
                # Calculate movement over the window
                first_pos = position_history[0]
                last_pos = position_history[-1]
                movement_distance = np.linalg.norm(np.array(last_pos) - np.array(first_pos))
                
                if movement_distance < STATIONARY_MOVEMENT_THRESHOLD_PX:
                    # Person is stationary
                    if 'stationary_start_time' not in obj_info:
                        obj_info['stationary_start_time'] = current_time
                    
                    stationary_duration = current_time - obj_info['stationary_start_time']
                    
                    if (stationary_duration > LOITERING_THRESHOLD_SECONDS and
                        not obj_info.get('backend_notified_loitering', False)):
                        
                        anomaly_id = f"loitering_{obj_id}"
                        data = {
                            "anomalyId": anomaly_id,
                            "anomalyType": "Loitering",
                            "timestamp": time.time(),
                            "details": f"Person ID {obj_id} has been stationary for {stationary_duration:.1f} seconds.",
                            "record_clip": False  # Less critical - no clip recording
                        }
                        if trigger_backend_analysis(data):
                            obj_info['backend_notified_loitering'] = True
                else:
                    # Person is moving, reset stationary tracking
                    obj_info.pop('stationary_start_time', None)
                    obj_info.pop('backend_notified_loitering', None)

# REMOVED: check_wrong_way_movement function

def check_fighting_aggression(tracked_objects, current_time):
    """Detect potential fighting based on erratic movements between close people."""
    person_objects = {oid: info for oid, info in tracked_objects.items() if info['class_name'] == 'person'}
    
    # Find clusters of people in close proximity
    person_ids = list(person_objects.keys())
    for i in range(len(person_ids)):
        for j in range(i + 1, len(person_ids)):
            id1, id2 = person_ids[i], person_ids[j]
            pos1 = person_objects[id1]['last_seen_centroid']
            pos2 = person_objects[id2]['last_seen_centroid']
            
            distance = np.linalg.norm(np.array(pos1) - np.array(pos2))
            
            if distance < FIGHTING_PROXIMITY_THRESHOLD_PX:
                cluster_key = f"cluster_{min(id1, id2)}_{max(id1, id2)}"
                
                # Track velocities and distance changes
                vel1 = person_objects[id1].get('velocity', 0)
                vel2 = person_objects[id2].get('velocity', 0)
                
                violence_score = (vel1 + vel2) * (1 / (distance + 1))  # Higher score for close, fast-moving people
                
                # Store violence scores for this cluster
                if cluster_key not in tracked_objects:
                    tracked_objects[cluster_key] = {
                        'class_name': 'cluster',
                        'violence_scores': deque(maxlen=FIGHTING_DETECTION_WINDOW_FRAMES),
                        'last_seen_time': current_time
                    }
                
                tracked_objects[cluster_key]['violence_scores'].append(violence_score)
                tracked_objects[cluster_key]['last_seen_time'] = current_time
                
                if len(tracked_objects[cluster_key]['violence_scores']) >= FIGHTING_DETECTION_WINDOW_FRAMES:
                    avg_violence_score = np.mean(tracked_objects[cluster_key]['violence_scores'])
                    
                    if (avg_violence_score > FIGHTING_SCORE_THRESHOLD and
                        not tracked_objects[cluster_key].get('backend_notified_fighting', False)):
                        
                        anomaly_id = f"fighting_{cluster_key}"
                        data = {
                            "anomalyId": anomaly_id,
                            "anomalyType": "Fighting/Aggression",
                            "timestamp": time.time(),
                            "details": f"Potential fighting detected between persons {id1} and {id2}. Violence score: {avg_violence_score:.2f}",
                            "record_clip": True  # Critical anomaly - record clip
                        }
                        if trigger_backend_analysis(data):
                            tracked_objects[cluster_key]['backend_notified_fighting'] = True

def check_asset_removal(current_detections, width, height, current_time):
    """Check if critical assets are missing from their designated locations."""
    global CRITICAL_ASSETS
    
    for asset_name, asset_config in CRITICAL_ASSETS.items():
        roi_norm = asset_config['roi']
        roi_abs = (
            int(roi_norm[0] * width),
            int(roi_norm[1] * height),
            int(roi_norm[2] * width),
            int(roi_norm[3] * height)
        )
        
        # Check if the asset is detected in its ROI
        asset_detected = False
        for detection in current_detections:
            class_name = YOLO_MODEL.names[int(detection.cls[0])]
            if class_name == asset_config['class_name']:
                x1, y1, x2, y2 = map(int, detection.xyxy[0])
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                
                if (roi_abs[0] <= centroid[0] <= roi_abs[2] and
                    roi_abs[1] <= centroid[1] <= roi_abs[3]):
                    asset_detected = True
                    break
        
        if asset_config['present'] is None:
            # First time checking this asset
            asset_config['present'] = asset_detected
            if asset_detected:
                print(f"[INFO] Asset {asset_name} confirmed present at startup.")
            continue
        
        if asset_config['present'] and not asset_detected:
            # Asset was present but now missing
            if 'missing_start_time' not in asset_config:
                asset_config['missing_start_time'] = current_time
            
            missing_duration = current_time - asset_config['missing_start_time']
            
            if (missing_duration > ASSET_MISSING_THRESHOLD_SECONDS and
                not asset_config.get('backend_notified', False)):
                
                anomaly_id = f"asset_removed_{asset_name}"
                data = {
                    "anomalyId": anomaly_id,
                    "anomalyType": "Asset Removal",
                    "timestamp": time.time(),
                    "details": f"Critical asset '{asset_name}' ({asset_config['class_name']}) is missing from its designated location.",
                    "record_clip": True  # Critical anomaly - record clip
                }
                if trigger_backend_analysis(data):
                    asset_config['backend_notified'] = True
        
        elif not asset_config['present'] and asset_detected:
            # Asset has returned
            asset_config['present'] = True
            asset_config.pop('missing_start_time', None)
            asset_config.pop('backend_notified', None)
            print(f"[INFO] Asset {asset_name} has returned to its location.")

def run_edge_monitoring():
    """Main function that runs continuous edge monitoring with clip recording."""
    global frame_count
    
    # Determine video source
    try:
        video_source_int = int(VIDEO_SOURCE)
        cap = cv2.VideoCapture(video_source_int)
        print(f"Using webcam source: {video_source_int}")
    except (ValueError, TypeError):
        cap = cv2.VideoCapture(VIDEO_SOURCE)
        print(f"Using video file source: {VIDEO_SOURCE}")

    if not cap.isOpened():
        print(f"Error: Could not open video source '{VIDEO_SOURCE}'")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print("--- 🤖 STATEFUL Edge Monitoring Initialized ---")
    print(f"  📹 Video Source: {VIDEO_SOURCE}")
    print(f"  🔗 Backend Target: {BACKEND_API_URL}")
    print(f"  ☁️ GCS Bucket: {GCS_BUCKET_NAME}")
    print(f"  📐 Video Dimensions: {width}x{height}")
    print(f"  🔥 Firebase State Management: {'✅ Enabled' if db else '⚠️ Disabled'}")
    print("  🎯 Enabled Anomalies: Unattended Objects, Crowd Density, Fall Detection, Loitering, Fighting, Asset Removal")
    print("  🧠 Intelligent Features: Clip Recording, Alert Deduplication, State Management")
    print("----------------------------------------------------")

    tracked_objects = {}
    next_object_id = 0

    crowd_density_roi_abs = (
        int(CROWD_DENSITY_ROI_NORMALIZED[0] * width),
        int(CROWD_DENSITY_ROI_NORMALIZED[1] * height),
        int(CROWD_DENSITY_ROI_NORMALIZED[2] * width),
        int(CROWD_DENSITY_ROI_NORMALIZED[3] * height)
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video source or failed to read frame.")
            break

        current_time = time.time()
        frame_count += 1
        
        # Add frame to buffer for potential clip recording
        frame_buffer.append(frame.copy())
        
        # Control processing speed
        time.sleep(1 / VIDEO_FPS)

        results = YOLO_MODEL(frame, verbose=False)

        current_persons = []
        detections_in_frame = []
        
        # Process YOLO results
        for r in results:
            for box in r.boxes:
                if float(box.conf[0]) > MIN_DETECTION_CONFIDENCE:
                    detections_in_frame.append(box)

        # Update Object Tracker
        matched_ids = set()
        for obj_id, obj_info in tracked_objects.items():
            if obj_info['class_name'] == 'cluster':  # Skip cluster objects in tracking
                continue
                
            min_dist = float('inf')
            best_match_idx = -1
            for i, box in enumerate(detections_in_frame):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                dist = np.linalg.norm(np.array(centroid) - np.array(obj_info['last_seen_centroid']))
                if dist < OBJECT_TRACKING_MAX_DISTANCE_PX and dist < min_dist:
                    min_dist = dist
                    best_match_idx = i
            
            if best_match_idx != -1:
                # Update the matched object
                box = detections_in_frame[best_match_idx]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                new_centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                
                # Store previous position for movement tracking
                obj_info['previous_centroid'] = obj_info['last_seen_centroid']
                obj_info['last_seen_centroid'] = new_centroid
                obj_info['last_seen_time'] = current_time
                
                # Update position history for loitering detection
                if 'position_history' not in obj_info:
                    obj_info['position_history'] = deque(maxlen=STATIONARY_CHECK_WINDOW_FRAMES)
                obj_info['position_history'].append(new_centroid)
                
                # Calculate velocity for fighting detection
                if obj_info.get('previous_centroid'):
                    prev_pos = obj_info['previous_centroid']
                    velocity = np.linalg.norm(np.array(new_centroid) - np.array(prev_pos))
                    obj_info['velocity'] = velocity
                
                # Update aspect ratio for fall detection
                if obj_info['class_name'] == 'person':
                    aspect_ratio = (y2-y1) / (x2-x1) if (x2-x1) > 0 else 0
                    obj_info['aspect_ratio_history'].append(aspect_ratio)
                    if len(obj_info['aspect_ratio_history']) > FALL_DETECTION_WINDOW_FRAMES:
                        obj_info['aspect_ratio_history'].pop(0)

                matched_ids.add(best_match_idx)

        # Add new objects for unmatched detections
        for i, box in enumerate(detections_in_frame):
            if i not in matched_ids:
                class_name = YOLO_MODEL.names[int(box.cls[0])]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                tracked_objects[next_object_id] = {
                    'class_name': class_name,
                    'last_seen_centroid': ((x1 + x2) // 2, (y1 + y2) // 2),
                    'previous_centroid': None,
                    'last_seen_time': current_time,
                    'last_person_near_time': 0 if class_name in UNATTENDED_OBJECT_CLASSES else current_time,
                    'aspect_ratio_history': [],
                    'position_history': deque(maxlen=STATIONARY_CHECK_WINDOW_FRAMES),
                    'velocity': 0,
                }
                next_object_id += 1
        
        # Clean up lost objects
        lost_ids = [obj_id for obj_id, info in tracked_objects.items() 
                   if info['class_name'] != 'cluster' and (current_time - info['last_seen_time']) > OBJECT_TRACKING_GRACE_PERIOD_SECONDS]
        for obj_id in lost_ids:
            print(f"[INFO] Lost track of object ID {obj_id} ({tracked_objects[obj_id]['class_name']})")
            del tracked_objects[obj_id]
        
        # Clean up old clusters
        cluster_ids = [obj_id for obj_id, info in tracked_objects.items() 
                      if info['class_name'] == 'cluster' and (current_time - info['last_seen_time']) > 5]
        for cluster_id in cluster_ids:
            del tracked_objects[cluster_id]
        
        current_persons = [info['last_seen_centroid'] for info in tracked_objects.values() if info['class_name'] == 'person']

        # --- STATEFUL ANOMALY MANAGEMENT ---
        # Periodically check if any active anomalies have been resolved in the backend
        check_and_resolve_anomalies()

        # Run All Anomaly Checks (now with intelligent state management)
        check_unattended_objects(tracked_objects, current_persons, current_time)
        check_crowd_density(current_persons, crowd_density_roi_abs)
        check_fall_detection(tracked_objects)
        
        # NEW: Additional anomaly checks
        check_loitering(tracked_objects, current_time)
        check_fighting_aggression(tracked_objects, current_time)
        check_asset_removal(detections_in_frame, width, height, current_time)

    cap.release()
    print("\nEdge monitoring finished.")

if __name__ == "__main__":
    if not VIDEO_SOURCE:
        print("Please set VIDEO_SOURCE in your .env file.")
        exit(1)
    
    print(f"Starting enhanced edge monitoring with clip recording...")
    print(f"  - Video Source: {VIDEO_SOURCE}")
    print(f"  - Backend Target: {BACKEND_API_URL}")
    print(f"  - GCS Bucket: {GCS_BUCKET_NAME}")
    run_edge_monitoring()