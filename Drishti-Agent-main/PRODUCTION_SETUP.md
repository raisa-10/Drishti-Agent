# Project Drishti - Production Setup Guide

## Prerequisites for Production Deployment

### 1. Google Cloud Setup with gcloud CLI

Make sure you have authenticated with gcloud and set your project:

```bash
# Login to Google Cloud
gcloud auth login

# Set your project (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com

# Set application default credentials
gcloud auth application-default login
```

### 2. Environment Configuration

Update your `.env` file with your actual values:

```bash
# Replace these placeholders in backend/.env
GOOGLE_CLOUD_PROJECT=your-actual-project-id
FIREBASE_STORAGE_BUCKET=your-actual-project-id.appspot.com
SECRET_KEY=your-secure-production-secret-key
FRONTEND_URL=https://your-production-domain.com
```

### 3. Firestore Database Setup

```bash
# Create Firestore database (if not exists)
gcloud firestore databases create --region=us-central1

# Set Firestore in Native mode
gcloud alpha firestore databases update --type=firestore-native
```

### 4. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Test Your Setup

Run this command to verify all services can initialize:

```bash
cd backend
python -c "
from main import app
import logging
logging.basicConfig(level=logging.INFO)
print('Testing service initialization...')
try:
    # This will trigger the lifespan startup
    import uvicorn
    print('✅ All imports successful')
    print('Ready to start server!')
except Exception as e:
    print(f'❌ Setup issue: {e}')
"
```

### 6. Start the Production Server

```bash
cd backend
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Verify API Endpoints

Test your API:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/system/status
```

## Edge Device Integration

Your edge detection system (`edge_test.py`) is already configured to work with the backend. Make sure:

1. Set the correct backend URL in your edge device:
```bash
# In simulated_edge/.env
BACKEND_API_URL=http://your-backend-server:8000/api/v1/trigger-anomaly
VIDEO_FILE_PATH=data_simulation/pre_recorded_videos/crowd_surge_demo.mp4
```

2. Test edge integration:
```bash
cd simulated_edge
python edge_test.py
```

## Security Considerations for Production

1. **Firewall Rules**: Restrict access to your backend
2. **HTTPS**: Use SSL certificates for production
3. **API Keys**: Rotate your secret keys regularly
4. **IAM**: Use least-privilege access for service accounts
5. **Monitoring**: Set up Cloud Monitoring and Logging

## Troubleshooting

### Common Issues:

1. **Authentication Error**:
   ```bash
   gcloud auth application-default login
   ```

2. **Project Not Set**:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **API Not Enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

4. **Firestore Not Initialized**:
   ```bash
   gcloud firestore databases create --region=us-central1
   ```

## Production Deployment Options

### Option 1: Google Cloud Run
```bash
# Build and deploy to Cloud Run
gcloud run deploy drishti-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 2: Google Compute Engine
```bash
# Deploy to VM instance
gcloud compute instances create drishti-vm \
  --machine-type=n1-standard-2 \
  --zone=us-central1-a \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud
```

### Option 3: Google Kubernetes Engine
```bash
# Deploy to GKE cluster
kubectl apply -f kubernetes-manifests/
```

Your system is now configured for production deployment with Google Cloud services!
