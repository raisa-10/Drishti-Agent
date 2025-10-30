#!/bin/bash
# Project Drishti - Final Setup Verification Script

echo "🔍 PROJECT DRISHTI - FINAL VERIFICATION"
echo "======================================="

cd backend

echo "1️⃣ Checking Python dependencies..."
python -c "
import sys
print(f'Python version: {sys.version}')

required_packages = [
    'fastapi', 'uvicorn', 'google.cloud.firestore', 'google.cloud.vision',
    'google.cloud.aiplatform', 'firebase_admin', 'googlemaps', 'geopy',
    'numpy', 'opencv-python', 'Pillow', 'pandas', 'scikit-learn'
]

missing = []
for pkg in required_packages:
    try:
        __import__(pkg.replace('-', '_').replace('.', '_'))
        print(f'✅ {pkg}')
    except ImportError:
        missing.append(pkg)
        print(f'❌ {pkg} - MISSING')

if missing:
    print(f'\\n🚨 Missing packages: {missing}')
    print('Run: pip install -r requirements.txt')
else:
    print('\\n✅ All required packages are installed!')
"

echo ""
echo "2️⃣ Checking environment variables..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['GCP_PROJECT_ID', 'FIREBASE_STORAGE_BUCKET']
missing = []

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f'✅ {var} = {value}')
    else:
        missing.append(var)
        print(f'❌ {var} - NOT SET')

if missing:
    print(f'\\n🚨 Missing environment variables: {missing}')
    print('Update your .env file!')
else:
    print('\\n✅ All required environment variables are set!')
"

echo ""
echo "3️⃣ Testing service imports..."
python -c "
import logging
logging.basicConfig(level=logging.WARNING)  # Suppress info logs

try:
    from services.firebase_service import FirebaseService
    print('✅ FirebaseService import')
except Exception as e:
    print(f'❌ FirebaseService import failed: {e}')

try:
    from services.vision_analysis import VisionAnalysisService
    print('✅ VisionAnalysisService import')
except Exception as e:
    print(f'❌ VisionAnalysisService import failed: {e}')

try:
    from services.gemini_agent import VertexAIGeminiAgentService
    print('✅ VertexAIGeminiAgentService import')
except Exception as e:
    print(f'❌ VertexAIGeminiAgentService import failed: {e}')

try:
    from services.forecasting_model import ForecastingService
    print('✅ ForecastingService import')
except Exception as e:
    print(f'❌ ForecastingService import failed: {e}')

try:
    from services.google_maps_service import GoogleMapsService
    print('✅ GoogleMapsService import')
except Exception as e:
    print(f'❌ GoogleMapsService import failed: {e}')

try:
    from utils.data_models import Location, ManualCommand, VideoAnalysisResult
    print('✅ Data models import')
except Exception as e:
    print(f'❌ Data models import failed: {e}')

try:
    from api.v1.routes import router
    print('✅ API routes import')
except Exception as e:
    print(f'❌ API routes import failed: {e}')

print('\\n✅ Service import test completed!')
"

echo ""
echo "4️⃣ Testing data model fixes..."
python -c "
from utils.data_models import Location, ManualCommand

# Test Location with optional coordinates
loc1 = Location(name='Test Location')
print(f'✅ Location with name only: {loc1.name}')

loc2 = Location(name='Test Location', latitude=34.0, longitude=-118.0)
print(f'✅ Location with coordinates: {loc2.name} ({loc2.latitude}, {loc2.longitude})')

# Test ManualCommand without incident_id
cmd = ManualCommand(action='dispatch', notes='Test command')
print(f'✅ ManualCommand without incident_id: {cmd.action}')

print('\\n✅ Data model validation passed!')
"

echo ""
echo "🎯 VERIFICATION COMPLETE!"
echo ""
echo "If all tests show ✅, your project is ready for demo!"
echo ""
echo "Next steps:"
echo "1. Start the backend: python main.py"
echo "2. Run edge simulation: cd ../simulated_edge && python edge_test.py"
echo "3. Test API endpoints with your frontend"
echo ""
echo "Good luck with your hackathon! 🚀"
