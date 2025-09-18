# 1. Start with a lightweight, official Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only the requirements file first to leverage Docker's caching
COPY backend/requirements.txt .

# 4. Install all the Python libraries your project needs
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your entire project (all folders and files) into the container
COPY . .

# 6. Expose the port that Google Cloud expects
EXPOSE 8080

# 7. The command to start your web server when the container launches
#    --bind 0.0.0.0:8080: Run on port 8080
CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0"]
```
*I've also added a few recommended Gunicorn settings for performance.*

---

### **Step 2: Build and Push Your Docker Image**

Next, you will build your application's "shipping container" (the Docker image) and upload it to Google's private storage, called the Artifact Registry.

Open your command prompt or terminal (like Git Bash) in your main `VitalLens/` project folder and run these commands one by one.

1.  **Log in to Google Cloud:**
    ```bash
    gcloud auth login
    ```

2.  **Set your Project ID:** (You can find your Project ID on your Google Cloud dashboard)
    ```bash
    gcloud config set project YOUR_PROJECT_ID
    ```

3.  **Enable the necessary APIs:**
    ```bash
    gcloud services enable run.googleapis.com
    gcloud services enable artifactregistry.googleapis.com
    ```

4.  **Create an Artifact Registry repository:** (This is a one-time setup)
    ```bash
    gcloud artifacts repositories create vitallens-repo --repository-format=docker --location=asia-south1 --description="Docker repository for VitalLens"
    ```

5.  **Build the Docker image:** (This command builds the "container" from your `Dockerfile`. This may take a few minutes. Don't miss the `.` at the end!)
    ```bash
    docker build -t vitallens-app .
    ```

6.  **Tag the image for upload:** (Replace `YOUR_PROJECT_ID` with your actual ID)
    ```bash
    docker tag vitallens-app asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/vitallens-repo/vitallens-app
    ```

7.  **Configure Docker to authenticate with Google:**
    ```bash
    gcloud auth configure-docker asia-south1-docker.pkg.dev
    ```

8.  **Push the image to the Artifact Registry:** (This uploads your container to Google's storage)
    ```bash
    docker push asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/vitallens-repo/vitallens-app
    ```

---

### **Step 3: Deploy to Cloud Run**

This is the final step. You will tell Cloud Run to take the image you just uploaded and launch it as a public web service.

Run this single, powerful command in your terminal. **This is where you solve the memory and timeout problems.**

```bash
gcloud run deploy vitallens-service \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/vitallens-repo/vitallens-app \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300s

