import * as Yup from 'yup';

// Login form validation schema
export const loginSchema = Yup.object().shape({
  credential: Yup.string()
    .required('Email or phone number is required')
    .test('is-email-or-phone', 'Enter a valid email or phone number', (value) => {
      const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
      const phoneRegex = /^[0-9]{10}$/; // Simple 10-digit phone validation
      
      return emailRegex.test(value) || phoneRegex.test(value);
    }),
  password: Yup.string()
    .required('Password is required')
    .min(8, 'Password must be at least 8 characters'),
  rememberMe: Yup.boolean(),
});

// Registration form validation schema
export const registrationSchema = Yup.object().shape({
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
  phoneNumber: Yup.string()
    .required('Phone number is required')
    .matches(/^[0-9]{10}$/, 'Phone number must be 10 digits'),
  profilePhoto: Yup.mixed(),
  
  // Professional Information
  licenseNumber: Yup.string()
    .required('Medical license number is required')
    .min(5, 'License number must be at least 5 characters'),
  specialization: Yup.string()
    .required('Specialization is required'),
  yearsOfExperience: Yup.number()
    .required('Years of experience is required')
    .min(0, 'Years of experience cannot be negative')
    .max(70, 'Please enter a valid number of years'),
  qualifications: Yup.string()
    .required('Medical qualifications are required'),
  
  // Practice Information
  clinicName: Yup.string()
    .required('Clinic/Hospital name is required'),
  clinicStreet: Yup.string()
    .required('Street address is required'),
  clinicCity: Yup.string()
    .required('City is required'),
  clinicState: Yup.string()
    .required('State is required'),
  clinicZip: Yup.string()
    .required('ZIP code is required')
    .matches(/^[0-9]{5}(-[0-9]{4})?$/, 'Enter a valid ZIP code'),
  practiceType: Yup.string()
    .required('Practice type is required'),
  
  // Account Security
  password: Yup.string()
    .required('Password is required')
    .min(8, 'Password must be at least 8 characters')
    .matches(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
      'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
    ),
  confirmPassword: Yup.string()
    .required('Please confirm your password')
    .oneOf([Yup.ref('password')], 'Passwords must match'),
  
  // Terms and Conditions
  termsAccepted: Yup.boolean()
    .oneOf([true], 'You must accept the terms and conditions'),
});
