import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  FormControlLabel,
  FormLabel,
  Paper,
  Radio,
  RadioGroup,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ConsultationApiError, consultationApi } from "./consultationApi";
import type { ConsultationRecord, ConsultationSummary } from "./consultationTypes";

export interface ConsultationSummaryService {
  summary: (consultationId: string) => Promise<ConsultationSummary>;
  restartConsultation: (consultationId: string) => Promise<ConsultationRecord>;
}

interface ConsultationSummaryScreenProps {
  service?: ConsultationSummaryService;
}

type SummaryState =
  | { status: "loading"; consultationId: string }
  | { status: "success"; consultationId: string; summary: ConsultationSummary }
  | { status: "unavailable"; consultationId: string }
  | { status: "not-found"; consultationId: string }
  | { status: "error"; consultationId: string };

type RestartError = "not-restartable" | "not-found" | "error" | null;

export function ConsultationSummaryScreen({
  service = consultationApi,
}: ConsultationSummaryScreenProps) {
  const { consultationId } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<SummaryState | null>(null);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState("");
  const [restartPending, setRestartPending] = useState(false);
  const [restartError, setRestartError] = useState<RestartError>(null);

  const loadSummary = useCallback(() => {
    if (!consultationId) return () => undefined;

    let active = true;
    service.summary(consultationId).then(
      (summary) => {
        if (active) setState({ status: "success", consultationId, summary });
      },
      (error: unknown) => {
        if (!active) return;
        const status =
          error instanceof ConsultationApiError
            ? error.kind === "summary-not-available"
              ? "unavailable"
              : error.kind === "not-found"
                ? "not-found"
                : "error"
            : "error";
        setState({ status, consultationId });
      },
    );

    return () => {
      active = false;
    };
  }, [consultationId, service]);

  useEffect(() => loadSummary(), [loadSummary]);

  const visibleState =
    consultationId
      ? state?.consultationId === consultationId
        ? state
        : { status: "loading" as const, consultationId }
      : null;

  const retrySummary = () => {
    if (!consultationId) return;
    setState({ status: "loading", consultationId });
    loadSummary();
  };

  const restart = async () => {
    if (!consultationId || visibleState?.status !== "success" || restartPending) return;
    setRestartPending(true);
    setRestartError(null);
    try {
      const restarted = await service.restartConsultation(consultationId);
      navigate(`/consultations/${encodeURIComponent(restarted.id)}`);
    } catch (error) {
      setRestartError(
        error instanceof ConsultationApiError
          ? error.kind === "not-restartable"
            ? "not-restartable"
            : error.kind === "not-found"
              ? "not-found"
              : "error"
          : "error",
      );
      setRestartPending(false);
    }
  };

  const bookAppointment = () => {
    if (!consultationId || !selectedRecommendationId) return;
    navigate(
      `/consultations/${encodeURIComponent(consultationId)}/appointments/new?${new URLSearchParams({ recommendation_id: selectedRecommendationId })}`,
    );
  };

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Consultation Summary
      </Typography>

      {(!consultationId || visibleState === null) && (
        <Alert severity="error">Consultation summary could not be loaded. Please try again.</Alert>
      )}

      {visibleState?.status === "loading" && (
        <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <CircularProgress size={24} />
          <span>Loading consultation summary…</span>
        </Box>
      )}

      {visibleState?.status === "unavailable" && (
        <Alert severity="info">A summary has not been generated for this consultation.</Alert>
      )}

      {visibleState?.status === "not-found" && (
        <Alert severity="info">Consultation not found. This consultation is unavailable.</Alert>
      )}

      {visibleState?.status === "error" && (
        <Alert severity="error" action={<Button onClick={retrySummary}>Retry</Button>}>
          Consultation summary could not be loaded. Please try again.
        </Alert>
      )}

      {visibleState?.status === "success" && (
        <Stack spacing={3}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={3}>
              <Box>
                <Typography component="h2" variant="h6">Patient summary</Typography>
                <Typography sx={{ whiteSpace: "pre-wrap" }}>
                  {visibleState.summary.patient_summary}
                </Typography>
              </Box>

              <FormControl>
                <FormLabel id="recommended-treatments-label">Recommended treatments</FormLabel>
                <RadioGroup
                  aria-labelledby="recommended-treatments-label"
                  value={selectedRecommendationId}
                  onChange={(event) => setSelectedRecommendationId(event.target.value)}
                >
                  {visibleState.summary.recommended_treatments.map((recommendation) => (
                    <FormControlLabel
                      key={recommendation.id}
                      value={recommendation.id}
                      control={<Radio />}
                      label={recommendation.treatment}
                    />
                  ))}
                </RadioGroup>
              </FormControl>

              {visibleState.summary.recommendation_rationale !== null && (
                <Box>
                  <Typography component="h2" variant="h6">Recommendation rationale</Typography>
                  <Typography sx={{ whiteSpace: "pre-wrap" }}>
                    {visibleState.summary.recommendation_rationale}
                  </Typography>
                </Box>
              )}
            </Stack>
          </Paper>

          {restartError === "not-restartable" && (
            <Alert severity="warning">This consultation cannot be restarted.</Alert>
          )}
          {restartError === "not-found" && (
            <Alert severity="warning">The source consultation is no longer available.</Alert>
          )}
          {restartError === "error" && (
            <Alert severity="error">Consultation could not be restarted. Please try again.</Alert>
          )}

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <Button variant="outlined" disabled={restartPending} onClick={restart}>
              {restartPending ? "Restarting…" : "Restart Consultation"}
            </Button>
            <Button
              variant="contained"
              disabled={!selectedRecommendationId}
              onClick={bookAppointment}
            >
              Book Appointment
            </Button>
          </Stack>
        </Stack>
      )}
    </Box>
  );
}
