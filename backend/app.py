from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np
import pandas as pd
import os
import cv2
import uuid # NEW: Import the library for generating unique IDs
from ml_processor import get_filtered_signal, extract_features, face_cascade
from report_generator import create_report

# --- App Configuration ---
app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.secret_key = 'your_super_secret_key'

# --- User Management Setup ---
USERS_FILE = 'users.csv'
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=['username', 'password']).to_csv(USERS_FILE, index=False)

# --- Load the Trained Model ---
model = joblib.load('trained_model/vital_signs_model.pkl')

# --- Routes for Authentication and Pages ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data['username']
        password = data['password']
        
        users_df = pd.read_csv(USERS_FILE)
        user_data = users_df[users_df['username'] == username]
        
        if not user_data.empty and check_password_hash(user_data.iloc[0]['password'], password):
            session['user'] = username
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data['username']
        password = data['password']
        
        users_df = pd.read_csv(USERS_FILE)
        if username in users_df['username'].values:
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
            
        hashed_password = generate_password_hash(password)
        new_user = pd.DataFrame([{'username': username, 'password': hashed_password}])
        new_user.to_csv(USERS_FILE, mode='a', header=False, index=False)
        
        return jsonify({'success': True})
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    display_name = session['user'].split('@')[0].capitalize()
    return render_template('home.html', username=display_name)

# --- API Routes ---
@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if not request.files.get('video_blob'): return jsonify({'error': 'No video blob received.'}), 400
    
    file = request.files.get('video_blob')
    
    # --- EDITED: Generate a unique filename for each request ---
    unique_id = uuid.uuid4()
    temp_video_path = f"temp_{session['user']}_{unique_id}.webm"
    file.save(temp_video_path)

    try:
        # --- HIGH ACCURACY PROCESSING ---
        cap = cv2.VideoCapture(temp_video_path)
        raw_signal = []
        frame_rate = cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 30

        total_frames = 0
        face_detected_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            total_frames += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) > 0:
                face_detected_frames += 1
                faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                x,y,w,h = faces[0]
                forehead_x = x + int(0.25 * w)
                forehead_y = y + int(0.1 * h)
                forehead_w = int(0.5 * w)
                forehead_h = int(0.15 * h)
                roi = frame[forehead_y:forehead_y + forehead_h, forehead_x:forehead_x + forehead_w]
                
                if roi.size > 0:
                    raw_signal.append(np.mean(roi[:, :, 1]))
                else:
                    raw_signal.append(0)
            else: 
                raw_signal.append(0)

        # --- Face Detection Consistency Check ---
        if total_frames > 0:
            detection_ratio = face_detected_frames / total_frames
            if detection_ratio < 0.8:
                return jsonify({'error': 'Face not detected consistently. Please try again.'}), 400

        if len(raw_signal) < 20: return jsonify({'error': 'Signal quality too low. Please try again.'}), 400

        filtered_signal = get_filtered_signal(np.array(raw_signal), fs=frame_rate)
        features = extract_features(filtered_signal)
        prediction = model.predict([features])[0]
        
        result = {
            'systolic_bp': round(prediction[0]),
            'diastolic_bp': round(prediction[1]),
            'heart_rate': round(prediction[2])
        }
        
        session['last_measurement'] = result
        return jsonify(result)

    finally:
        # --- CLEANUP BLOCK ---
        # This code is GUARANTEED to run, ensuring the file lock is released
        # before we attempt to delete the file.
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)


@app.route('/download_report')
def download_report():
    if 'user' not in session: return redirect(url_for('login'))
    if 'last_measurement' not in session: return "No measurement found.", 404

    username = session['user']
    vitals = session['last_measurement']
    report_path = create_report(username, vitals)
    
    return send_file(report_path, as_attachment=True)

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)

