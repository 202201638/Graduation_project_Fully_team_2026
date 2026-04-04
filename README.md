
# 🏥 Medical AI System – Pneumonia Detection from Chest X-Rays

An end-to-end **AI-powered medical platform** that detects pneumonia from chest X-ray images using deep learning, combined with a full-stack system for patient management and analytics.

---

## 🚀 Overview

This project integrates **Artificial Intelligence + Full-Stack Development** to support medical professionals in diagnosing pneumonia efficiently.

* ⚡ AI model analyzes chest X-rays
* 📊 Doctors get confidence scores & reports
* 👨‍⚕️ Patient records are fully managed
* 🔐 Secure authentication & data protection

---

## ✨ Key Features

### 🤖 AI Diagnosis

* Pneumonia detection using deep learning
* Confidence score for each prediction
* Automated medical report generation
* Optimized image preprocessing pipeline

### 👥 Patient Management System

* Create & manage patient profiles
* Track medical history
* Record allergies and medications
* Maintain structured medical data

### 🔐 Security & Authentication

* JWT-based authentication
* Role-based access control (RBAC)
* Secure API endpoints
* Data privacy compliance (HIPAA-ready design)

### 📊 Dashboard & Insights

* Real-time analytics dashboard
* X-ray analysis history tracking
* Patient statistics visualization
* System performance monitoring

---

## 🏗️ System Architecture

```
Medical-AI-System/
│
├── Backend/ (FastAPI)
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── database/
│   │   └── utils/
│   ├── main.py
│   └── requirements.txt
│
├── Frontend/ (Angular)
│   ├── src/app/
│   │   ├── components/
│   │   ├── services/
│   │   └── models/
│   └── package.json
│
└── docs/
```

---

## 🧠 Tech Stack

### Backend

* ⚙️ **FastAPI** – High-performance Python API
* 🐍 **Python** – Core backend logic
* 🍃 **MongoDB** – NoSQL database
* 🔐 **JWT** – Authentication

### Frontend

* 🌐 **Angular** – Modern frontend framework
* 🎨 **TypeScript** – Strongly typed JavaScript
* 📡 **REST API Integration**

### AI / ML

* 🧠 Deep Learning Model (CNN)
* 🖼️ Image preprocessing (OpenCV / PIL)
* 📊 Model inference pipeline

---

## ⚙️ Installation & Setup

### 🔹 1. Clone Repository

```bash
git clone https://github.com/202201638/Graduation_project_Fully_team_2026.git
cd Graduation_project_Fully_team_2026
```

---

### 🔹 2. Backend Setup (FastAPI)

```bash
cd Backend

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

Create `.env` file:

```env
MONGODB_URL=mongodb://localhost:27017/medical_ai
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Run server:

```bash
python main.py
```

👉 Backend: [http://localhost:8000](http://localhost:8000)
👉 Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 🔹 3. Frontend Setup (Angular)

```bash
cd Frontend

npm install
ng serve
```

👉 Frontend: [http://localhost:4200](http://localhost:4200)

---

## 📡 API Endpoints

### 🔐 Authentication

* `POST /api/auth/signup`
* `POST /api/auth/login`
* `GET /api/auth/me`

### 👥 Patients

* `POST /api/patients/`
* `GET /api/patients/`
* `PUT /api/patients/`

### 🩻 X-Ray Analysis

* `POST /api/xray/upload`
* `GET /api/xray/`
* `GET /api/xray/{id}`
* `DELETE /api/xray/{id}`

---

## 🧪 Testing

Use **Postman Collection** included in:

```
Backend/Postman_Collection.json
```

### Test Account

```
Email: john.doe@example.com
Password: Secure123
```

---

## 📸 Screenshots

> Add your screenshots here:

* Login Page
* Dashboard
* X-ray Analysis Result
* Patient Management

---

## 📈 Future Improvements

* 🔬 Improve AI model accuracy
* 📱 Mobile app version (React Native)
* ☁️ Cloud deployment (AWS / Azure)
* 🧾 PDF medical reports export
* 🧑‍⚕️ Doctor recommendation system

---

## 👨‍💻 Author

**Ahmed Mohamed**
🎓 Graduation Project – 2026
📌 Project ID: 202201638

* GitHub: [https://github.com/202201638](https://github.com/202201638)

---

## 🤝 Contributing

Contributions are welcome!

```bash
git checkout -b feature/new-feature
git commit -m "Add new feature"
git push origin feature/new-feature
```

---

## 📄 License

This project is licensed under the **MIT License**.

---

## ⭐ Final Note

> This system demonstrates how AI can enhance healthcare by assisting doctors in faster and more accurate diagnosis.
