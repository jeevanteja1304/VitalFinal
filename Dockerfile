# 1. Start with a lightweight, official Python image that matches your environment
FROM python:3.10-slim

# 2. Set the working directory inside the container to /app
WORKDIR /app

# 3. Copy only the requirements file first. This is a Docker optimization that
#    prevents re-installing all libraries every time you change your code.
COPY backend/requirements.txt .

# 4. Install all the Python libraries your project needs using the requirements file.
#    The --no-cache-dir flag keeps the final image size smaller.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your entire project (all folders and files) into the container's /app directory
COPY . .

# 6. Expose the port that the application will run on.
#    8080 is the standard for Google Cloud Run, and 7860 for Hugging Face.
#    We will use 8080 as it is a common standard.
EXPOSE 8080

# 7. The command to start your web server when the container launches.
#    --chdir backend: First, change the directory to 'backend'
#    app:app: Then, run the Flask application named 'app' from the 'app.py' file
#    --bind 0.0.0.0:8080: Run on the correct host and port
#    --workers, --threads, --timeout: Recommended settings for stability and performance
CMD ["gunicorn", "--chdir", "backend", "app:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0"]

