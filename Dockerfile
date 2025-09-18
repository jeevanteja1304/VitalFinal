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

