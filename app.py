"""
TrashWatch - Real-time Trash Detection with YOLOv8 + Supabase + Streamlit
"""

import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import os
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import time
import threading
import platform

# Configure Streamlit page
st.set_page_config(
    page_title="TrashWatch",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZE SESSION STATE & SUPABASE
# ============================================================================

@st.cache_resource
def load_yolo_model():
    """Load YOLOv8 model (cached for performance)"""
    try:
        model = YOLO("yolov8n.pt")
        return model
    except Exception as e:
        st.error(f"Error loading YOLOv8 model: {e}")
        return None

def play_alert_sound():
    """Play alert sound when trash is detected"""
    try:
        if platform.system() == "Windows":
            winsound.Beep(1000, 500)  # frequency 1000Hz, duration 500ms
        else:
            # On Mac/Linux, use system beep
            os.system('afplay /System/Library/Sounds/Alarm.aiff &' if platform.system() == "Darwin" else 'paplay /usr/share/sounds/freedesktop/stereo/bell.oga &')
    except Exception as e:
        st.warning(f"Could not play sound: {e}")

def upload_to_supabase(image_bytes, detection_label, confidence, camera_source):
    """Upload snapshot to Supabase storage"""
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        
        # Upload image to storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{timestamp}_{int(time.time()*1000)}.jpg"
        
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "image/jpeg"
        }
        
        upload_url = f"{supabase_url}/storage/v1/object/public/snapshots/{filename}"
        response = requests.post(upload_url, headers=headers, data=image_bytes)
        
        image_url = f"{supabase_url}/storage/v1/object/public/snapshots/{filename}" if response.status_code == 200 else None
        
        # Log detection to database
        log_detection_to_db(detection_label, confidence, camera_source, image_url)
        
        return True
    except Exception as e:
        st.warning(f"Could not upload to Supabase: {e}")
        return False

def log_detection_to_db(label, confidence, camera_source, image_url=None):
    """Log detection to Supabase database"""
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        data = {
            "label": label,
            "confidence": float(confidence),
            "camera_source": camera_source,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "image_url": image_url
        }
        
        response = requests.post(
            f"{supabase_url}/rest/v1/detections",
            headers=headers,
            json=data
        )
        
        return response.status_code == 201
    except Exception as e:
        st.warning(f"Could not log to database: {e}")
        return False

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

st.sidebar.title("⚙️ TrashWatch Settings")

# Camera selection
camera_source = st.sidebar.radio(
    "📷 Camera Source",
    options=["Laptop webcam", "Mobile IP Webcam"],
    help="Select where to capture video from"
)

if camera_source == "Mobile IP Webcam":
    mobile_url = st.sidebar.text_input(
        "📱 Mobile Camera URL",
        value="http://192.168.1.5:8080/shot.jpg",
        help="IP Webcam URL ending in /shot.jpg (must be on same Wi-Fi)"
    )
else:
    mobile_url = None

# Confidence threshold
confidence_threshold = st.sidebar.slider(
    "🎯 Confidence Threshold",
    min_value=0.1,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Lower = more detections but more false positives"
)

# Enable/disable features
enable_sound = st.sidebar.checkbox("🔔 Alert Sound", value=True)
enable_snapshots = st.sidebar.checkbox("📸 Save Snapshots to Supabase", value=True)
show_stats = st.sidebar.checkbox("📊 Show Statistics", value=True)

st.sidebar.divider()
st.sidebar.write("**🗑️ TrashWatch v1.0**")
st.sidebar.write("Built with YOLOv8 + Streamlit + Supabase")

# ============================================================================
# MAIN TABS
# ============================================================================

tab1, tab2, tab3 = st.tabs(["🎥 LIVE DETECTION", "📋 HISTORY", "ℹ️ ABOUT"])

# ============================================================================
# TAB 1: LIVE DETECTION
# ============================================================================

