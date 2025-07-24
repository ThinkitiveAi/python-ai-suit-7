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
  Grid,
  Stepper,
  Step,
  StepLabel,
  MenuItem,
  FormHelperText,
  Divider
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  LocalHospital, 
  CloudUpload,
  ArrowBack,
  ArrowForward
} from '@mui/icons-material';
import { useFormik } from 'formik';
import { Link as RouterLink } from 'react-router-dom';
import { registrationSchema } from '../utils/validationSchemas';

// Specialization options
const specializations = [
  'Cardiology',
  'Dermatology',
  'Emergency Medicine',
  'Family Medicine',
  'Gastroenterology',
  'Internal Medicine',
  'Neurology',
  'Obstetrics & Gynecology',
  'Oncology',
  'Ophthalmology',
  'Orthopedics',
  'Pediatrics',
  'Psychiatry',
  'Radiology',
  'Surgery',
  'Urology',
  'Other'
];

// Practice types
const practiceTypes = [
  'Private Practice',
  'Hospital',
  'Clinic',
  'Academic Medical Center',
  'Community Health Center',
  'Telehealth',
  'Other'
];

const RegisterPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [registerError, setRegisterError] = useState(null);
  const [profilePhotoPreview, setProfilePhotoPreview] = useState(null);

  const steps = ['Personal Information', 'Professional Details', 'Practice Information', 'Account Setup'];

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleClickShowConfirmPassword = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const handleNext = () => {
    const currentStepFields = {
      0: ['firstName', 'lastName', 'email', 'phoneNumber'],
      1: ['licenseNumber', 'specialization', 'yearsOfExperience', 'qualifications'],
      2: ['clinicName', 'clinicStreet', 'clinicCity', 'clinicState', 'clinicZip', 'practiceType'],
      3: ['password', 'confirmPassword', 'termsAccepted']
    };
    
    // Validate only the fields in the current step
    const stepFields = currentStepFields[activeStep];
    const stepErrors = {};
    let hasErrors = false;
    
    stepFields.forEach(field => {
      formik.setFieldTouched(field, true);
      if (formik.errors[field]) {
        stepErrors[field] = formik.errors[field];
        hasErrors = true;
      }
    });
    
    if (!hasErrors) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleProfilePhotoChange = (event) => {
    const file = event.currentTarget.files[0];
    if (file) {
      formik.setFieldValue('profilePhoto', file);
      
      // Create a preview URL for the image
      const reader = new FileReader();
      reader.onload = () => {
        setProfilePhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRegister = async (values) => {
    setIsLoading(true);
    setRegisterError(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // For demo purposes, simulate a successful registration
      console.log('Registration successful with:', values);
      
      // Redirect would happen here in a real app
      // history.push('/registration-success');
    } catch (error) {
      setRegisterError('Registration failed. Please try again.');
      console.error('Registration error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formik = useFormik({
    initialValues: {
      firstName: '',
      lastName: '',
      email: '',
      phoneNumber: '',
      profilePhoto: null,
      licenseNumber: '',
      specialization: '',
      yearsOfExperience: '',
      qualifications: '',
      clinicName: '',
      clinicStreet: '',
      clinicCity: '',
      clinicState: '',
      clinicZip: '',
      practiceType: '',
      password: '',
      confirmPassword: '',
      termsAccepted: false,
    },
    validationSchema: registrationSchema,
    onSubmit: handleRegister,
  });

  // Render form content based on active step
  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="firstName"
                  name="firstName"
                  label="First Name"
                  value={formik.values.firstName}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.firstName && Boolean(formik.errors.firstName)}
                  helperText={formik.touched.firstName && formik.errors.firstName}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="lastName"
                  name="lastName"
                  label="Last Name"
                  value={formik.values.lastName}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.lastName && Boolean(formik.errors.lastName)}
                  helperText={formik.touched.lastName && formik.errors.lastName}
                  margin="normal"
                />
              </Grid>
            </Grid>
            
            <TextField
              fullWidth
              id="email"
              name="email"
              label="Email Address"
              type="email"
              value={formik.values.email}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.email && Boolean(formik.errors.email)}
              helperText={formik.touched.email && formik.errors.email}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="phoneNumber"
              name="phoneNumber"
              label="Phone Number"
              value={formik.values.phoneNumber}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.phoneNumber && Boolean(formik.errors.phoneNumber)}
              helperText={formik.touched.phoneNumber && formik.errors.phoneNumber}
              margin="normal"
            />
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Profile Photo
              </Typography>
              
              <Box 
                sx={{ 
                  display: 'flex',
                  flexDirection: { xs: 'column', sm: 'row' },
                  alignItems: 'center',
                  gap: 2,
                  mt: 1
                }}
              >
                {profilePhotoPreview && (
                  <Box
                    component="img"
                    src={profilePhotoPreview}
                    alt="Profile Preview"
                    sx={{
                      width: 100,
                      height: 100,
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '2px solid #e0e0e0'
                    }}
                  />
                )}
                
                <Button
                  component="label"
                  variant="outlined"
                  startIcon={<CloudUpload />}
                  sx={{ mt: { xs: 1, sm: 0 } }}
                >
                  Upload Photo
                  <input
                    type="file"
                    accept="image/*"
                    hidden
                    onChange={handleProfilePhotoChange}
                  />
                </Button>
              </Box>
              
              <FormHelperText>
                Upload a professional photo for your provider profile
              </FormHelperText>
            </Box>
          </>
        );
      
      case 1:
        return (
          <>
            <TextField
              fullWidth
              id="licenseNumber"
              name="licenseNumber"
              label="Medical License Number"
              value={formik.values.licenseNumber}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.licenseNumber && Boolean(formik.errors.licenseNumber)}
              helperText={formik.touched.licenseNumber && formik.errors.licenseNumber}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="specialization"
              name="specialization"
              select
              label="Specialization"
              value={formik.values.specialization}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.specialization && Boolean(formik.errors.specialization)}
              helperText={formik.touched.specialization && formik.errors.specialization}
              margin="normal"
            >
              {specializations.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            
            <TextField
              fullWidth
              id="yearsOfExperience"
              name="yearsOfExperience"
              label="Years of Experience"
              type="number"
              value={formik.values.yearsOfExperience}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.yearsOfExperience && Boolean(formik.errors.yearsOfExperience)}
              helperText={formik.touched.yearsOfExperience && formik.errors.yearsOfExperience}
              margin="normal"
              InputProps={{ inputProps: { min: 0, max: 70 } }}
            />
            
            <TextField
              fullWidth
              id="qualifications"
              name="qualifications"
              label="Medical Degree/Qualifications"
              multiline
              rows={3}
              value={formik.values.qualifications}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.qualifications && Boolean(formik.errors.qualifications)}
              helperText={formik.touched.qualifications && formik.errors.qualifications}
              margin="normal"
              placeholder="E.g., MD, Harvard Medical School, Board Certified in Internal Medicine"
            />
          </>
        );
      
      case 2:
        return (
          <>
            <TextField
              fullWidth
              id="clinicName"
              name="clinicName"
              label="Clinic/Hospital Name"
              value={formik.values.clinicName}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.clinicName && Boolean(formik.errors.clinicName)}
              helperText={formik.touched.clinicName && formik.errors.clinicName}
              margin="normal"
            />
            
            <TextField
              fullWidth
              id="clinicStreet"
              name="clinicStreet"
              label="Street Address"
              value={formik.values.clinicStreet}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.clinicStreet && Boolean(formik.errors.clinicStreet)}
              helperText={formik.touched.clinicStreet && formik.errors.clinicStreet}
              margin="normal"
            />
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  id="clinicCity"
                  name="clinicCity"
                  label="City"
                  value={formik.values.clinicCity}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.clinicCity && Boolean(formik.errors.clinicCity)}
                  helperText={formik.touched.clinicCity && formik.errors.clinicCity}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  id="clinicState"
                  name="clinicState"
                  label="State"
                  value={formik.values.clinicState}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.clinicState && Boolean(formik.errors.clinicState)}
                  helperText={formik.touched.clinicState && formik.errors.clinicState}
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <TextField
                  fullWidth
                  id="clinicZip"
                  name="clinicZip"
                  label="ZIP Code"
                  value={formik.values.clinicZip}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  error={formik.touched.clinicZip && Boolean(formik.errors.clinicZip)}
                  helperText={formik.touched.clinicZip && formik.errors.clinicZip}
                  margin="normal"
                />
              </Grid>
            </Grid>
            
            <TextField
              fullWidth
              id="practiceType"
              name="practiceType"
              select
              label="Practice Type"
              value={formik.values.practiceType}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.practiceType && Boolean(formik.errors.practiceType)}
              helperText={formik.touched.practiceType && formik.errors.practiceType}
              margin="normal"
            >
              {practiceTypes.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </>
        );
      
      case 3:
        return (
          <>
            <TextField
              fullWidth
              id="password"
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formik.values.password}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.password && Boolean(formik.errors.password)}
              helperText={formik.touched.password && formik.errors.password}
              margin="normal"
              InputProps={{
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
            />
            
            <TextField
              fullWidth
              id="confirmPassword"
              name="confirmPassword"
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formik.values.confirmPassword}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.confirmPassword && Boolean(formik.errors.confirmPassword)}
              helperText={formik.touched.confirmPassword && formik.errors.confirmPassword}
              margin="normal"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowConfirmPassword}
                      onMouseDown={handleMouseDownPassword}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            
            <Box sx={{ mt: 3 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    id="termsAccepted"
                    name="termsAccepted"
                    color="primary"
                    checked={formik.values.termsAccepted}
                    onChange={formik.handleChange}
                  />
                }
                label="I agree to the Terms of Service and Privacy Policy"
              />
              {formik.touched.termsAccepted && formik.errors.termsAccepted && (
                <FormHelperText error>{formik.errors.termsAccepted}</FormHelperText>
              )}
            </Box>
          </>
        );
      
      default:
        return 'Unknown step';
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#f0f9ff',
        backgroundImage: 'linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="md">
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
            Provider Registration
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary" 
            sx={{ 
              mb: 3,
              textAlign: 'center'
            }}
          >
            Create your healthcare provider account
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
          {registerError && (
            <Alert 
              severity="error" 
              sx={{ 
                borderTopLeftRadius: 12, 
                borderTopRightRadius: 12 
              }}
            >
              {registerError}
            </Alert>
          )}
          
          <CardContent sx={{ p: 4 }}>
            <Stepper 
              activeStep={activeStep} 
              alternativeLabel
              sx={{ mb: 4 }}
            >
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
            
            <Divider sx={{ mb: 4 }} />
            
            <form onSubmit={formik.handleSubmit}>
              {renderStepContent(activeStep)}
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                <Button
                  color="inherit"
                  disabled={activeStep === 0}
                  onClick={handleBack}
                  startIcon={<ArrowBack />}
                  variant="outlined"
                >
                  Back
                </Button>
                
                <Box>
                  {activeStep === steps.length - 1 ? (
                    <Button
                      variant="contained"
                      color="primary"
                      type="submit"
                      disabled={isLoading}
                      sx={{ 
                        minWidth: 150,
                        fontWeight: 600
                      }}
                    >
                      {isLoading ? (
                        <CircularProgress size={24} color="inherit" />
                      ) : (
                        'Complete Registration'
                      )}
                    </Button>
                  ) : (
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleNext}
                      endIcon={<ArrowForward />}
                      sx={{ 
                        minWidth: 150,
                        fontWeight: 600
                      }}
                    >
                      Next
                    </Button>
                  )}
                </Box>
              </Box>
            </form>
          </CardContent>
        </Card>
        
        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Already have an account?{' '}
            <Link
              component={RouterLink}
              to="/login"
              underline="hover"
              sx={{ 
                color: 'primary.main',
                fontWeight: 500
              }}
            >
              Login here
            </Link>
          </Typography>
        </Box>
        
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

export default RegisterPage;
