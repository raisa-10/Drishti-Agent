# Use an official, slim Python runtime as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed by some Python libraries (like OpenCV)
# This is a robust way to prevent common installation errors.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install the Python dependencies with increased timeout and no cache
RUN pip install --no-cache-dir --timeout=120 -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Tell Cloud Run what port the application will be listening on
# The PORT environment variable is automatically set by Cloud Run to 8080.
ENV PORT 8080
EXPOSE 8080

# Define the command to run your application using Uvicorn
# Use the PORT environment variable that Cloud Run provides
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
