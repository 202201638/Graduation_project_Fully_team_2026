# 🏥 Medical System Backend - FastAPI & MongoDB

A robust RESTful API backend for the AI-powered X-ray chest diagnosis system, built with FastAPI and MongoDB.

## 🚀 Features

### 🔐 Authentication System
- **JWT-based Authentication**: Secure token-based authentication
- **User Registration & Login**: Complete user management
- **Role-based Access**: Support for patients and administrators
- **Password Security**: Bcrypt hashing for secure password storage

### 👥 Patient Management
- **Complete Patient Profiles**: Comprehensive patient information storage
- **Medical History Tracking**: Add and view medical history
- **Allergy Management**: Track patient allergies
- **Medication Records**: Keep track of current medications

### 📊 X-Ray Analysis
- **Image Upload**: Secure file upload with validation
- **AI-Powered Analysis**: Mock pneumonia detection with confidence scores
- **Analysis History**: View all past X-ray analyses
- **Results Management**: Detailed findings and recommendations

### 🗄️ Database Features
- **MongoDB Integration**: NoSQL database for flexible data storage
- **Indexing**: Optimized queries with proper indexing
- **Data Validation**: Pydantic models for data integrity
- **Connection Management**: Async MongoDB connection handling

## 🛠️ Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **MongoDB**: NoSQL database for data storage
- **Motor**: Async MongoDB driver for Python
- **Pydantic**: Data validation and settings management
- **JWT**: JSON Web Tokens for authentication
- **Bcrypt**: Password hashing
- **OpenCV**: Image processing for X-ray analysis
- **Pillow**: Image manipulation
- **Uvicorn**: ASGI server

## 📋 Prerequisites

- Python 3.8+
- MongoDB 4.4+
- pip package manager

## 🚀 Getting Started

### 1. Clone and Navigate
```bash
cd Backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy `.env` file and update if needed:
```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=medical_system

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-2024
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Start MongoDB
Make sure MongoDB is running on your system:
```bash
# Windows (if installed as service)
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
```

### 6. Run the API
```bash
python main.py
```

The API will be available at: `http://localhost:8000`

## 📚 API Documentation

### Interactive Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### API Endpoints

#### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - User logout

#### Patient Management
- `POST /api/patients/` - Create patient record
- `GET /api/patients/` - Get patient record
- `PUT /api/patients/` - Update patient record
- `POST /api/patients/medical-history` - Add medical history
- `POST /api/patients/allergies` - Add allergy
- `POST /api/patients/medications` - Add medication

#### X-Ray Analysis
- `POST /api/xray/upload` - Upload and analyze X-ray
- `GET /api/xray/` - Get all analyses
- `GET /api/xray/{analysis_id}` - Get specific analysis
- `DELETE /api/xray/{analysis_id}` - Delete analysis

#### System
- `GET /` - API root
- `GET /health` - Health check

## 🧪 Testing with Postman

### 1. Import Collection
1. Open Postman
2. Click "Import" 
3. Select the `Postman_Collection.json` file
4. The collection will be imported with all endpoints

### 2. Set Environment Variables
The collection includes these variables:
- `base_url`: `http://localhost:8000`
- `auth_token`: Automatically set after login
- `user_id`: Automatically set after login
- `patient_id`: Automatically set after patient creation
- `analysis_id`: Automatically set after X-ray upload

### 3. Test Sequence
Run the requests in this order:

1. **Authentication Flow**
   - Signup → Login → Get Current User → Logout

2. **Patient Management**
   - Create Patient → Get Patient → Update Patient
   - Add Medical History → Add Allergy → Add Medication

3. **X-Ray Analysis**
   - Upload X-Ray → Get All Analyses → Get Specific Analysis → Delete Analysis

4. **System Checks**
   - Health Check → API Root

### 4. Sample Test Data
```json
// User Registration
{
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "password": "SecurePass123",
    "role": "patient"
}

// Patient Creation
{
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-15",
    "gender": "male",
    "phone": "+1234567890",
    "address": "123 Main St, City, State 12345",
    "emergency_contact": "+1234567891 - Jane Doe"
}
```

## 🗄️ Database Schema

### Users Collection
```javascript
{
    _id: ObjectId,
    user_id: "USR_123ABC456DEF",
    email: "user@example.com",
    full_name: "John Doe",
    role: "patient",
    hashed_password: "bcrypt_hash",
    is_active: true,
    created_at: Date,
    updated_at: Date
}
```

### Patients Collection
```javascript
{
    _id: ObjectId,
    patient_id: "PAT_789GHI012JKL",
    user_id: "USR_123ABC456DEF",
    first_name: "John",
    last_name: "Doe",
    date_of_birth: "1990-01-15",
    gender: "male",
    phone: "+1234567890",
    address: "123 Main St",
    emergency_contact: "Jane Doe",
    medical_history: ["History entry 1"],
    allergies: ["Penicillin"],
    medications: ["Lisinopril 10mg"],
    created_at: Date,
    updated_at: Date
}
```

### X-Ray Analyses Collection
```javascript
{
    _id: ObjectId,
    analysis_id: "ANA_345MNO678PQR",
    patient_id: "PAT_789GHI012JKL",
    image_url: "/uploads/filename.jpg",
    image_filename: "original_name.jpg",
    result: {
        pneumonia_detected: true,
        confidence_score: 0.85,
        findings: "Evidence of bilateral infiltrates...",
        recommendations: "Immediate medical consultation...",
        analysis_details: {...}
    },
    status: "completed",
    processing_time: 2.1,
    created_at: Date,
    updated_at: Date
}
```

## 🔧 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Structure
```
Backend/
├── app/
│   ├── database/          # MongoDB connection
│   ├── models/           # Pydantic models
│   ├── routers/          # API routes
│   └── utils/            # Utility functions
├── tests/                # Test files
├── uploads/              # Uploaded X-ray images
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
└── README.md           # This file
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production
```bash
MONGODB_URL=mongodb://your-production-db:27017
DATABASE_NAME=medical_system_prod
SECRET_KEY=your-very-secure-secret-key
DEBUG=False
```

## 🔒 Security Considerations

- **JWT Tokens**: Use strong, random secret keys
- **Password Hashing**: Bcrypt with appropriate salt rounds
- **Input Validation**: Pydantic models for all inputs
- **File Upload**: Validate file types and sizes
- **CORS**: Configure appropriate origins
- **Rate Limiting**: Consider implementing rate limiting
- **HTTPS**: Use HTTPS in production

## 📈 Performance Optimization

- **Database Indexing**: Proper indexes on frequently queried fields
- **Async Operations**: Async database operations for better concurrency
- **Image Processing**: Efficient image preprocessing
- **Caching**: Consider Redis for frequently accessed data
- **Connection Pooling**: MongoDB connection pooling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string in `.env`
   - Verify network connectivity

2. **Import Errors**
   - Activate virtual environment
   - Install all requirements: `pip install -r requirements.txt`

3. **Authentication Failures**
   - Check JWT secret key
   - Verify token format in headers
   - Ensure token is not expired

4. **File Upload Issues**
   - Check upload directory permissions
   - Verify file size limits
   - Ensure supported file formats

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the test collection for usage examples
