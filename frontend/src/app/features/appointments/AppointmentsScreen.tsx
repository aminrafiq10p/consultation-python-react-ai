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
import { PageHeader, Surface } from "../../ui/visualSystem";

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
      aria-label={`View consultation for ${appointment.patient_name}`}
    >
      View consultation for {appointment.patient_name}
    </Button>
  );
}

function AppointmentCard({ appointment }: { appointment: AppointmentListItem }) {
  return (
    <Card component="article" variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
      <Stack spacing={2} sx={{ minWidth: 0 }}>
          <Box>
            <Typography component="h2" variant="h3">{appointment.patient_name}</Typography>
            <Typography color="text.secondary" sx={{ mt: 0.35, overflowWrap: "anywhere" }}>{appointment.recommendation.treatment}</Typography>
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
              <Typography sx={{ overflowWrap: "anywhere" }}>{appointment.location}</Typography>
            </Box>
          </Box>
          <Box sx={{ bgcolor: "#fbfcfe", borderRadius: 1.5, p: 1.5 }}>
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
    <Surface sx={{ overflow: "hidden" }}>
      <TableContainer>
      <Table aria-label="Appointments" sx={{ minWidth: 860, tableLayout: "fixed" }}>
        <TableHead>
          <TableRow sx={{ "& th": { bgcolor: "#fbfcfe", color: "text.secondary", fontSize: "0.72rem", fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase", whiteSpace: "nowrap" } }}>
            <TableCell sx={{ width: "17%" }}>Patient</TableCell>
            <TableCell sx={{ width: "20%" }}>Treatment</TableCell>
            <TableCell sx={{ width: "19%" }}>Date and time</TableCell>
            <TableCell sx={{ width: "17%" }}>Location</TableCell>
            <TableCell sx={{ width: "13%" }}>Appointment ID</TableCell>
            <TableCell sx={{ width: "14%" }}>Consultation</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {appointments.map((appointment) => (
            <TableRow key={appointment.id} hover sx={{ "& td": { minHeight: 76, borderColor: "divider", verticalAlign: "top" } }}>
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
    </Surface>
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
    <Box sx={{ minWidth: 0 }}>
      <PageHeader
        title="Appointments"
        subtitle="Review booked appointments and continue to their consultations."
      />

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
