import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os
from ml_processor import process_video_for_ippg, extract_features

# --- Configuration ---
# This script assumes it's being run from the 'backend' directory.
TRAINING_DATA_PATH = '../training_data/'
VIDEO_FOLDER = os.path.join(TRAINING_DATA_PATH, 'videos')
LABELS_FILE = os.path.join(TRAINING_DATA_PATH, 'labels.csv')
MODEL_SAVE_PATH = 'trained_model/vital_signs_model.pkl'

# --- 1. Load Labels ---
print("Loading labels...")
try:
    labels_df = pd.read_csv(LABELS_FILE)
except FileNotFoundError:
    print(f"ERROR: The labels file was not found at {LABELS_FILE}")
    print("Please make sure your 'labels.csv' file is in the 'training_data' folder.")
    exit()

print(f"Found labels for {len(labels_df)} videos.")

# --- 2. Process Videos and Extract Features ---
print("\nProcessing videos and extracting iPPG features...")
print("This may take some time depending on the number and length of your videos.")
all_features = []
all_labels = []

for index, row in labels_df.iterrows():
    # Assumes the 'filename' column does NOT have an extension.
    filename = row['filename']
    video_path = os.path.join(VIDEO_FOLDER, f"{filename}.mp4") # Assumes all videos are .mp4

    if not os.path.exists(video_path):
        print(f"  - WARNING: Video file not found for '{filename}', skipping.")
        continue

    print(f"  - Processing: {filename}.mp4")
    # Process the video to get the clean iPPG signal
    ippg_signal = process_video_for_ippg(video_path)
    
    if ippg_signal is not None and len(ippg_signal) > 0:
        # Extract statistical features from the signal
        features = extract_features(ippg_signal)
        all_features.append(features)
        
        # We will predict systolic, diastolic, and heart rate together
        all_labels.append([row['systolic_bp'], row['diastolic_bp'], row['heart_rate']])
    else:
        print(f"  - WARNING: Could not extract a valid signal for '{filename}', skipping.")

if not all_features:
    print("\nERROR: No features were extracted. Could not train the model.")
    print("Please check your video files and ensure they contain detectable faces.")
    exit()

X = np.array(all_features)
y = np.array(all_labels)

# --- 3. Train the Machine Learning Model ---
print("\nTraining the model...")
# Split data into training and a small test set for validation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Using RandomForestRegressor as it's robust and good for this type of task
# It can predict multiple values at once (multi-output)
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1) # n_jobs=-1 uses all available CPU cores
model.fit(X_train, y_train)

# --- 4. Evaluate the Model ---
print("\nEvaluating model performance on the test set...")
predictions = model.predict(X_test)
mae = mean_absolute_error(y_test, predictions, multioutput='raw_values')
print(f"  - Mean Absolute Error for Systolic BP: {mae[0]:.2f}")
print(f"  - Mean Absolute Error for Diastolic BP: {mae[1]:.2f}")
print(f"  - Mean Absolute Error for Heart Rate: {mae[2]:.2f} bpm")

# --- 5. Save the Trained Model ---
print(f"\nSaving trained model to: {MODEL_SAVE_PATH}")
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
joblib.dump(model, MODEL_SAVE_PATH)

print("\n-----------------------------------------")
print("✅ Training complete! Your model is ready.")
print("-----------------------------------------")
