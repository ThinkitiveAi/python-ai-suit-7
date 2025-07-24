import React from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Paper, 
  Grid,
  Card,
  CardContent,
  Button
} from '@mui/material';
import { 
  LocalHospital, 
  Person, 
  CalendarToday, 
  Notifications 
} from '@mui/icons-material';

const DashboardPage = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#f8fafc',
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" fontWeight={600}>
            Welcome to Health First
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Provider Dashboard
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {/* Summary Cards */}
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Today's Appointments
                    </Typography>
                    <Typography variant="h4" fontWeight={600}>
                      8
                    </Typography>
                  </Box>
                  <CalendarToday sx={{ color: 'primary.main', fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Total Patients
                    </Typography>
                    <Typography variant="h4" fontWeight={600}>
                      124
                    </Typography>
                  </Box>
                  <Person sx={{ color: 'secondary.main', fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Pending Reports
                    </Typography>
                    <Typography variant="h4" fontWeight={600}>
                      5
                    </Typography>
                  </Box>
                  <Notifications sx={{ color: 'warning.main', fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Completed Visits
                    </Typography>
                    <Typography variant="h4" fontWeight={600}>
                      42
                    </Typography>
                  </Box>
                  <LocalHospital sx={{ color: 'success.main', fontSize: 40 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Main Content */}
          <Grid item xs={12}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 3, 
                borderRadius: 2,
                height: '400px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                textAlign: 'center'
              }}
            >
              <LocalHospital sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Welcome to your Provider Dashboard
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: '600px', mb: 3 }}>
                This is a placeholder dashboard. In a real application, this would display your appointments, patient information, and other relevant healthcare provider data.
              </Typography>
              <Button variant="contained" color="primary">
                View Appointments
              </Button>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default DashboardPage;
