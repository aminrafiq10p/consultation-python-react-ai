import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { appointmentApi } from "./appointmentApi";
import type { AppointmentListItem, AppointmentListResponse } from "./appointmentTypes";

export interface AppointmentListService {
  listAppointments: () => Promise<AppointmentListResponse>;
}

interface AppointmentsScreenProps {
  service?: AppointmentListService;
}

type AppointmentsState =
  | { status: "loading" }
  | { status: "success"; appointments: AppointmentListItem[] }
  | { status: "error" };

const formatScheduledAt = (value: string) =>
  new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

const identityText = { overflowWrap: "anywhere", wordBreak: "break-word" };

function ConsultationLink({ appointment }: { appointment: AppointmentListItem }) {
  return (
    <Button
      component={Link}
      to={`/consultations/${encodeURIComponent(appointment.consultation_id)}`}
      variant="outlined"
      size="small"
    >
      View consultation for {appointment.patient_name}
    </Button>
  );
}

function AppointmentCard({ appointment }: { appointment: AppointmentListItem }) {
  return (
    <Card component="article" variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Box>
            <Typography component="h2" variant="h6">{appointment.patient_name}</Typography>
            <Typography color="text.secondary">{appointment.recommendation.treatment}</Typography>
          </Box>
          <Divider />
          <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" } }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Date and time</Typography>
              <Typography component="time" dateTime={appointment.scheduled_at}>
                {formatScheduledAt(appointment.scheduled_at)}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Location</Typography>
              <Typography>{appointment.location}</Typography>
            </Box>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Appointment ID</Typography>
            <Typography variant="body2" sx={identityText}>{appointment.id}</Typography>
            <Typography variant="caption" color="text.secondary">Consultation ID</Typography>
            <Typography variant="body2" sx={identityText}>{appointment.consultation_id}</Typography>
            <Typography variant="caption" color="text.secondary">Recommendation ID</Typography>
            <Typography variant="body2" sx={identityText}>{appointment.recommendation.id}</Typography>
            <Typography variant="caption" color="text.secondary">Booked at</Typography>
            <Typography component="time" dateTime={appointment.created_at} variant="body2">
              {formatScheduledAt(appointment.created_at)}
            </Typography>
          </Box>
          <Box>
            <ConsultationLink appointment={appointment} />
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

function AppointmentTable({ appointments }: { appointments: AppointmentListItem[] }) {
  return (
    <TableContainer component={Card} variant="outlined">
      <Table aria-label="Appointments" sx={{ tableLayout: "fixed" }}>
        <TableHead>
          <TableRow>
            <TableCell>Patient</TableCell>
            <TableCell>Treatment</TableCell>
            <TableCell>Date and time</TableCell>
            <TableCell>Location</TableCell>
            <TableCell>Appointment identity</TableCell>
            <TableCell>Consultation</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {appointments.map((appointment) => (
            <TableRow key={appointment.id} hover>
              <TableCell>{appointment.patient_name}</TableCell>
              <TableCell>
                <Typography variant="body2">{appointment.recommendation.treatment}</Typography>
                <Typography variant="caption" color="text.secondary" sx={identityText}>
                  Recommendation ID: {appointment.recommendation.id}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography component="time" dateTime={appointment.scheduled_at} variant="body2">
                  {formatScheduledAt(appointment.scheduled_at)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Booked <time dateTime={appointment.created_at}>{formatScheduledAt(appointment.created_at)}</time>
                </Typography>
              </TableCell>
              <TableCell>{appointment.location}</TableCell>
              <TableCell sx={identityText}>{appointment.id}</TableCell>
              <TableCell>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block", ...identityText }}>
                  Consultation ID: {appointment.consultation_id}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <ConsultationLink appointment={appointment} />
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export function AppointmentsScreen({ service = appointmentApi }: AppointmentsScreenProps) {
  const theme = useTheme();
  const desktop = useMediaQuery(theme.breakpoints.up("lg"));
  const [state, setState] = useState<AppointmentsState>({ status: "loading" });
  const requestId = useRef(0);

  const requestAppointments = useCallback(() => {
    const currentRequestId = ++requestId.current;

    service.listAppointments().then(
      ({ items }) => {
        if (requestId.current === currentRequestId) setState({ status: "success", appointments: items });
      },
      () => {
        if (requestId.current === currentRequestId) setState({ status: "error" });
      },
    );
  }, [service]);

  const retry = () => {
    setState({ status: "loading" });
    requestAppointments();
  };

  useEffect(() => {
    requestAppointments();
    return () => {
      requestId.current += 1;
    };
  }, [requestAppointments]);

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>Appointments</Typography>

      {state.status === "loading" && (
        <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <CircularProgress size={24} />
          <span>Loading appointments…</span>
        </Box>
      )}

      {state.status === "error" && (
        <Alert severity="error" action={<Button color="inherit" onClick={retry}>Retry</Button>}>
          Appointments could not be loaded. Please try again.
        </Alert>
      )}

      {state.status === "success" && state.appointments.length === 0 && (
        <Alert severity="info">No appointments have been booked yet.</Alert>
      )}

      {state.status === "success" && state.appointments.length > 0 && (
        desktop ? <AppointmentTable appointments={state.appointments} /> : (
          <Stack spacing={2}>
            {state.appointments.map((appointment) => (
              <AppointmentCard key={appointment.id} appointment={appointment} />
            ))}
          </Stack>
        )
      )}
    </Box>
  );
}