with tab1:
    st.header("🎥 Live Trash Detection")
    
    # Load model
    model = load_yolo_model()
    if model is None:
        st.error("Could not load YOLOv8 model. Make sure you have internet to download it.")
        st.stop()
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        start_detection = st.button("▶️ START DETECTION", use_container_width=True, key="start_btn")
        stop_detection = st.button("⏹️ STOP DETECTION", use_container_width=True, key="stop_btn")
    
    with col1:
        video_placeholder = st.empty()
        stats_placeholder = st.empty()
    
    # Detection loop
    if start_detection or st.session_state.get("detection_running", False):
        st.session_state.detection_running = True
        
        detections_list = []
        frame_count = 0
        total_detections = 0
        
        try:
            # Open camera
            if camera_source == "Laptop webcam":
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    st.error("Cannot open webcam. Make sure camera is available and not used by another app.")
                    st.session_state.detection_running = False
                    st.stop()
            else:
                # Mobile camera
                cap = None
            
            progress_bar = st.progress(0)
            frame_counter = st.empty()
            
            while st.session_state.detection_running and not stop_detection:
                try:
                    # Capture frame
                    if camera_source == "Laptop webcam":
                        ret, frame = cap.read()
                        if not ret:
                            st.error("Could not read from webcam")
                            break
                        frame = cv2.resize(frame, (640, 480))
                    else:
                        # Mobile IP Webcam
                        try:
                            response = requests.get(mobile_url, timeout=5)
                            if response.status_code == 200:
                                image = Image.open(BytesIO(response.content))
                                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                                frame = cv2.resize(frame, (640, 480))
                            else:
                                st.error("Cannot connect to mobile camera. Check URL and Wi-Fi.")
                                break
                        except Exception as e:
                            st.error(f"Mobile camera error: {e}")
                            break
                    
                    # Run YOLO detection
                    results = model(frame, conf=confidence_threshold, verbose=False)
                    
                    # Draw bounding boxes
                    annotated_frame = results[0].plot()
                    
                    # Extract detections
                    if results[0].boxes is not None:
                        for box in results[0].boxes:
                            cls_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            label = model.names[cls_id]
                            
                            total_detections += 1
                            detections_list.append({
                                'label': label,
                                'confidence': confidence,
                                'timestamp': datetime.now()
                            })
                            
                            # Alert
                            if enable_sound:
                                threading.Thread(target=play_alert_sound, daemon=True).start()
                            
                            # Upload to Supabase
                            if enable_snapshots:
                                _, buffer = cv2.imencode('.jpg', frame)
                                upload_to_supabase(buffer.tobytes(), label, confidence, camera_source)
                    
                    # Display frame
                    frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
                    
                    # Update statistics
                    frame_count += 1
                    progress_bar.progress(min(frame_count / 1000, 1.0))
                    frame_counter.metric("Frames Processed", frame_count)
                    
                    with stats_placeholder.container():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Detections", total_detections)
                        with col2:
                            avg_per_frame = total_detections / max(frame_count, 1)
                            st.metric("Avg per Frame", f"{avg_per_frame:.2f}")
                        with col3:
                            st.metric("FPS", f"{1/0.033:.0f}")  # Approx FPS
                    
                    # Small delay for UI responsiveness
                    time.sleep(0.033)  # ~30 FPS
                    
                except Exception as e:
                    st.error(f"Detection error: {e}")
                    break
            
            if camera_source == "Laptop webcam" and cap:
                cap.release()
            
            st.session_state.detection_running = False
            st.success("Detection stopped!")
            
        except Exception as e:
            st.error(f"Error during detection: {e}")
            st.session_state.detection_running = False

# ============================================================================
# TAB 2: HISTORY
# ============================================================================

with tab2:
    st.header("📋 Detection History")
    
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/detections?order=timestamp.desc&limit=100",
            headers=headers
        )
        
        if response.status_code == 200:
            detections = response.json()
            
            if detections:
                st.dataframe(
                    detections,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download button
                import csv
                import io
                
                csv_buffer = io.StringIO()
                if detections:
                    writer = csv.DictWriter(csv_buffer, fieldnames=detections[0].keys())
                    writer.writeheader()
                    writer.writerows(detections)
                    
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"detections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No detections yet. Start detection to see history.")
        else:
            st.warning("Could not fetch history. Check Supabase credentials in secrets.")
    
    except Exception as e:
        st.warning(f"Error fetching history: {e}")

# ============================================================================
# TAB 3: ABOUT
# ============================================================================

with tab3:
    st.header("ℹ️ About TrashWatch")
    
    st.markdown("""
    ### 🗑️ TrashWatch
    
    Real-time trash detection using computer vision.
    
    **Features:**
    - 🎥 Live detection from laptop or mobile camera
    - 🔊 Alert sounds when trash is detected
    - 📸 Automatic snapshot storage
    - 📊 Detection history and analytics
    - ☁️ Cloud storage with Supabase
    - 📱 Mobile camera support via IP Webcam
    
    **How It Works:**
    1. Captures video frames from your camera
    2. Runs YOLOv8 object detection model
    3. Identifies trash objects in the frame
    4. Draws bounding boxes and labels
    5. Logs detections to Supabase database
    6. Stores snapshots in cloud storage
    
    **Detectable Objects:**
    - Bottles, cups, cans
    - Food waste, containers
    - Plastic bags, wrappers
    - And more...
    
    **Setup Instructions:**
    1. Create a Supabase project at supabase.com
    2. Run the SQL setup from supabase_setup.sql
    3. Copy your API credentials to .streamlit/secrets.toml
    4. Run: `streamlit run app.py`
    
    **Troubleshooting:**
    - Camera not working? Check permissions and close other apps using camera
    - Supabase not connecting? Verify credentials in secrets.toml
    - Nothing detected? Lower confidence threshold and ensure good lighting
    - Poor FPS? Lower video resolution or disable snapshots
    
    **Tech Stack:**
    - YOLOv8 (object detection)
    - Streamlit (web framework)
    - Supabase (database + storage)
    - OpenCV (image processing)
    - Python 3.9+
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "TrashWatch © 2024 | Built with YOLOv8 + Streamlit + Supabase"
    "</p>",
    unsafe_allow_html=True
)
