import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  FormControlLabel,
  FormLabel,
  Radio,
  RadioGroup,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ConsultationApiError, consultationApi } from "./consultationApi";
import type { ConsultationRecord, ConsultationSummary } from "./consultationTypes";
import { PageHeader, Surface } from "../../ui/visualSystem";

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

  const summary = visibleState?.status === "success" ? visibleState.summary : null;

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
      <PageHeader
        title="Consultation Summary"
        subtitle="Review the persisted summary and choose a treatment to continue."
      />

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

      {summary && (
        <Stack spacing={{ xs: 3, md: 4 }}>
          <Box
            sx={{
              display: "grid",
              gap: 2.5,
              gridTemplateColumns: {
                xs: "1fr",
                lg: summary.recommendation_rationale !== null
                  ? "minmax(0, 1.65fr) minmax(280px, 0.85fr)"
                  : "1fr",
              },
              alignItems: "stretch",
            }}
          >
            <Surface sx={{ p: { xs: 2.25, sm: 3 }, minWidth: 0 }}>
              <Typography component="h2" variant="h2" sx={{ mb: 2 }}>
                Patient Summary
              </Typography>
              <Typography sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                {summary.patient_summary}
              </Typography>
            </Surface>

            {summary.recommendation_rationale !== null && (
              <Surface
                sx={{
                  p: { xs: 2.25, sm: 3 },
                  minWidth: 0,
                  borderLeft: { lg: "3px solid" },
                  borderLeftColor: { lg: "primary.main" },
                  bgcolor: "#fbfcfe",
                }}
              >
                <Typography
                  component="h2"
                  variant="overline"
                  color="primary.dark"
                  sx={{ display: "block", fontWeight: 800, letterSpacing: "0.08em", mb: 1.25 }}
                >
                  AI Insight
                </Typography>
                <Typography sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                  {summary.recommendation_rationale}
                </Typography>
              </Surface>
            )}
          </Box>

          <FormControl component="fieldset" fullWidth>
            <FormLabel
              id="recommended-treatments-label"
              component="h2"
              sx={{
                color: "text.primary",
                fontSize: "1.25rem",
                fontWeight: 700,
                mb: 1.5,
                "&.Mui-focused": { color: "text.primary" },
              }}
            >
              Recommended Treatments
            </FormLabel>
            <RadioGroup
              aria-label="Recommended treatments"
              value={selectedRecommendationId}
              onChange={(event) => setSelectedRecommendationId(event.target.value)}
              sx={{
                display: "grid",
                gap: 2,
                gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" },
              }}
            >
              {summary.recommended_treatments.map((recommendation) => {
                const selected = selectedRecommendationId === recommendation.id;
                return (
                  <FormControlLabel
                    key={recommendation.id}
                    value={recommendation.id}
                    control={
                      <Radio
                        slotProps={{ input: { "aria-label": recommendation.treatment } }}
                        sx={{ alignSelf: "flex-start", mt: 0.1 }}
                      />
                    }
                    label={
                      <Box sx={{ minWidth: 0, width: "100%" }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "flex-start",
                            justifyContent: "space-between",
                            gap: 1,
                          }}
                        >
                          <Typography component="span" sx={{ fontWeight: 750, overflowWrap: "anywhere" }}>
                            {recommendation.treatment}
                          </Typography>
                          <Typography
                            component="span"
                            variant="caption"
                            sx={{
                              flexShrink: 0,
                              px: 1,
                              py: 0.5,
                              borderRadius: 999,
                              bgcolor: selected ? "primary.light" : "#edf1f5",
                              color: selected ? "primary.dark" : "text.secondary",
                              fontWeight: 750,
                            }}
                          >
                            Priority {recommendation.position}
                          </Typography>
                        </Box>
                      </Box>
                    }
                    sx={{
                      m: 0,
                      p: { xs: 1.5, sm: 2 },
                      minWidth: 0,
                      minHeight: 88,
                      alignItems: "flex-start",
                      border: "1px solid",
                      borderColor: selected ? "primary.main" : "divider",
                      borderRadius: 1.5,
                      bgcolor: "background.paper",
                      boxShadow: selected ? "0 0 0 2px rgba(23, 105, 209, 0.12)" : "none",
                      transition: "border-color 120ms ease, box-shadow 120ms ease",
                      "&:hover": { borderColor: "primary.main" },
                    }}
                  />
                );
              })}
            </RadioGroup>
          </FormControl>

          {restartError === "not-restartable" && (
            <Alert severity="warning">This consultation cannot be restarted.</Alert>
          )}
          {restartError === "not-found" && (
            <Alert severity="warning">The source consultation is no longer available.</Alert>
          )}
          {restartError === "error" && (
            <Alert severity="error">Consultation could not be restarted. Please try again.</Alert>
          )}

          <Surface
            sx={{
              p: { xs: 2.5, sm: 3.5 },
              textAlign: "center",
              bgcolor: "#fbfcfe",
            }}
          >
            <Typography component="h2" variant="h2" sx={{ mb: 1 }}>
              Next Steps
            </Typography>
            <Typography color="text.secondary" sx={{ maxWidth: 560, mx: "auto", mb: 2.5 }}>
              Select a recommended treatment to continue to appointment booking,
              or restart the consultation to begin again.
            </Typography>
            <Box
              sx={{
                display: "flex",
                flexDirection: { xs: "column", sm: "row-reverse" },
                justifyContent: "center",
                gap: 1.5,
              }}
            >
              <Button
                variant="contained"
                disabled={!selectedRecommendationId}
                onClick={bookAppointment}
              >
                Book Appointment
              </Button>
              <Button variant="outlined" disabled={restartPending} onClick={restart}>
                {restartPending ? "Restarting…" : "Restart Consultation"}
              </Button>
            </Box>
          </Surface>
        </Stack>
      )}
    </Box>
  );
}
