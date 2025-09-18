document.addEventListener('DOMContentLoaded', async () => {
    // --- Get all DOM elements ---
    const webcamElement = document.getElementById('webcam');
    const predictBtn = document.getElementById('predict-btn');
    const reportBtn = document.getElementById('report-btn');
    const statusText = document.getElementById('status-text');
    const faceIndicator = document.getElementById('face-indicator');
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsGrid = document.getElementById('results-grid');
    const hrValueElement = document.getElementById('hr-value');
    const bpValueElement = document.getElementById('bp-value');
    const stressValueElement = document.getElementById('stress-value');

    // --- Global variables ---
    let mediaRecorder;
    let recordedChunks = [];
    let faceCheckInterval;
    let model; // Variable to hold the BlazeFace model
    let measurementAborted = false; // NEW: Flag to track if the measurement was stopped early

    // --- 1. Load the BlazeFace Model ---
    async function loadModel() {
        try {
            model = await blazeface.load();
            console.log("BlazeFace model loaded successfully.");
            statusText.textContent = "Initializing camera...";
        } catch (err) {
            console.error("Error loading model:", err);
            statusText.textContent = "Error: Could not load face detection model.";
            faceIndicator.textContent = 'Error';
        }
    }
    
    // --- 2. Initialize Webcam and Start Processes ---
    async function initializeWebcam() {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                webcamElement.srcObject = stream;
                
                webcamElement.onloadedmetadata = () => {
                    predictBtn.disabled = false;
                    statusText.textContent = "Ready to start monitoring.";

                    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
                    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recordedChunks.push(e.data); };
                    
                    // --- EDITED: Check flag before sending to server ---
                    mediaRecorder.onstop = () => {
                        // Only send to server if the measurement was not aborted
                        if (!measurementAborted) {
                            const videoBlob = new Blob(recordedChunks, { type: 'video/webm' });
                            sendToServerForPrediction(videoBlob);
                        }
                        recordedChunks = []; // Always clear chunks
                    };

                    if (model) {
                        faceCheckInterval = setInterval(detectFace, 500);
                    }
                };
            } catch (err) {
                console.error("Webcam Error:", err);
                statusText.textContent = "Error: Could not access webcam.";
            }
        }
    }

    // --- 3. Face Detection Logic ---
    async function detectFace() {
        // This function remains the same
        if (!model || webcamElement.readyState < 2) return;
        try {
            const predictions = await model.estimateFaces(webcamElement, false);
            if (predictions.length > 0) {
                faceIndicator.textContent = 'Face Detected';
                faceIndicator.className = 'status-indicator green';
            } else {
                faceIndicator.textContent = 'No Face Detected';
                faceIndicator.className = 'status-indicator red';
            }
        } catch (err) { console.error("Face detection error:", err); }
    }

    // --- 4. Handle Measurement (MAJOR UPDATE) ---
    function startMeasurement() {
        if (!faceIndicator.classList.contains('green')) {
            statusText.textContent = "Please ensure your face is detected before starting.";
            setTimeout(() => {
                if(statusText.textContent === "Please ensure your face is detected before starting."){
                   statusText.textContent = "Ready to start monitoring.";
                }
            }, 3000);
            return;
        }

        resultsPlaceholder.style.display = 'block';
        resultsGrid.style.display = 'none';
        predictBtn.disabled = true;
        measurementAborted = false; // Reset the abort flag

        const measurementDuration = 30000;
        let countdown = measurementDuration / 1000;
        
        // --- NEW: Logic to abort if face is lost ---
        let faceLostCounter = 0;
        const faceLostThreshold = 3; // Abort after 3 consecutive seconds of no face

        statusText.textContent = `Recording... ${countdown}s remaining`;
        
        const measurementInterval = setInterval(() => {
            countdown--;
            statusText.textContent = `Recording... ${countdown}s remaining`;

            // Check face status every second
            if (faceIndicator.classList.contains('green')) {
                faceLostCounter = 0; // Reset counter if face is found
            } else {
                faceLostCounter++; // Increment counter if face is lost
            }

            // If face is lost for too long, abort the measurement
            if (faceLostCounter >= faceLostThreshold) {
                clearInterval(measurementInterval); // Stop this interval
                mediaRecorder.stop();
                measurementAborted = true; // Set the flag
                statusText.textContent = 'Face lost during measurement. Please try again.';
                predictBtn.disabled = false; // Re-enable button
                return;
            }

            // If countdown finishes normally, stop the interval
            if (countdown <= 0) {
                clearInterval(measurementInterval);
            }
        }, 1000);

        mediaRecorder.start();
        setTimeout(() => {
            if (mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                // Only show processing message if not aborted
                if (!measurementAborted) {
                    statusText.textContent = 'Processing... Please wait.';
                }
            }
        }, measurementDuration);
    }

    // --- 5. Send to Server ---
    async function sendToServerForPrediction(blob) {
        const formData = new FormData();
        formData.append('video_blob', blob, 'recording.webm');
        try {
            const response = await fetch('/predict', { method: 'POST', body: formData });
            if (!response.ok) {
                const errData = await response.json().catch(() => ({ error: 'Server returned an error.' }));
                throw new Error(errData.error || `Prediction failed.`);
            }
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error('Prediction Error:', error);
            statusText.textContent = `Error: ${error.message}`;
        } finally {
            predictBtn.disabled = false;
        }
    }
    
    // --- 6. Display Results ---
    function displayResults(data) {
        resultsPlaceholder.style.display = 'none';
        resultsGrid.style.display = 'flex';
        hrValueElement.textContent = `${data.heart_rate} bpm`;
        bpValueElement.textContent = `${data.systolic_bp}/${data.diastolic_bp} mmHg`;
        
        let stress = 'Normal';
        if (data.heart_rate > 100 || data.systolic_bp > 135) stress = 'High';
        else if (data.heart_rate > 85 || data.systolic_bp > 125) stress = 'Moderate';
        stressValueElement.textContent = stress;

        statusText.textContent = 'Measurement complete. Ready to start monitoring.';
    }
    
    // --- Event Listeners and Initialization ---
    predictBtn.addEventListener('click', startMeasurement);
    reportBtn.addEventListener('click', () => window.location.href = '/download_report');
    await loadModel();
    await initializeWebcam();
});

