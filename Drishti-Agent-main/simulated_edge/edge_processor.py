# simulated_edge/edge_processor.py
import cv2
import os
import time
# No need for requests, google.cloud.storage, dotenv for this pure local test
# from google.cloud import storage
# from dotenv import load_dotenv
import uuid # Still useful for generating unique IDs for logs if needed
from ultralytics import YOLO
import numpy as np

# --- Configuration ---
# Only VIDEO_FILE_PATH is strictly needed for this local test.
# GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
# CLOUD_FUNCTION_URL = os.getenv('CLOUD_FUNCTION_URL')
VIDEO_FILE_PATH = os.getenv('VIDEO_FILE_PATH') # This will be read from .env

CLIP_DURATION_SECONDS = 5 # Still relevant for conceptual clip saving
VIDEO_FPS = 30 

# --- YOLO Model Configuration ---
YOLO_MODEL = YOLO('yolov8n.pt') 

# --- Anomaly Detection Criteria ---
# Unattended Objects
UNATTENDED_OBJECT_CLASSES = ['backpack', 'suitcase', 'handbag']
UNATTENDED_THRESHOLD_SECONDS = 5 
PERSON_PROXIMITY_THRESHOLD_PX = 100 

# Crowd Density
CROWD_DENSITY_ZONE_THRESHOLD = 4 # Max number of people allowed in the zone
CROWD_DENSITY_ROI_NORMALIZED = (0.2, 0.5, 0.8, 0.9) # Adjust this based on your video

# Fall Detection
FALL_ASPECT_RATIO_THRESHOLD = 1.2 
FALL_RATIO_CHANGE_THRESHOLD = 0.5 
FALL_DETECTION_WINDOW_FRAMES = 5 

# Wrong-Way / Counter-Flow Detection - REMOVED

MIN_DETECTION_CONFIDENCE = 0.5 

# --- Helper Functions (Stubs for local test) ---
# These functions are now just placeholders to avoid errors if called
# and to confirm that the cloud interaction points are reached conceptually.
def upload_blob(source_file_name, destination_blob_name):
    """Stub: Simulates upload to GCS."""
    print(f"[TEST MODE - GCS] Simulating upload of {source_file_name} to {destination_blob_name}")
    return f"http://dummy-gcs-url.com/{destination_blob_name}"

def trigger_cloud_function(anomaly_data):
    """Stub: Simulates sending anomaly data to Cloud Function."""
    print(f"[TEST MODE - CF] Simulating Cloud Function trigger for anomaly: {anomaly_data['anomalyType']}")
    print(f"  Details: {anomaly_data.get('details', 'No details provided')}")
    print(f"  Video URL (would be uploaded): {anomaly_data['videoUrl']}")


