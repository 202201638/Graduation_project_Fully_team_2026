# Medical AI System

Unified graduation project repository for a public-beta chest X-ray pneumonia detection web app.

## Repository Layout

- `Backend/`: FastAPI API, MongoDB persistence, authentication, patient records, and model inference.
- `Frontend/`: Angular app for doctor signup/login, patient creation, upload, result, and saved records.
- `ai/`: reproducible training/evaluation utilities, model preflight, model promotion, and smoke-test helpers.
- `documentation/`: reports, slides, and project supporting documents.

Multiple `.gitignore` files are intentional. The root file handles shared generated output, while `Frontend/.gitignore` and `ai/.gitignore` keep framework-specific caches, datasets, and training artifacts out of git.

## Current Beta Product Flow

1. A doctor creates an account or logs in.
2. A new account starts empty: no default patients, no manual history, and no demo account activity.
3. The doctor creates one or more patient records.
4. The doctor uploads an X-ray for an existing patient.
5. The authenticated app uses `POST /api/xray/upload`, saves the analysis in MongoDB, and redirects to the result page.
6. Dashboard, records, profile activity, result refresh, and comparison load from authenticated backend history.

The public `POST /api/xray/analyze` endpoint remains available as a non-persistent demo/dev endpoint. The logged-in app uses authenticated persistent APIs by default.

## Model Handoff

The deployed default model is `fasterrcnn`, configured in `Backend/model_assets/manifest.json`.

Detection models can localize likely pneumonia regions and render boxes:

- `fasterrcnn`
- `yolo`
- `retinanet`

Classification models only return whole-image probabilities and cannot draw pneumonia regions:

- `resnet50`
- `densenet121`
- `efficientnet_b0`

Required deployable model assets in `Backend/model_assets`:

- `manifest.json`
- `fasterrcnn.pt`
- `phase3_baseline_results.json`
- `web_result.json`
- `demo_output.png`

Optional but supported assets:

- `yolo_best.pt`
- `retinanet.pt`
- `resnet50.pt`
- `densenet121.pt`
- `efficientnet_b0.pt`
- `phase8_demo_result.json`
- `kaggle_notebook_summary.json`

## Backend Setup

```powershell
cd "D:\Collage\graduation project\Backend"
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `Backend/.env` before deploying:

```env
APP_ENV=development
MONGODB_URL=mongodb://localhost:27017/medical_system
SECRET_KEY=change-this-to-a-random-32-plus-character-secret-before-deploy
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

Production requirements:

- Set `APP_ENV=production`.
- Set a strong unique `SECRET_KEY` with at least 32 characters.
- Set `CORS_ORIGINS` to the deployed frontend origin.
- Keep `DEBUG=False`; the `/debug` route is only registered when debug mode is enabled.
- Configure MongoDB. Authentication, patients, and stored analysis history require MongoDB.

Run backend locally:

```powershell
cd "D:\Collage\graduation project\Backend"
.\venv\Scripts\activate
python main.py
```

Production-style startup:

```powershell
cd "D:\Collage\graduation project\Backend"
.\venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Useful backend URLs:

- API root: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Model status: `http://localhost:8000/api/xray/status`
- Model metadata: `http://localhost:8000/api/xray/metadata`

## Frontend Setup

```powershell
cd "D:\Collage\graduation project\Frontend"
npm install
npm start
```

Frontend URL:

- `http://localhost:4200`

The frontend backend URL is configured in `Frontend/src/environments/environment.ts`. For deployment, set the runtime global `window.__MEDISCAN_API_BASE_URL__` before the Angular app boots, or update the environment file during your deploy build.

## AI Pipeline Setup

```powershell
cd "D:\Collage\graduation project\ai"
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python -m compileall main.py src
```

Run preflight checks:

```powershell
python -c "from src.preflight import run_preflight_checks; run_preflight_checks()"
```

Dry-run model promotion:

```powershell
python -m src.model_promotion --metric recall
```

Apply model promotion only when you intentionally want to copy deployable assets into `Backend/model_assets`:

```powershell
python -m src.model_promotion --metric recall --apply
```

Run backend inference smoke tests after starting the backend:

```powershell
python -m src.inference_smoke --backend-url http://localhost:8000 --model-name fasterrcnn --limit 2
```

## Authenticated API Summary

Authentication:

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`

Patients:

- `POST /api/patients/`
- `GET /api/patients/list`
- `GET /api/patients/{patient_id}`
- `PUT /api/patients/{patient_id}`
- `DELETE /api/patients/{patient_id}`

X-ray history:

- `POST /api/xray/upload`
- `GET /api/xray/`
- `GET /api/xray/{analysis_id}`
- `DELETE /api/xray/{analysis_id}`

Demo/dev inference:

- `POST /api/xray/analyze`

## Verification Commands

Backend:

```powershell
cd "D:\Collage\graduation project\Backend"
.\venv\Scripts\activate
python -m pytest -q
```

Frontend:

```powershell
cd "D:\Collage\graduation project\Frontend"
npm test
npm run build
```

AI:

```powershell
cd "D:\Collage\graduation project\ai"
python -m compileall main.py src
```

Manual beta acceptance:

1. Start MongoDB, backend, and frontend.
2. Create a new doctor account.
3. Confirm dashboard, records, and profile activity are empty.
4. Create a patient.
5. Upload a chest X-ray for that patient.
6. Confirm the result page shows the model output and rendered image.
7. Open records, refresh the browser, and confirm the saved scan remains.
