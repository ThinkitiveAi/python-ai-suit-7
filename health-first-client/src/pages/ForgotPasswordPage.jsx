import React, { useState } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  Link, 
  CircularProgress,
  Alert,
  Container
} from '@mui/material';
import { LocalHospital, ArrowBack } from '@mui/icons-material';
import { useFormik } from 'formik';
import { Link as RouterLink } from 'react-router-dom';
import * as Yup from 'yup';

const forgotPasswordSchema = Yup.object().shape({
  email: Yup.string()
    .email('Enter a valid email')
    .required('Email is required'),
});

const ForgotPasswordPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [resetStatus, setResetStatus] = useState(null);

  const handleResetPassword = async (values) => {
    setIsLoading(true);
    setResetStatus(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // For demo purposes, simulate a successful password reset request
      console.log('Password reset requested for:', values.email);
      setResetStatus({
        type: 'success',
        message: 'Password reset instructions have been sent to your email address.'
      });
    } catch (error) {
      setResetStatus({
        type: 'error',
        message: 'Failed to process your request. Please try again.'
      });
      console.error('Password reset error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formik = useFormik({
    initialValues: {
      email: '',
    },
    validationSchema: forgotPasswordSchema,
    onSubmit: handleResetPassword,
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f0f9ff',
        backgroundImage: 'linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center',
            mb: 4
          }}
        >
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              mb: 2 
            }}
          >
            <LocalHospital 
              sx={{ 
                fontSize: 40, 
                color: 'primary.main', 
                mr: 1 
              }} 
            />
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700, 
                color: 'primary.main' 
              }}
            >
              Health First
            </Typography>
          </Box>
          <Typography 
            variant="h5" 
            component="h2" 
            sx={{ 
              fontWeight: 600, 
              mb: 1,
              textAlign: 'center'
            }}
          >
            Forgot Password
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary" 
            sx={{ 
              mb: 3,
              textAlign: 'center'
            }}
          >
            Enter your email to reset your password
          </Typography>
        </Box>

        <Card 
          elevation={4}
          sx={{
            borderRadius: 3,
            overflow: 'visible',
            position: 'relative',
          }}
        >
          {resetStatus && (
            <Alert 
              severity={resetStatus.type} 
              sx={{ 
                borderTopLeftRadius: 12, 
                borderTopRightRadius: 12 
              }}
            >
              {resetStatus.message}
            </Alert>
          )}
          
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={formik.handleSubmit}>
              <TextField
                fullWidth
                id="email"
                name="email"
                label="Email Address"
                type="email"
                placeholder="Enter your registered email"
                value={formik.values.email}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.email && Boolean(formik.errors.email)}
                helperText={formik.touched.email && formik.errors.email}
                margin="normal"
                InputProps={{
                  sx: { borderRadius: 2 }
                }}
                sx={{ mb: 3 }}
              />
              
              <Button
                fullWidth
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                disabled={isLoading}
                sx={{ 
                  py: 1.5,
                  mb: 2,
                  fontWeight: 600
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Reset Password'
                )}
              </Button>
              
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Link
                  component={RouterLink}
                  to="/login"
                  underline="hover"
                  sx={{ 
                    color: 'primary.main',
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <ArrowBack sx={{ fontSize: 16, mr: 0.5 }} />
                  Back to Login
                </Link>
              </Box>
            </form>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default ForgotPasswordPage;