def simulate_edge_detection(video_path):
    """
    Simulates an edge device processing a video, detecting anomalies using YOLO,
    and logging detections. No actual cloud interaction.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Processing video: {video_path} ({width}x{height}) with {total_frames} frames.")

    frames_per_clip = int(CLIP_DURATION_SECONDS * VIDEO_FPS)
    
    # --- Anomaly State Management ---
    # Only crowd density remains a global flag as it's zone-based.
    crowd_density_anomaly_active = False 

    # For General Object Tracking
    # Each tracked object will now have its own anomaly active flags
    tracked_objects = {}
    next_object_id = 0 

    current_frame_number = 0
    frames_buffer = [] 

    # Define ROI for crowd density in absolute pixel coordinates
    crowd_density_roi_abs = (
        int(CROWD_DENSITY_ROI_NORMALIZED[0] * width),
        int(CROWD_DENSITY_ROI_NORMALIZED[1] * height), 
        int(CROWD_DENSITY_ROI_NORMALIZED[2] * width),
        int(CROWD_DENSITY_ROI_NORMALIZED[3] * height)
    )

    # Removed: expected_flow_vector_abs

    while True:
        ret, frame = cap.read()
        if not ret:
            break 

        current_frame_number += 1
        current_time = time.time()
        
        frames_buffer.append(frame)
        if len(frames_buffer) > frames_per_clip:
            frames_buffer.pop(0)

        time.sleep(1 / VIDEO_FPS) 

        # --- YOLO Inference ---
        results = YOLO_MODEL(frame, verbose=False) 

        current_persons = [] 
        newly_detected_in_frame = {} 

        # Process detections and update tracked_objects
        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = YOLO_MODEL.names[class_id]

                if confidence < MIN_DETECTION_CONFIDENCE:
                    continue 

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                obj_centroid_x, obj_centroid_y = (x1 + x2) // 2, (y1 + y2) // 2
                obj_centroid = (obj_centroid_x, obj_centroid_y) 

                box_width = x2 - x1
                box_height = y2 - y1
                aspect_ratio = box_height / box_width if box_width > 0 else 0

                matched_id = None
                min_dist = float('inf')
                for obj_id, obj_info in tracked_objects.items():
                    if obj_info['class_name'] == class_name and 'last_seen_centroid' in obj_info:
                        dist = np.linalg.norm(np.array(obj_centroid) - np.array(obj_info['last_seen_centroid']))
                        if dist < 70: 
                            if dist < min_dist:
                                min_dist = dist
                                matched_id = obj_id
                
                if matched_id:
                    obj_id = matched_id
                    tracked_objects[obj_id]['last_seen_centroid'] = obj_centroid
                    tracked_objects[obj_id]['last_seen_time'] = current_time
                else:
                    obj_id = next_object_id
                    next_object_id += 1
                    tracked_objects[obj_id] = {
                        'class_name': class_name,
                        'last_seen_centroid': obj_centroid,
                        'last_seen_time': current_time,
                        'last_person_near_time': current_time, 
                        'aspect_ratio_history': [], 
                        # Removed: 'last_flow_centroid'
                        'is_unattended_active': False, # Per-object anomaly flag
                        'is_fall_active': False,       # Per-object anomaly flag
                        # Removed: 'is_wrong_way_active'
                    }
                newly_detected_in_frame[obj_id] = True 

                if class_name == 'person':
                    current_persons.append((obj_centroid_x, obj_centroid_y)) 
                    tracked_objects[obj_id]['aspect_ratio_history'].append(aspect_ratio)
                    if len(tracked_objects[obj_id]['aspect_ratio_history']) > FALL_DETECTION_WINDOW_FRAMES:
                        tracked_objects[obj_id]['aspect_ratio_history'].pop(0)
                
                # Removed: if class_name in FLOW_CLASSES:
                # Removed: tracked_objects[obj_id]['current_flow_centroid'] = obj_centroid
        
        # Clean up tracked_objects not seen in current frame
        # Keep objects for a short grace period (1 second) to allow for re-detection
        tracked_objects = {
            obj_id: info for obj_id, info in tracked_objects.items()
            if obj_id in newly_detected_in_frame or (current_time - info['last_seen_time'] < 1) 
        }

        # --- Anomaly Detection Logic (Logging Only) ---

        # 1. Unattended Objects Detection
        for obj_id, obj_info in tracked_objects.items():
            if obj_info['class_name'] in UNATTENDED_OBJECT_CLASSES:
                obj_centroid = obj_info['last_seen_centroid']
                obj_class = obj_info['class_name']
                
                person_near = False
                for person_centroid in current_persons:
                    if np.linalg.norm(np.array(obj_centroid) - np.array(person_centroid)) < PERSON_PROXIMITY_THRESHOLD_PX:
                        person_near = True
                        break
                
                is_currently_unattended = (current_time - obj_info['last_person_near_time'] > UNATTENDED_THRESHOLD_SECONDS and
                                           current_time - obj_info['last_seen_time'] < 2) # Still visible

                if is_currently_unattended and not obj_info['is_unattended_active']:
                    print(f"\n[ANOMALY DETECTED] Unattended {obj_class} (ID: {obj_id}) at frame {current_frame_number}")
                    print(f"  Details: Object stationary for {UNATTENDED_THRESHOLD_SECONDS}s without a person nearby.")
                    obj_info['is_unattended_active'] = True
                elif not is_currently_unattended and obj_info['is_unattended_active']:
                    print(f"\n[ANOMALY RESOLVED] Unattended {obj_class} (ID: {obj_id}) at frame {current_frame_number}")
                    obj_info['is_unattended_active'] = False 


        # 2. Crowd Density Detection (Global Flag)
        persons_in_roi = 0
        for p_centroid_x, p_centroid_y in current_persons:
            if (crowd_density_roi_abs[0] <= p_centroid_x <= crowd_density_roi_abs[2] and
                crowd_density_roi_abs[1] <= p_centroid_y <= crowd_density_roi_abs[3]):
                persons_in_roi += 1
        
        if persons_in_roi > CROWD_DENSITY_ZONE_THRESHOLD:
            if not crowd_density_anomaly_active:
                print(f"\n[ANOMALY DETECTED] High Crowd Density in ROI at frame {current_frame_number}")
                print(f"  Details: Detected {persons_in_roi} persons in zone, threshold is {CROWD_DENSITY_ZONE_THRESHOLD}.")
                crowd_density_anomaly_active = True
        else:
            crowd_density_anomaly_active = False 

        # 3. Fall Detection (Per-Object Flag)
        for obj_id, obj_info in tracked_objects.items():
            if obj_info['class_name'] == 'person' and len(obj_info['aspect_ratio_history']) >= FALL_DETECTION_WINDOW_FRAMES:
                current_ar = obj_info['aspect_ratio_history'][-1]
                previous_ar = obj_info['aspect_ratio_history'][-FALL_DETECTION_WINDOW_FRAMES] 

                is_currently_fallen = (previous_ar - current_ar > FALL_RATIO_CHANGE_THRESHOLD and
                                        current_ar < FALL_ASPECT_RATIO_THRESHOLD)
                    
                if is_currently_fallen and not obj_info['is_fall_active']:
                    print(f"\n[ANOMALY DETECTED] Person Fall (ID: {obj_id}) at frame {current_frame_number}")
                    print(f"  Details: Aspect ratio changed from {previous_ar:.2f} to {current_ar:.2f}.")
                    obj_info['is_fall_active'] = True
                elif not is_currently_fallen and obj_info['is_fall_active']:
                    print(f"\n[ANOMALY RESOLVED] Person Fall (ID: {obj_id}) at frame {current_frame_number}")
                    obj_info['is_fall_active'] = False 

        # 4. Wrong-Way / Counter-Flow Detection - REMOVED
        # All logic for Wrong-Way / Counter-Flow detection has been removed from here.

        # Optional: Display frame with detections and ROI (uncomment for visual debugging)
        # frame_display = frame.copy()
        # for obj_id, obj_info in tracked_objects.items():
        #     class_name = obj_info['class_name']
        #     centroid = obj_info['last_seen_centroid']
        #     # Simple box for visualization
        #     x1, y1 = centroid[0] - 20, centroid[1] - 20 
        #     x2, y2 = centroid[0] + 20, centroid[1] + 20
        #     color = (0, 255, 0) # Green for general detection
        #     text = f"{class_name} ID:{obj_id}"

        #     if obj_info.get('is_unattended_active'):
        #         color = (0, 165, 255) # Orange for potential unattended
        #         text += " (UNATTENDED)"
            
        #     if obj_info.get('is_fall_active'):
        #         color = (0, 0, 255) # Red for fall
        #         text += " (FALLING)"

        #     # Removed: if obj_info.get('is_wrong_way_active'):
        #     # Removed: color = (255, 0, 0) # Blue for wrong-way
        #     # Removed: text += " (WRONG-WAY)"

        #     cv2.rectangle(frame_display, (x1, y1), (x2, y2), color, 2)
        #     cv2.putText(frame_display, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # # Draw crowd density ROI
        # cv2.rectangle(frame_display, (crowd_density_roi_abs[0], crowd_density_roi_abs[1]), 
        #               (crowd_density_roi_abs[2], crowd_density_roi_abs[3]), (255, 255, 0), 2) # Cyan ROI
        # cv2.putText(frame_display, f"Persons in ROI: {persons_in_roi}", (crowd_density_roi_abs[0], crowd_density_roi_abs[1] - 10),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # cv2.imshow('Simulated Edge Detection', frame_display)
        # if cv2.waitKey(1) & 0xFF == ord('q'): 
        #     break

    cap.release()
    # cv2.destroyAllWindows() 
    print("\nSimulation finished.")

if __name__ == "__main__":
    # Load environment variables here, as they are needed for VIDEO_FILE_PATH
    from dotenv import load_dotenv
    load_dotenv()

    if not VIDEO_FILE_PATH: 
        print("Please set VIDEO_FILE_PATH in your .env file.")
        exit(1)
    
    full_video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), VIDEO_FILE_PATH))
    
    if not os.path.exists(full_video_path):
        print(f"Error: Video file not found at {full_video_path}")
        print("Please check VIDEO_FILE_PATH in your .env file and ensure the video exists.")
        exit(1)

    print("Starting simulated edge detection with YOLOv8n (TEST MODE - Logging Only)...")
    simulate_edge_detection(full_video_path)
