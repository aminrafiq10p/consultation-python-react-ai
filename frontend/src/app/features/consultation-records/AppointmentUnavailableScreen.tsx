import { Alert, Box, Typography } from "@mui/material";

export function AppointmentUnavailableScreen() {
  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Appointment
      </Typography>
      <Alert severity="info">
        Appointment setup is not available yet. Your consultation selection has been preserved in the navigation boundary.
      </Alert>
    </Box>
  );
}
