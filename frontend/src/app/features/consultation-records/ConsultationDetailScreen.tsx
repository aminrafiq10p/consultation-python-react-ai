import { Alert, Box, CircularProgress, Paper, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { ConsultationApiError, consultationApi } from "./consultationApi";
import type { ConsultationRecord } from "./consultationTypes";

export interface ConsultationDetailService {
  detail: (consultationId: string) => Promise<ConsultationRecord>;
}

interface ConsultationDetailScreenProps {
  service?: ConsultationDetailService;
}

type DetailState =
  | { status: "loading"; consultationId?: string }
  | { status: "success"; consultationId: string; record: ConsultationRecord }
  | { status: "not-found"; consultationId: string }
  | { status: "error"; consultationId: string };

export function ConsultationDetailScreen({
  service = consultationApi,
}: ConsultationDetailScreenProps) {
  const { consultationId } = useParams();
  const [state, setState] = useState<DetailState>({ status: "loading" });

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

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        Consultation Details
      </Typography>

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
        <Paper sx={{ p: 3 }}>
          <Stack component="dl" spacing={2} sx={{ m: 0 }}>
            <Box>
              <Typography component="dt" variant="subtitle2">Patient name</Typography>
              <Typography component="dd" sx={{ m: 0 }}>{state.record.patient_name}</Typography>
            </Box>
            <Box>
              <Typography component="dt" variant="subtitle2">Primary concern</Typography>
              <Typography component="dd" sx={{ m: 0 }}>{state.record.primary_concern}</Typography>
            </Box>
            <Box>
              <Typography component="dt" variant="subtitle2">Recommended procedure</Typography>
              <Typography component="dd" sx={{ m: 0 }}>{state.record.recommended_procedure}</Typography>
            </Box>
            <Box>
              <Typography component="dt" variant="subtitle2">Status</Typography>
              <Typography component="dd" sx={{ m: 0 }}>{state.record.status}</Typography>
            </Box>
          </Stack>
        </Paper>
      )}
    </Box>
  );
}
