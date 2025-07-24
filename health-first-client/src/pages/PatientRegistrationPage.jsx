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
  Divider,
  Paper
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  LocalHospital, 
  Person,
  Mail,
  Phone,
  CalendarToday,
  Male,
  Female,
  Transgender,
  CloudUpload,
  ArrowBack,
  ArrowForward
} from '@mui/icons-material';
import { useFormik } from 'formik';
import { Link as RouterLink } from 'react-router-dom';
import * as Yup from 'yup';

// Gender options
const genderOptions = [
  { value: 'male', label: 'Male', icon: <Male sx={{ mr: 1 }} /> },
  { value: 'female', label: 'Female', icon: <Female sx={{ mr: 1 }} /> },
  { value: 'other', label: 'Other', icon: <Transgender sx={{ mr: 1 }} /> },
  { value: 'prefer_not_to_say', label: 'Prefer not to say', icon: <Person sx={{ mr: 1 }} /> }
];

// Patient registration validation schema
const patientRegistrationSchema = Yup.object().shape({
  // Personal Information
  firstName: Yup.string()
    .required('First name is required')
    .max(50, 'First name must be less than 50 characters'),
  lastName: Yup.string()
    .required('Last name is required')
    .max(50, 'Last name must be less than 50 characters'),
  email: Yup.string()
    .required('Email is required')
    .email('Enter a valid email'),
  phone: Yup.string()
    .required('Phone number is required')
    .matches(/^[0-9]{10}$/, 'Phone number must be 10 digits'),
  dateOfBirth: Yup.date()
    .required('Date of birth is required')
    .max(new Date(), 'Date of birth cannot be in the future')
    .test('is-adult', 'You must be at least 13 years old', (value) => {
      if (!value) return true;
      const age = Math.floor((new Date() - new Date(value)) / (1000 * 60 * 60 * 24 * 365.25));
      return age >= 13;
    }),
  gender: Yup.string()
    .required('Gender is required'),
  profilePhoto: Yup.mixed(),
  
  // Address Information
  streetAddress: Yup.string()
    .required('Street address is required'),
  city: Yup.string()
    .required('City is required'),
  state: Yup.string()
    .required('State is required'),
  zipCode: Yup.string()
    .required('ZIP code is required')
    .matches(/^[0-9]{5}(-[0-9]{4})?$/, 'Enter a valid ZIP code'),
  country: Yup.string()
    .required('Country is required'),
  
  // Emergency Contact
  emergencyContactName: Yup.string()
    .required('Emergency contact name is required'),
  emergencyContactRelationship: Yup.string()
    .required('Relationship is required'),
  emergencyContactPhone: Yup.string()
    .required('Emergency contact phone is required')
    .matches(/^[0-9]{10}$/, 'Emergency contact phone must be 10 digits'),
  
  // Account Security
  password: Yup.string()
    .required('Password is required')
    .min(8, 'Password must be at least 8 characters')
    .matches(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/, // At least one uppercase, lowercase, number, special char
      'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
    ),
  confirmPassword: Yup.string()
    .required('Please confirm your password')
    .oneOf([Yup.ref('password')], 'Passwords must match'),
  
  // Terms and Conditions
  termsAccepted: Yup.boolean()
    .oneOf([true], 'You must accept the terms and conditions'),
});

const PatientRegistrationPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [registerError, setRegisterError] = useState(null);
  const [profilePhotoPreview, setProfilePhotoPreview] = useState(null);

  const steps = [
    'Personal Information',
    'Address Information',
    'Emergency Contact',
    'Account Security'
  ];

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
      0: ['firstName', 'lastName', 'email', 'phone', 'dateOfBirth', 'gender'],
      1: ['streetAddress', 'city', 'state', 'zipCode', 'country'],
      2: ['emergencyContactName', 'emergencyContactRelationship', 'emergencyContactPhone'],
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
      console.log('Patient registration successful with:', values);
      
      // Redirect would happen here in a real app
      // history.push('/patient/registration-success');
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
      phone: '',
      dateOfBirth: '',
      gender: '',
      profilePhoto: null,
      streetAddress: '',
      city: '',
      state: '',
      zipCode: '',
      country: 'United States',
      emergencyContactName: '',
      emergencyContactRelationship: '',
      emergencyContactPhone: '',
      password: '',
      confirmPassword: '',
      termsAccepted: false,
    },
    validationSchema: patientRegistrationSchema,
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
                  placeholder="Enter your first name"
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
                  placeholder="Enter your last name"
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
              placeholder="Enter your email address"
              value={formik.values.email}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.email && Boolean(formik.errors.email)}
              helperText={formik.touched.email && formik.errors.email}
              margin="normal"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Mail sx={{ color: '#10b981' }} />
                  </InputAdornment>
                ),
              }}
            />
            
            <TextField
              fullWidth
              id="phone"
              name="phone"
              label="Phone Number"
              placeholder="Enter your phone number"
              value={formik.values.phone}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.phone && Boolean(formik.errors.phone)}
              helperText={formik.touched.phone && formik.errors.phone}
              margin="normal"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Phone sx={{ color: '#10b981' }} />
                  </InputAdornment>
                ),
              }}
            />
            
            <TextField
              fullWidth
              id="dateOfBirth"
              name="dateOfBirth"
              label="Date of Birth"
              type="date"
              value={formik.values.dateOfBirth}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.dateOfBirth && Boolean(formik.errors.dateOfBirth)}
              helperText={formik.touched.dateOfBirth && formik.errors.dateOfBirth}
              margin="normal"
              InputLabelProps={{
                shrink: true,
              }}
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              id="gender"
              name="gender"
              select
              label="Gender"
              value={formik.values.gender}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={formik.touched.gender && Boolean(formik.errors.gender)}
              helperText={formik.touched.gender && formik.errors.gender}
              margin="normal"
            >
              {genderOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.icon}
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Profile Photo (Optional)
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
                Upload a photo for your patient profile (optional)
              </FormHelperText>
            </Box>
          </>
        );
      
      case 1:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="streetAddress"
                name="streetAddress"
                label="Street Address"
                placeholder="Enter your street address"
                value={formik.values.streetAddress}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.streetAddress && Boolean(formik.errors.streetAddress)}
                helperText={formik.touched.streetAddress && formik.errors.streetAddress}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                id="city"
                name="city"
                label="City"
                placeholder="Enter your city"
                value={formik.values.city}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.city && Boolean(formik.errors.city)}
                helperText={formik.touched.city && formik.errors.city}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                id="state"
                name="state"
                label="State"
                placeholder="Enter your state"
                value={formik.values.state}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.state && Boolean(formik.errors.state)}
                helperText={formik.touched.state && formik.errors.state}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                id="zipCode"
                name="zipCode"
                label="ZIP Code"
                placeholder="Enter your ZIP code"
                value={formik.values.zipCode}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.zipCode && Boolean(formik.errors.zipCode)}
                helperText={formik.touched.zipCode && formik.errors.zipCode}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="country"
                name="country"
                label="Country"
                placeholder="Enter your country"
                value={formik.values.country}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.country && Boolean(formik.errors.country)}
                helperText={formik.touched.country && formik.errors.country}
                margin="normal"
              />
            </Grid>
          </Grid>
        );
      
      case 2:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="emergencyContactName"
                name="emergencyContactName"
                label="Emergency Contact Name"
                placeholder="Enter emergency contact's name"
                value={formik.values.emergencyContactName}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.emergencyContactName && Boolean(formik.errors.emergencyContactName)}
                helperText={formik.touched.emergencyContactName && formik.errors.emergencyContactName}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="emergencyContactRelationship"
                name="emergencyContactRelationship"
                label="Relationship"
                placeholder="Enter your relationship to this person"
                value={formik.values.emergencyContactRelationship}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.emergencyContactRelationship && Boolean(formik.errors.emergencyContactRelationship)}
                helperText={formik.touched.emergencyContactRelationship && formik.errors.emergencyContactRelationship}
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="emergencyContactPhone"
                name="emergencyContactPhone"
                label="Emergency Contact Phone"
                placeholder="Enter emergency contact's phone number"
                value={formik.values.emergencyContactPhone}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.emergencyContactPhone && Boolean(formik.errors.emergencyContactPhone)}
                helperText={formik.touched.emergencyContactPhone && formik.errors.emergencyContactPhone}
                margin="normal"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Phone sx={{ color: '#10b981' }} />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>
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
              placeholder="Create a secure password"
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
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              id="confirmPassword"
              name="confirmPassword"
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Confirm your password"
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
              sx={{ mb: 2 }}
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
                label={(
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="body1">
                      I agree to the{' '}
                    </Typography>
                    <Link 
                      href="#" 
                      underline="hover" 
                      sx={{ 
                        color: '#3b82f6',
                        fontWeight: 500,
                        ml: 0.5,
                        mr: 0.5
                      }}
                    >
                      Terms of Service
                    </Link>
                    <Typography variant="body1">
                      and{' '}
                    </Typography>
                    <Link 
                      href="#" 
                      underline="hover" 
                      sx={{ 
                        color: '#3b82f6',
                        fontWeight: 500,
                        ml: 0.5,
                        mr: 0.5
                      }}
                    >
                      Privacy Policy
                    </Link>
                  </Box>
                )}
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
                color: '#3b82f6', 
                mr: 1 
              }} 
            />
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700, 
                color: '#3b82f6' 
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
            Patient Registration
          </Typography>
          <Typography 
            variant="body1" 
            color="text.secondary" 
            sx={{ 
              mb: 3,
              textAlign: 'center'
            }}
          >
            Create your healthcare account
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
                        fontWeight: 600,
                        backgroundColor: '#3b82f6',
                        '&:hover': {
                          backgroundColor: '#2563eb',
                        }
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
                        fontWeight: 600,
                        backgroundColor: '#3b82f6',
                        '&:hover': {
                          backgroundColor: '#2563eb',
                        }
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
              to="/patient/login"
              underline="hover"
              sx={{ 
                color: '#3b82f6',
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

export default PatientRegistrationPage;
