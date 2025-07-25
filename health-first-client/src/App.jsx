import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme/theme';

// Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import DashboardPage from './pages/DashboardPage';
import PatientLoginPage from './pages/PatientLoginPage';
import PatientRegistrationPage from './pages/PatientRegistrationPage';

// Layout
import Layout from './components/common/Layout';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/login" replace />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="forgot-password" element={<ForgotPasswordPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="patient">
              <Route path="login" element={<PatientLoginPage />} />
              <Route path="register" element={<PatientRegistrationPage />} />
              <Route path="forgot-password" element={<ForgotPasswordPage />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
