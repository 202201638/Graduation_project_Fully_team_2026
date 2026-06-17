# Medical AI System: Full Technical Explanation

This document provides a comprehensive breakdown of the graduation project, explaining the architecture, the role of each component, and how the system functions from end-to-end.

---

## 1. Project Structure & Folders

### 📂 Root Directory (`/`)
The root contains the overall project configuration and links the three main pillars:
- **`Backend/`**: The FastAPI server and AI inference logic.
- **`Frontend/`**: The Angular web application.
- **`ai/`**: Research, training, and evaluation scripts.
- **`documentation/`**: Official project reports and slides.

### 📂 `Backend/` (FastAPI + MongoDB)
This is the "brain" of the web application. It handles logic, security, and AI model execution.
- **`app/database/`**: Contains `mongodb.py`. This connects the app to your database. It uses **Motor**, an asynchronous driver, so the website stays fast even under load.
- **`app/models/`**: Defines **Pydantic** models. These act as "gatekeepers" to ensure that any data sent to the API (like patient info) is in the correct format.
- **`app/routers/`**:
    - `auth.py`: Handles signup/login using JWT (JSON Web Tokens).
    - `patients.py`: Manages patient records (Create, Read, Update, Delete).
    - `xray_analysis.py`: The most important file. It handles X-ray uploads and connects to the AI models.
- **`app/utils/`**:
    - `xray_inference.py`: The core service that loads PyTorch/YOLO models and performs the actual diagnosis.
- **`model_assets/`**: This is where the trained `.pt` files (weights) live. The `manifest.json` tells the backend which model is currently "active."
- **`uploads/`**: Stores original X-rays and the "rendered" images (the ones with boxes drawn on them).

### 📂 `Frontend/` (Angular)
The user interface designed for doctors.
- **`src/app/`**: Contains the pages (Dashboard, Upload, Results, Profile).
- **`analysis-state.service.ts`**: The central "memory" of the frontend. It keeps track of the current analysis and history as the user moves between pages.
- **`api.service.ts`**: The "messenger" that sends requests to the Backend.

### 📂 `ai/` (Training & Research)
This is where the AI development happens. It is separate from the web app so that training doesn't slow down the website.
- **`src/detection/`**: Scripts to train YOLO (YOLOv8n) and Faster R-CNN.
- **`src/classification/`**: Scripts to train ResNet, DenseNet, and EfficientNet.
- **`model_promotion.py`**: A special tool to take a trained model from this folder and "promote" it into the `Backend/model_assets` folder for deployment.

---

## 2. How the System Works (The Workflow)

### 🔄 End-to-End Flow
1. **Authentication**: The doctor logs in. The backend gives them a "token" which they must use for every following step.
2. **Patient Selection**: The doctor selects or creates a patient record.
3. **Upload**: The doctor selects an X-ray image. The Frontend sends this to `POST /api/xray/upload`.
4. **Inference (The AI Part)**:
    - The Backend saves the image.
    - The `XRayInferenceService` picks the best model (default: Faster R-CNN).
    - The model scans the image for patterns of pneumonia.
    - If found, it calculates the **coordinates** (boxes) and a **confidence score**.
5. **Rendering**: The system creates a copy of the image and draws the detection boxes on it so the doctor can visualize the result.
6. **Result**: The Backend saves everything to MongoDB and sends the result back to the Frontend.
7. **Display**: The doctor sees the "Pneumonia Detected" status, the confidence level (e.g., 85%), and specific medical recommendations.

---

## 3. Why we use each Model & Function

### 🤖 Why 5 different models?
We use a **Multi-Model Strategy** to ensure accuracy:
1. **Detection Models (YOLOv8n, Faster R-CNN)**:
   - **Why**: These are "Object Detection" models. They can tell you *where* the pneumonia is. This is essential for doctors to verify the AI's findings.
2. **Classification Models (ResNet50, DenseNet121, EfficientNet-B0)**:
   - **Why**: These are "Image Level" models. They provide a simple Yes/No probability. They are often faster and can be used as a "second opinion" to confirm the detection models.

### ⚙️ Key Functions
- **`nms` (Non-Maximum Suppression)**: AI models often draw multiple boxes on the same spot. NMS cleans this up, keeping only the most confident box.
- **`JWT Authentication`**: Ensures that patient data is private and only accessible by the authorized doctor.
- **`Async/Await`**: Used throughout the backend to handle multiple users simultaneously without the server crashing.

---

## 4. Current Problems & Solutions

### ⚠️ The "Heavy Model" Problem
**Problem**: Loading a 150MB AI model every time someone clicks "Upload" would take 10-20 seconds.
**Solution**: The system uses a **Singleton Warmup**. When the server starts, it loads the model into RAM *once*. Every upload after that is nearly instant.

### ⚠️ The "Black Box" Problem
**Problem**: Doctors don't trust AI if it just says "Pneumonia" without explanation.
**Solution**: We use **Detection Overlays** (drawing boxes) and **Findings/Recommendations** text to explain *why* the AI made its choice.

### ⚠️ The "Stale Model" Problem
**Problem**: As you get more data, your model improves, but updating the website is hard.
**Solution**: The **Model Handoff/Promotion** script. You can train a new model in the `ai/` folder and run one command to update the live website without touching the backend code.

---

## 5. Summary for Graduation Presentation
When presenting this project, emphasize that it is not just an AI script, but a **Full-Stack Clinical Tool**. It solves the gap between "Research" (AI models) and "Practice" (a doctor-friendly website with patient history and secure records).
