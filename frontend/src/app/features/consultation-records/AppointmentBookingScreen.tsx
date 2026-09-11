import {
  Alert,
  Box,
  Button,
  CircularProgress,
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
import { PageHeader, Surface } from "../../ui/visualSystem";

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
    <Box sx={{ minWidth: 0 }}>
      <Button
        type="button"
        variant="text"
        onClick={goToSummary}
        disabled={pending}
        startIcon={<span aria-hidden="true">←</span>}
        sx={{ mb: 1, px: 0.5, color: "text.secondary", "&:hover": { color: "primary.main", bgcolor: "transparent" } }}
      >
        Back to Summary
      </Button>

      <PageHeader
        title="Book Appointment"
        subtitle="Configure appointment details for the recommended treatment."
      />

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
        <Box sx={{ display: "grid", gap: 2.5, gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1.65fr) minmax(280px, 0.75fr)" }, alignItems: "start" }}>
          <Stack component="form" spacing={2.5} onSubmit={(event) => void submit(event)} noValidate>
            <Surface sx={{ p: { xs: 2.25, sm: 3 } }}>
              <Typography component="h2" variant="h2" sx={{ mb: 2 }}>Procedure Details</Typography>
              <Typography id="selected-treatment-label" component="span" variant="caption" sx={{ display: "block", fontWeight: 700, mb: 0.75 }}>
                Selected treatment
              </Typography>
              <Box id="selected-treatment" role="group" aria-labelledby="selected-treatment-label" sx={{ px: 1.5, py: 1.35, bgcolor: "#f5f7fb", border: 1, borderColor: "divider", borderRadius: 1, overflowWrap: "anywhere" }}>
                <Typography sx={{ whiteSpace: "pre-wrap", fontWeight: 600 }}>{selectedRecommendation.treatment}</Typography>
              </Box>
            </Surface>

            <Surface sx={{ p: { xs: 2.25, sm: 3 } }}>
              <Typography component="h2" variant="h2" sx={{ mb: 2 }}>Logistics</Typography>
              <Stack spacing={2}>
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
              </Stack>
            </Surface>

            {bookingError === "validation" && <Alert severity="error">The appointment details were not accepted. Review the form and try again.</Alert>}
            {bookingError === "consultation-not-found" && <Alert severity="warning">The consultation no longer exists. Return to Consultation Records.</Alert>}
            {bookingError === "recommendation-not-found" && <Alert severity="warning">The selected recommendation no longer exists. Return to the consultation summary.</Alert>}
            {bookingError === "recommendation-not-bookable" && <Alert severity="warning">This recommendation cannot be booked for the consultation.</Alert>}
            {bookingError === "consultation-not-bookable" && <Alert severity="warning">This consultation is not eligible for appointment booking.</Alert>}
            {bookingError === "already-exists" && <Alert severity="info" action={<Button onClick={goToRecords}>View records</Button>}>An appointment already exists for this consultation.</Alert>}
            {bookingError === "ambiguous" && <Alert severity="error" action={<Button onClick={goToRecords}>Check records</Button>}>Confirmation could not be verified. Check Consultation Records before deliberately trying again; the appointment may have been created.</Alert>}

            <Button type="submit" variant="contained" size="large" fullWidth disabled={pending || bookingError === "already-exists"}>
              {pending ? "Confirming…" : "Confirm Appointment"}
            </Button>
          </Stack>

          <Box component="aside" aria-label="Appointment summary" sx={{ position: { lg: "sticky" }, top: { lg: 24 } }}>
            <Surface sx={{ p: { xs: 2.25, sm: 3 } }}>
              <Typography component="h2" variant="h2" sx={{ mb: 2 }}>Summary</Typography>
              <Stack divider={<Box sx={{ borderTop: 1, borderColor: "divider" }} />}>
                <Box sx={{ py: 1.25 }}>
                  <Typography variant="caption" color="text.secondary">Selected treatment</Typography>
                  <Typography sx={{ mt: 0.35 }}>Shown in Procedure Details.</Typography>
                </Box>
                <Box sx={{ py: 1.25 }}>
                  <Typography variant="caption" color="text.secondary">Date and time</Typography>
                  <Typography sx={{ mt: 0.35 }}>Entered in Logistics.</Typography>
                </Box>
                <Box sx={{ py: 1.25 }}>
                  <Typography variant="caption" color="text.secondary">Location</Typography>
                  <Typography sx={{ mt: 0.35 }}>Entered in Logistics.</Typography>
                </Box>
              </Stack>
            </Surface>
          </Box>
        </Box>
      )}
    </Box>
  );
}
