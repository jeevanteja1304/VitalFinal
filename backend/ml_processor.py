import cv2
import numpy as np
from scipy.signal import butter, filtfilt

# --- Configuration ---
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except Exception:
    print("ERROR: Could not load the Haar Cascade face detector.")
    exit()

def get_filtered_signal(signal, low_cutoff=0.75, high_cutoff=4.0, fs=30):
    """
    Applies a Butterworth bandpass filter to the raw signal.
    """
    if signal is None or len(signal) < 20:
        return None
        
    # Safety check for Nyquist frequency
    if fs <= 2 * high_cutoff:
        print(f"Error: Frame rate ({fs} FPS) is too low to reliably detect signals up to {high_cutoff} Hz.")
        return None

    nyquist = 0.5 * fs
    low = low_cutoff / nyquist
    high = high_cutoff / nyquist
    
    b, a = butter(1, [low, high], btype='band')
    
    try:
        filtered_signal = filtfilt(b, a, signal)
        return filtered_signal
    except ValueError:
        return None

def extract_features(signal):
    """
    Calculates key statistical features from the clean iPPG signal.
    """
    if signal is None:
        return None
    return [
        np.mean(signal),
        np.std(signal),
        np.min(signal),
        np.max(signal),
        np.ptp(signal)
    ]

def process_video_for_ippg(video_path):
    """
    This is the main pipeline function. It uses the original reliable logic
    but with frame resizing for a significant speed boost on servers.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return None

    raw_signal = []
    frame_rate = cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 30

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            # --- THE ONLY OPTIMIZATION ---
            # Resize the frame. This is the biggest factor for performance.
            small_frame = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            # Skip corrupted frames
            continue
        
        # Detect faces on the smaller frame
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) > 0:
            faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
            x, y, w, h = faces[0]

            # Define ROI on the small color frame
            forehead_x = x + int(0.2 * w)
            forehead_y = y + int(0.1 * h)
            forehead_w = int(0.6 * w)
            forehead_h = int(0.15 * h)
            
            roi = small_frame[forehead_y : forehead_y + forehead_h, forehead_x : forehead_x + forehead_w]

            if roi.size > 0:
                raw_signal.append(np.mean(roi[:, :, 1]))
            else:
                raw_signal.append(0)
        else:
            raw_signal.append(0)

    cap.release()

    # We are no longer skipping frames, so the frame_rate is accurate
    filtered_signal = get_filtered_signal(np.array(raw_signal), fs=frame_rate)
    
    return filtered_signal

