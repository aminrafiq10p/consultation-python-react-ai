import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { ConsultationApiError, consultationApi } from "./consultationApi";
import type {
  Appointment,
  AppointmentBookingRequest,
  ConsultationSummary,
} from "./consultationTypes";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export interface AppointmentBookingService {
  summary: (consultationId: string) => Promise<ConsultationSummary>;
  bookAppointment: (
    consultationId: string,
    request: AppointmentBookingRequest,
  ) => Promise<Appointment>;
}

interface AppointmentBookingScreenProps {
  service?: AppointmentBookingService;
  now?: () => Date;
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; summary: ConsultationSummary }
  | { status: "unavailable" }
  | { status: "not-found" }
  | { status: "error" };

type BookingError =
  | "validation"
  | "consultation-not-found"
  | "recommendation-not-found"
  | "recommendation-not-bookable"
  | "consultation-not-bookable"
  | "already-exists"
  | "ambiguous"
  | null;

export function AppointmentBookingScreen({
  service = consultationApi,
  now = () => new Date(),
}: AppointmentBookingScreenProps) {
  const { consultationId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const recommendationValues = searchParams.getAll("recommendation_id");
  const recommendationId = recommendationValues.length === 1 ? recommendationValues[0] : null;
  const validContext = Boolean(
    consultationId &&
      UUID_PATTERN.test(consultationId) &&
      recommendationId &&
      UUID_PATTERN.test(recommendationId),
  );

  const [loadState, setLoadState] = useState<LoadState | null>(null);
  const [scheduledAt, setScheduledAt] = useState("");
  const [location, setLocation] = useState("");
  const [scheduledAtError, setScheduledAtError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [bookingError, setBookingError] = useState<BookingError>(null);
  const [pending, setPending] = useState(false);

  const loadSummary = useCallback(() => {
    if (!validContext || !consultationId) return () => undefined;
    let active = true;
    service.summary(consultationId).then(
      (summary) => {
        if (active) setLoadState({ status: "ready", summary });
      },
      (error: unknown) => {
        if (!active) return;
        const status =
          error instanceof ConsultationApiError
            ? error.kind === "not-found"
              ? "not-found"
              : error.kind === "summary-not-available"
                ? "unavailable"
                : "error"
            : "error";
        setLoadState({ status });
      },
    );
    return () => {
      active = false;
    };
  }, [consultationId, service, validContext]);

  useEffect(() => loadSummary(), [loadSummary]);

  const selectedRecommendation = useMemo(
    () =>
      loadState?.status === "ready"
        ? loadState.summary.recommended_treatments.find(
            (recommendation) => recommendation.id === recommendationId,
          ) ?? null
        : null,
    [loadState, recommendationId],
  );

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (pending || !consultationId || !selectedRecommendation) return;

    let valid = true;
    const parsed = new Date(scheduledAt);
    if (!scheduledAt) {
      setScheduledAtError("Appointment date and time are required.");
      valid = false;
    } else if (Number.isNaN(parsed.getTime())) {
      setScheduledAtError("Enter a valid appointment date and time.");
      valid = false;
    } else if (parsed.getTime() <= now().getTime()) {
      setScheduledAtError("Appointment date and time must be in the future.");
      valid = false;
    } else {
      setScheduledAtError(null);
    }

    const normalizedLocation = location.trim();
    if (!normalizedLocation) {
      setLocationError("Location is required.");
      valid = false;
    } else if ([...normalizedLocation].length > 200) {
      setLocationError("Location must be 200 characters or fewer.");
      valid = false;
    } else {
      setLocationError(null);
    }
    if (!valid) return;

    setLocation(normalizedLocation);
    setPending(true);
    setBookingError(null);
    try {
      await service.bookAppointment(consultationId, {
        recommendation_id: selectedRecommendation.id,
        scheduled_at: parsed.toISOString(),
        location: normalizedLocation,
      });
      navigate("/consultations", { replace: true });
    } catch (error) {
      const kind = error instanceof ConsultationApiError ? error.kind : "booking-submission";
      const mapped: BookingError =
        kind === "booking-validation"
          ? "validation"
          : kind === "booking-consultation-not-found"
            ? "consultation-not-found"
            : kind === "booking-recommendation-not-found"
              ? "recommendation-not-found"
              : kind === "recommendation-not-bookable"
                ? "recommendation-not-bookable"
                : kind === "consultation-not-bookable"
                  ? "consultation-not-bookable"
                  : kind === "appointment-already-exists"
                    ? "already-exists"
                    : "ambiguous";
      setBookingError(mapped);
      setPending(false);
    }
  };

  const goToRecords = () => navigate("/consultations");
  const retrySummary = () => {
    setLoadState({ status: "loading" });
    loadSummary();
  };
  const goToSummary = () => {
    if (consultationId && UUID_PATTERN.test(consultationId)) {
      navigate(`/consultations/${encodeURIComponent(consultationId)}/summary`);
    } else {
      goToRecords();
    }
  };

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Book Appointment
      </Typography>

      {!validContext && (
        <Alert severity="warning" action={<Button onClick={goToRecords}>View records</Button>}>
          This booking link is invalid or incomplete. Return to Consultation Records and select a recommendation again.
        </Alert>
      )}

      {validContext && (loadState === null || loadState.status === "loading") && (
        <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <CircularProgress size={24} />
          <span>Loading appointment details…</span>
        </Box>
      )}

      {loadState?.status === "not-found" && (
        <Alert severity="warning" action={<Button onClick={goToRecords}>View records</Button>}>
          Consultation not found. This appointment cannot be booked.
        </Alert>
      )}
      {loadState?.status === "unavailable" && (
        <Alert severity="warning" action={<Button onClick={goToSummary}>Back to summary</Button>}>
          A persisted consultation summary is not available for booking.
        </Alert>
      )}
      {loadState?.status === "error" && (
        <Alert severity="error" action={<Button onClick={retrySummary}>Retry</Button>}>
          Appointment details could not be loaded. Please try again.
        </Alert>
      )}
      {loadState?.status === "ready" && !selectedRecommendation && (
        <Alert severity="warning" action={<Button onClick={goToSummary}>Back to summary</Button>}>
          The selected recommendation is not available for this consultation.
        </Alert>
      )}

      {loadState?.status === "ready" && selectedRecommendation && (
        <Paper sx={{ p: 3 }}>
          <Stack component="form" spacing={3} onSubmit={(event) => void submit(event)} noValidate>
            <Box>
              <Typography component="h2" variant="h6">Selected treatment</Typography>
              <Typography sx={{ whiteSpace: "pre-wrap" }}>{selectedRecommendation.treatment}</Typography>
            </Box>

            {bookingError === "validation" && <Alert severity="error">The appointment details were not accepted. Review the form and try again.</Alert>}
            {bookingError === "consultation-not-found" && <Alert severity="warning">The consultation no longer exists. Return to Consultation Records.</Alert>}
            {bookingError === "recommendation-not-found" && <Alert severity="warning">The selected recommendation no longer exists. Return to the consultation summary.</Alert>}
            {bookingError === "recommendation-not-bookable" && <Alert severity="warning">This recommendation cannot be booked for the consultation.</Alert>}
            {bookingError === "consultation-not-bookable" && <Alert severity="warning">This consultation is not eligible for appointment booking.</Alert>}
            {bookingError === "already-exists" && <Alert severity="info" action={<Button onClick={goToRecords}>View records</Button>}>An appointment already exists for this consultation.</Alert>}
            {bookingError === "ambiguous" && <Alert severity="error" action={<Button onClick={goToRecords}>Check records</Button>}>Confirmation could not be verified. Check Consultation Records before deliberately trying again; the appointment may have been created.</Alert>}

            <TextField
              label="Appointment date and time"
              type="datetime-local"
              value={scheduledAt}
              onChange={(event) => setScheduledAt(event.target.value)}
              error={scheduledAtError !== null}
              helperText={scheduledAtError ?? "Choose a future date and time."}
              disabled={pending || bookingError === "already-exists"}
              slotProps={{ inputLabel: { shrink: true } }}
              required
            />
            <TextField
              label="Location"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              error={locationError !== null}
              helperText={locationError ?? `${[...location.trim()].length}/200 characters`}
              disabled={pending || bookingError === "already-exists"}
              required
            />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <Button type="button" variant="outlined" onClick={goToSummary} disabled={pending}>
                Back to Summary
              </Button>
              <Button type="submit" variant="contained" disabled={pending || bookingError === "already-exists"}>
                {pending ? "Confirming…" : "Confirm Appointment"}
              </Button>
            </Stack>
          </Stack>
        </Paper>
      )}
    </Box>
  );
}
