import { Alert, Avatar, Box, Button, CircularProgress, Typography } from "@mui/material";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ConsultationApiError, consultationApi } from "./consultationApi";
import {
  ConsultationConversation,
  type ConsultationConversationService,
} from "./ConsultationConversation";
import type { ConsultationMessage, ConsultationRecord } from "./consultationTypes";
import { PageHeader, StatusChip, Surface } from "../../ui/visualSystem";

export interface ConsultationDetailService extends ConsultationConversationService {
  detail: (consultationId: string) => Promise<ConsultationRecord>;
  generateSummary: (consultationId: string) => Promise<unknown>;
}

interface ConsultationDetailScreenProps {
  service?: ConsultationDetailService;
}

type DetailState =
  | { status: "loading"; consultationId?: string }
  | { status: "success"; consultationId: string; record: ConsultationRecord }
  | { status: "not-found"; consultationId: string }
  | { status: "error"; consultationId: string };

type GenerationError = "not-eligible" | "generation" | "generic" | null;

function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

export function ConsultationDetailScreen({
  service = consultationApi,
}: ConsultationDetailScreenProps) {
  const { consultationId } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState<DetailState>({ status: "loading" });
  const [history, setHistory] = useState<ConsultationMessage[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<GenerationError>(null);
  const [conversationClosed, setConversationClosed] = useState(false);

  useEffect(() => {
    let active = true;

    if (!consultationId) {
      return () => {
        active = false;
      };
    }

    service.detail(consultationId).then(
      (record) => {
        if (active) setState({ status: "success", consultationId, record });
      },
      (error: unknown) => {
        if (!active) return;
        setState({
          status:
            error instanceof ConsultationApiError && error.kind === "not-found"
              ? "not-found"
              : "error",
          consultationId,
        });
      },
    );

    return () => {
      active = false;
    };
  }, [consultationId, service]);

  const visibleStatus = !consultationId
    ? "error"
    : state.consultationId === consultationId
      ? state.status
      : "loading";

  const handleConversationNotFound = useCallback(() => {
    if (consultationId) {
      setState({ status: "not-found", consultationId });
    }
  }, [consultationId]);

  const handleHistoryLoaded = useCallback((messages: ConsultationMessage[]) => {
    setHistory(messages);
  }, []);

  const handleGenerateSummary = async () => {
    if (!consultationId || generating) return;
    setGenerating(true);
    setGenerationError(null);
    try {
      await service.generateSummary(consultationId);
      navigate(`/consultations/${consultationId}/summary`);
    } catch (error) {
      if (error instanceof ConsultationApiError && error.kind === "not-found") {
        setState({ status: "not-found", consultationId });
      } else if (
        error instanceof ConsultationApiError &&
        error.kind === "summary-not-eligible"
      ) {
        setGenerationError("not-eligible");
      } else if (
        error instanceof ConsultationApiError &&
        error.kind === "summary-generation"
      ) {
        setGenerationError("generation");
      } else {
        setGenerationError("generic");
      }
    } finally {
      setGenerating(false);
    }
  };

  const eligibleForSummary =
    state.status === "success" &&
    state.record.status === "PENDING" &&
    !conversationClosed &&
    history !== null &&
    history.every((message) => message.consultation_id === state.consultationId) &&
    history.some((message) => message.role === "USER") &&
    history.some((message) => message.role === "ASSISTANT") &&
    history.at(-1)?.role === "ASSISTANT";

  return (
    <Box sx={{ minWidth: 0 }}>
      <PageHeader title="Consultation Details" subtitle="Review the consultation and continue the conversation." />

      {visibleStatus === "loading" && (
        <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <CircularProgress size={24} />
          <span>Loading consultation details…</span>
        </Box>
      )}

      {visibleStatus === "not-found" && (
        <Alert severity="info">
          Consultation not found. This consultation is unavailable.
        </Alert>
      )}

      {visibleStatus === "error" && (
        <Alert severity="error">
          Consultation details could not be loaded. Please try again.
        </Alert>
      )}

      {visibleStatus === "success" && state.status === "success" && (
        <>
          <Surface sx={{ p: { xs: 2, sm: 2.5 } }}>
            <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 2, alignItems: { xs: "flex-start", sm: "center" } }}>
              <Avatar sx={{ width: 52, height: 52, bgcolor: "primary.light", color: "primary.dark", fontWeight: 800 }}>{initials(state.record.patient_name)}</Avatar>
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography component="h2" variant="h2">{state.record.patient_name}</Typography>
                <Typography color="text.secondary" sx={{ mt: 0.5, overflowWrap: "anywhere" }}>{state.record.primary_concern}</Typography>
              </Box>
              <StatusChip label={state.record.status} />
            </Box>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" }, gap: 2, mt: 2.5, pt: 2, borderTop: 1, borderColor: "divider" }}>
              <Box><Typography variant="caption" color="text.secondary">Recommended procedure</Typography><Typography sx={{ fontWeight: 700, mt: 0.25 }}>{state.record.recommended_procedure}</Typography></Box>
            </Box>
          </Surface>
          {eligibleForSummary && (
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={() => void handleGenerateSummary()}
                disabled={generating}
              >
                {generating ? "Generating Summary…" : "Generate Summary"}
              </Button>
            </Box>
          )}
          {state.record.status === "COMPLETED" && (
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={() => navigate(`/consultations/${state.consultationId}/summary`)}
              >
                View Summary
              </Button>
            </Box>
          )}
          {generationError === "not-eligible" && (
            <Alert severity="info" sx={{ mt: 2 }}>
              This consultation is not eligible for summary generation. Continue the conversation before trying again.
            </Alert>
          )}
          {generationError === "generation" && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              The summary could not be generated right now. Please try again.
            </Alert>
          )}
          {generationError === "generic" && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Summary generation could not be completed. Please try again.
            </Alert>
          )}
          <ConsultationConversation
            consultationId={state.consultationId}
            service={service}
            onNotFound={handleConversationNotFound}
            consultationStatus={state.record.status}
            onHistoryLoaded={handleHistoryLoaded}
            onConversationClosed={() => setConversationClosed(true)}
          />
        </>
      )}
    </Box>
  );
}
