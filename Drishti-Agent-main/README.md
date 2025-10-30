# Drishti Agent

Drishti Agent is a multi-component research/demo project that combines computer vision, edge processing, backend services, and web frontends to simulate an incident-detection and response system.

This repository contains several components used for demos and development:

- `backend/` – Python backend services, models and APIs; includes `main.py`, `main_dev.py`, and `main_demo.py`.
- `back-fe/` – Backend-facing frontend (TypeScript/React/Vite) used by demos.
- `frontend/` – Another frontend client (similar structure to `back-fe`).
- `cloud_functions/` – Firebase Cloud Functions (Node.js) for event-based triggers.
- `data/` – (empty in repo) data assets.
- `data_simulation/` – Dummy data for simulating sensors, responders, and social posts.
- `simulated_edge/` – Edge processing simulation code (Python).
- `streamlit_ui/` – Streamlit demo app and API client.

## Quick start (dev)

Prerequisites
- Python 3.10+ (or the project's target Python)
- Node.js 16+ and npm or yarn
- Docker (optional, for container builds)

Backend (Python)
1. Create and activate a virtual environment (PowerShell example):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the dev backend (choose the file appropriate for your use-case):

```powershell
# development server
python main_dev.py

# demo runner
python main_demo.py

# production-ish run
python main.py
```

Frontend (back-fe / frontend)
1. Install dependencies and run dev server (example for `back-fe`):

```powershell
cd ..\back-fe
npm install
npm run dev
```

Check `package.json` in each frontend folder for the exact start command (`npm run dev` or `npm start`).

Streamlit UI

```powershell
cd ..\streamlit_ui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Docker (backend)

```powershell
cd ..\backend
# build
docker build -t drishti-agent:latest .
# run (adjust ports/env as needed)
docker run --rm -p 8000:8000 drishti-agent:latest
```

Useful scripts
- `run_demo.sh` – demo startup script (Linux/macOS); on Windows open and adapt or run inside WSL.
- `verify_setup.sh` – helper script to validate environment (bash).

Cloud Functions
- `cloud_functions/functions/` contains Node.js Cloud Functions. Deploy using the Firebase CLI from that folder.

Data and Simulation
- `data_simulation/` contains sample JSON and pre-recorded videos used by the demos.
- `simulated_edge/` contains an edge processor simulation.

Developer notes
- There are multiple frontends (`back-fe`, `frontend`, `fee`) — check each `package.json` to see which one you should run for your use-case.
- Some modules include mocks for easier local development (e.g., `backend/services/mock_*`).

Contributing
- Please open issues or pull requests against this repo. Add tests and update README if you change behavior.

License
- Add a LICENSE file to the repository and update this section with the chosen license.

Contact / help
- If you need help running the project, tell me which component you want to run (backend, `back-fe`, `frontend`, streamlit) and your OS; I can provide concrete, step-by-step commands.
