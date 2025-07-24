# Health First Client

A modern healthcare provider portal built with React and Material UI that allows medical professionals to securely access their healthcare application dashboard.

## Features

- **Provider Login**: Secure authentication with email/phone and password
- **Provider Registration**: Comprehensive multi-step registration process
- **Forgot Password**: Password recovery functionality
- **Dashboard**: Provider dashboard overview
- **Responsive Design**: Mobile-friendly interface
- **Accessibility**: WCAG compliant components

## Tech Stack

- **Frontend Framework**: React with Vite
- **UI Library**: Material UI
- **Form Validation**: Formik with Yup
- **Routing**: React Router
- **Styling**: CSS-in-JS with Emotion

## Color Scheme

- **Primary Color**: Blue (#2563eb)
- **Secondary Color**: Green (#059669)

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project directory
cd health-first-client

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── assets/         # Static assets (images, icons)
├── components/     # Reusable components
│   ├── auth/       # Authentication related components
│   └── common/     # Common UI components
├── pages/          # Page components
├── theme/          # Theme configuration
├── utils/          # Utility functions and validation schemas
├── App.jsx         # Main application component
└── main.jsx        # Application entry point
```

## Features

### Provider Login
- Email/Phone input with validation
- Password with show/hide toggle
- Remember me functionality
- Forgot password link

### Provider Registration
- Multi-step registration process
- Personal information collection
- Professional details
- Practice information
- Account security setup

### Form Validation
- Real-time validation feedback
- Comprehensive validation rules
- Error handling
