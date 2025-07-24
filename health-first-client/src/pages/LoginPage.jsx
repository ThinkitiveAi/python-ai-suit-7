import React, { useState } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  TextField, 
  Button, 
  FormControlLabel, 
  Checkbox, 
  Link, 
  InputAdornment, 
  IconButton,
  CircularProgress,
  Alert,
  Container,
  Grid
} from '@mui/material';
import { Visibility, VisibilityOff, LocalHospital } from '@mui/icons-material';
import { useFormik } from 'formik';
import { Link as RouterLink } from 'react-router-dom';
import { loginSchema } from '../utils/validationSchemas';

const LoginPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState(null);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const handleLogin = async (values) => {
    setIsLoading(true);
    setLoginError(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // For demo purposes, simulate a successful login
      console.log('Login successful with:', values);
      
      // Redirect would happen here in a real app
      // history.push('/dashboard');
    } catch (error) {
      setLoginError('Invalid credentials. Please try again.');
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formik = useFormik({
    initialValues: {
      credential: '',
      password: '',
      rememberMe: false,
    },
    validationSchema: loginSchema,
    onSubmit: handleLogin,
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f0f9ff', // Light blue background
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
            Provider Login
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary" 
            sx={{ 
              mb: 3,
              textAlign: 'center'
            }}
          >
            Access your healthcare provider dashboard
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
          {loginError && (
            <Alert 
              severity="error" 
              sx={{ 
                borderTopLeftRadius: 12, 
                borderTopRightRadius: 12 
              }}
            >
              {loginError}
            </Alert>
          )}
          
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={formik.handleSubmit}>
              <TextField
                fullWidth
                id="credential"
                name="credential"
                label="Email or Phone Number"
                placeholder="Enter your email or phone number"
                value={formik.values.credential}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.credential && Boolean(formik.errors.credential)}
                helperText={formik.touched.credential && formik.errors.credential}
                margin="normal"
                InputProps={{
                  sx: { borderRadius: 2 }
                }}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                id="password"
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={formik.values.password}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.password && Boolean(formik.errors.password)}
                helperText={formik.touched.password && formik.errors.password}
                margin="normal"
                InputProps={{
                  sx: { borderRadius: 2 },
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleClickShowPassword}
                        onMouseDown={handleMouseDownPassword}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 1 }}
              />
              
              <Box 
                sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  mb: 3
                }}
              >
                <FormControlLabel
                  control={
                    <Checkbox
                      id="rememberMe"
                      name="rememberMe"
                      color="primary"
                      checked={formik.values.rememberMe}
                      onChange={formik.handleChange}
                    />
                  }
                  label="Remember me"
                />
                
                <Link 
                  component={RouterLink} 
                  to="/forgot-password"
                  underline="hover"
                  sx={{ 
                    color: 'primary.main',
                    fontWeight: 500,
                  }}
                >
                  Forgot Password?
                </Link>
              </Box>
              
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
                  'Login'
                )}
              </Button>
              
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Don't have an account?{' '}
                  <Link
                    component={RouterLink}
                    to="/register"
                    underline="hover"
                    sx={{ 
                      color: 'primary.main',
                      fontWeight: 500
                    }}
                  >
                    Register as a Provider
                  </Link>
                </Typography>
              </Box>
            </form>
          </CardContent>
        </Card>
        
        <Grid 
          container 
          spacing={2} 
          justifyContent="center" 
          sx={{ mt: 4 }}
        >
          <Grid item>
            <Link 
              href="#" 
              underline="hover" 
              color="text.secondary" 
              variant="body2"
            >
              Privacy Policy
            </Link>
          </Grid>
          <Grid item>
            <Link 
              href="#" 
              underline="hover" 
              color="text.secondary" 
              variant="body2"
            >
              Terms of Service
            </Link>
          </Grid>
          <Grid item>
            <Link 
              href="#" 
              underline="hover" 
              color="text.secondary" 
              variant="body2"
            >
              Help & Support
            </Link>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default LoginPage;
