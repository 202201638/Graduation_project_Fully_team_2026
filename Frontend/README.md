# 🏥 Medical System - AI-Powered X-Ray Chest Diagnosis

A modern, responsive web application built with Angular 21 that leverages artificial intelligence to analyze chest X-ray images and detect pneumonia and other respiratory conditions.

## 🌟 Features

### 🤖 AI-Powered Diagnosis
- **Intelligent Image Analysis**: Advanced machine learning algorithms analyze chest X-ray images
- **Pneumonia Detection**: Automatic identification of pneumonia patterns with confidence scores
- **Real-time Processing**: Fast image processing with immediate results
- **Confidence Metrics**: Detailed confidence percentages for diagnosis reliability

### 👥 User Management
- **Secure Authentication**: Login and signup system with password recovery
- **Patient Profiles**: Comprehensive patient record management
- **Role-based Access**: Different access levels for patients and administrators
- **Session Management**: Secure user sessions with automatic logout

### 📊 Medical Records
- **Digital Patient History**: Complete medical record storage and retrieval
- **Search & Filter**: Advanced search capabilities by patient ID, date, or diagnosis
- **Report Generation**: Downloadable detailed medical reports in PDF format
- **Comparison Tools**: Side-by-side comparison of historical scans

### 🎨 Modern UI/UX
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Professional Interface**: Clean, medical-grade design with intuitive navigation
- **Horizontal Navigation**: Modern navbar with smooth transitions and hover effects
- **Dark/Light Theme**: Eye-friendly color schemes for extended usage

### 🔧 Technical Features
- **Angular 21**: Latest Angular framework with standalone components
- **TypeScript**: Type-safe development with enhanced code quality
- **SSR Support**: Server-side rendering for improved SEO and performance
- **Progressive Web App**: PWA capabilities for offline functionality

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/202201638/X-ray-Chest-senior-project-team-2026.git
   cd X-ray-Chest-senior-project-team-2026/Frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   ng serve
   ```

4. **Open your browser**
   Navigate to `http://localhost:4200/`

## 📁 Project Structure

```
Frontend/
├── src/
│   ├── app/
│   │   ├── admin-panel/          # Admin dashboard
│   │   ├── dashboard/            # Main patient dashboard
│   │   ├── forget-password/      # Password recovery
│   │   ├── intro/                # Landing page
│   │   ├── login/                # User authentication
│   │   ├── patient-records/      # Medical records management
│   │   ├── processing/           # AI analysis processing
│   │   ├── profile/              # User profile settings
│   │   ├── result/               # Diagnosis results
│   │   ├── settings/             # Application settings
│   │   ├── shared/               # Shared components
│   │   │   └── navbar/           # Navigation component
│   │   ├── signup/               # User registration
│   │   ├── upload/               # Image upload interface
│   │   └── welcome/              # Welcome page
│   ├── assets/                   # Static assets
│   └── styles/                   # Global styles
├── public/                       # Public assets
└── dist/                         # Build output
```

## 🎯 Key Components

### 🏠 Intro Page
- Engaging landing page with call-to-action
- Overview of system capabilities
- Quick access to login and signup

### 🔐 Authentication System
- Secure user login and registration
- Password recovery functionality
- Session management and security

### 📤 Upload Interface
- Drag-and-drop image upload
- File format validation
- Preview capabilities

### 🧠 AI Processing
- Real-time image analysis
- Progress indicators
- Error handling and feedback

### 📋 Results Dashboard
- Detailed diagnosis results
- Confidence scores and explanations
- Historical comparison tools

## 🛠️ Development Commands

### Development Server
```bash
ng serve
# Runs on http://localhost:4200/
```

### Build for Production
```bash
ng build
# Creates optimized build in dist/ directory
```

### Run Tests
```bash
ng test
# Run unit tests
```

### Linting
```bash
ng lint
# Check code quality and style
```

## 🔧 Configuration

### Environment Variables
Configure application settings in `src/environments/`:
- `environment.ts` - Development settings
- `environment.prod.ts` - Production settings

### Angular Configuration
Main configuration in `angular.json`:
- Build optimization settings
- Server-side rendering configuration
- Asset management

## 🌐 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 📱 Responsive Design

The application is fully responsive and optimized for:
- 🖥️ Desktop (1200px+)
- 💻 Laptop (768px - 1199px)
- 📱 Tablet (480px - 767px)
- 📱 Mobile (<480px)

## 🔒 Security Features

- Input validation and sanitization
- XSS protection
- Secure file upload handling
- Session management
- CORS configuration

## 🚀 Performance Optimizations

- Lazy loading for routes
- Image optimization
- Bundle size optimization
- Caching strategies
- Service Worker implementation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Development Team

- **Backend Development**: AI/ML Integration
- **Frontend Development**: Angular & UI/UX
- **Medical Consultation**: Radiology Expertise
- **Project Management**: Agile Development

## 📞 Support

For support and inquiries:
- 📧 Email: support@medicalsystem.com
- 🐛 Issues: [GitHub Issues](https://github.com/202201638/X-ray-Chest-senior-project-team-2026/issues)
- 📖 Documentation: [Project Wiki](https://github.com/202201638/X-ray-Chest-senior-project-team-2026/wiki)

## 🙏 Acknowledgments

- Angular Framework team
- Medical imaging research community
- Open source contributors
- Healthcare professionals for validation

---

**⚠️ Medical Disclaimer**: This system is designed as a diagnostic aid and should not replace professional medical judgment. Always consult with qualified healthcare providers for medical decisions.
