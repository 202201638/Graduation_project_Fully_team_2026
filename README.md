# Medical AI System

This project now supports an end-to-end chest X-ray inference flow using the YOLO weights stored in `Backend/model_assets/yolo_best.pt`.

## Required model files

Place these files in `Backend/model_assets`:

- Required: `yolo_best.pt`
- Recommended: `manifest.json`
- Recommended: `phase3_baseline_results.json`
- Recommended: `web_result.json`
- Optional: `phase8_demo_result.json`
- Optional: `demo_output.png`

These files are not used by the web integration and are not required:

- `phase1_dataset_summary.json`
- `phase1_conversion_summary.json`
- `phase2_yolo_dataset_summary.json`
- full `png_images/`
- full `yolo_dataset/`
- full `runs/` directories

## What the app does

- Backend loads `yolo_best.pt` through Ultralytics YOLO.
- Backend exposes public web inference and metadata endpoints.
- Frontend upload page sends the selected image to FastAPI.
- Result page shows diagnosis, confidence, rendered output, findings, recommendations, and detection boxes.

## Backend setup

### 1. Open a terminal in the repository root

```powershell
cd "D:\Collage\graduation project\webapp\Graduation_project_Fully_team_2026"
```

### 2. Create or use a Python virtual environment

```powershell
cd Backend
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install backend dependencies

```powershell
python -m pip install -r requirements.txt
```

This installs FastAPI plus the YOLO runtime dependencies, including `ultralytics`, `torch`, and `torchvision`.

### 4. Optional environment variables

Create `Backend/.env` if you want to override defaults:

```env
MONGODB_URL=mongodb://localhost:27017/medical_system
SECRET_KEY=change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Notes:

- MongoDB is optional for the public model demo flow.
- MongoDB is required for authentication, patients, and stored analysis history endpoints.

### 5. Start the backend

```powershell
cd Backend
.\venv\Scripts\activate
python main.py
```

Backend URLs:

- API root: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

## Frontend setup

### 1. Install frontend dependencies

```powershell
cd Frontend
npm install
```

### 2. Start the frontend

```powershell
npm start
```

Frontend URL:

- App: [http://localhost:4200](http://localhost:4200)

## End-to-end web flow

1. Start the backend on port `8000`.
2. Start the frontend on port `4200`.
3. Open [http://localhost:4200/upload](http://localhost:4200/upload).
4. Upload a chest X-ray image in `jpg`, `jpeg`, `png`, `bmp`, or `tiff`.
5. Enter `Patient ID` and `Scan Type`.
6. Click `Analyze X-ray`.
7. The processing page waits for the backend response.
8. The result page shows:
   - diagnosis
   - confidence
   - rendered prediction image
   - original upload
   - findings
   - recommendations
   - detection bounding boxes

Generated inference images are written to `Backend/uploads/`.

## Model endpoints

Public endpoints used by the frontend:

- `GET /api/xray/status`
- `GET /api/xray/metadata`
- `GET /api/xray/metadata/manifest`
- `GET /api/xray/metadata/baseline`
- `GET /api/xray/metadata/web-result`
- `GET /api/xray/metadata/demo-result` if `phase8_demo_result.json` exists
- `POST /api/xray/analyze`

Authenticated history endpoints remain available when MongoDB is configured:

- `POST /api/xray/upload`
- `GET /api/xray/`
- `GET /api/xray/{analysis_id}`
- `DELETE /api/xray/{analysis_id}`

## Verification performed

The following checks were run after the integration:

- Backend Python compile check passed.
- Backend app import passed.
- Real request to `POST /api/xray/analyze` passed using `Backend/model_assets/demo_output.png`.
- `GET /health`, `GET /api/xray/status`, and `GET /api/xray/metadata` all returned `200`.
- Angular production build completed successfully and wrote output to `Frontend/dist/medical_system`.

Observed result from the verified demo request:

- Analysis endpoint returned `200`
- `analysis_id` was generated
- Detection result was `false`
- Confidence was `0.0`
- Rendered output image URL was returned

## Notes

- Ultralytics settings are stored under `Backend/.ultralytics` so the model runtime does not depend on the user profile path.
- The frontend build still emits existing budget warnings for bundle size and `profile.css`, but the production build completes successfully.
