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
import { type FormEvent, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ConsultationApiError, consultationApi } from "./consultationApi";
import type { ConsultationCreationRequest, ConsultationRecord } from "./consultationTypes";

const MAX_PATIENT_NAME_LENGTH = 200;
const MAX_PRIMARY_CONCERN_LENGTH = 4_000;

export interface NewConsultationService {
  createConsultation: (
    request: ConsultationCreationRequest,
  ) => Promise<ConsultationRecord>;
}

interface NewConsultationScreenProps {
  service?: NewConsultationService;
}

type FormError = "validation" | "ambiguous" | null;

const characterCount = (value: string) => Array.from(value).length;

export function NewConsultationScreen({
  service = consultationApi,
}: NewConsultationScreenProps) {
  const navigate = useNavigate();
  const patientNameInput = useRef<HTMLInputElement>(null);
  const primaryConcernInput = useRef<HTMLInputElement>(null);
  const inFlight = useRef(false);
  const [patientName, setPatientName] = useState("");
  const [primaryConcern, setPrimaryConcern] = useState("");
  const [patientNameError, setPatientNameError] = useState<string | null>(null);
  const [primaryConcernError, setPrimaryConcernError] = useState<string | null>(null);
  const [formError, setFormError] = useState<FormError>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (inFlight.current) return;

    const normalizedPatientName = patientName.trim();
    const normalizedPrimaryConcern = primaryConcern.trim();
    let firstInvalid: "patient-name" | "primary-concern" | null = null;

    if (characterCount(normalizedPatientName) === 0) {
      setPatientNameError("Patient name is required.");
      firstInvalid = "patient-name";
    } else if (characterCount(normalizedPatientName) > MAX_PATIENT_NAME_LENGTH) {
      setPatientNameError("Patient name must be 200 characters or fewer.");
      firstInvalid = "patient-name";
    } else {
      setPatientNameError(null);
    }

    if (characterCount(normalizedPrimaryConcern) === 0) {
      setPrimaryConcernError("Primary concern is required.");
      firstInvalid ??= "primary-concern";
    } else if (characterCount(normalizedPrimaryConcern) > MAX_PRIMARY_CONCERN_LENGTH) {
      setPrimaryConcernError("Primary concern must be 4,000 characters or fewer.");
      firstInvalid ??= "primary-concern";
    } else {
      setPrimaryConcernError(null);
    }

    if (firstInvalid) {
      setFormError(null);
      if (firstInvalid === "patient-name") patientNameInput.current?.focus();
      else primaryConcernInput.current?.focus();
      return;
    }

    inFlight.current = true;
    setPatientName(normalizedPatientName);
    setPrimaryConcern(normalizedPrimaryConcern);
    setSubmitting(true);
    setFormError(null);

    let completed = false;
    try {
      const consultation = await service.createConsultation({
        patient_name: normalizedPatientName,
        primary_concern: normalizedPrimaryConcern,
      });
      completed = true;
      navigate(`/consultations/${consultation.id}`, { replace: true });
    } catch (error) {
      setFormError(
        error instanceof ConsultationApiError && error.kind === "creation-validation"
          ? "validation"
          : "ambiguous",
      );
    } finally {
      if (!completed) {
        inFlight.current = false;
        setSubmitting(false);
      }
    }
  };

  const cancel = () => {
    if (!inFlight.current) navigate("/consultations");
  };

  return (
    <Box>
      <Typography component="h1" variant="h4" gutterBottom>
        New Consultation
      </Typography>
      <Paper sx={{ maxWidth: 760, p: { xs: 2.5, sm: 3 } }}>
        <Box component="form" noValidate onSubmit={submit}>
          <Stack spacing={3}>
            <Typography color="text.secondary">
              Start a consultation with the patient’s name and primary concern.
            </Typography>
            {formError === "validation" && (
              <Alert severity="warning" role="alert">
                The consultation details could not be accepted. Review the highlighted fields and try again.
              </Alert>
            )}
            {formError === "ambiguous" && (
              <Alert severity="error" role="alert">
                Creation could not be confirmed. Check Consultation Records before deliberately trying again.
              </Alert>
            )}
            <TextField
              inputRef={patientNameInput}
              label="Patient name"
              required
              fullWidth
              value={patientName}
              disabled={submitting}
              error={Boolean(patientNameError)}
              helperText={patientNameError ?? "Up to 200 characters."}
              onChange={(event) => setPatientName(event.target.value)}
            />
            <TextField
              inputRef={primaryConcernInput}
              label="Primary concern"
              required
              fullWidth
              multiline
              minRows={5}
              value={primaryConcern}
              disabled={submitting}
              error={Boolean(primaryConcernError)}
              helperText={primaryConcernError ?? "Up to 4,000 characters."}
              onChange={(event) => setPrimaryConcern(event.target.value)}
            />
            {submitting && (
              <Box role="status" sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <CircularProgress size={20} />
                <span>Starting consultation…</span>
              </Box>
            )}
            <Stack direction={{ xs: "column-reverse", sm: "row" }} spacing={2}>
              <Button type="button" variant="outlined" disabled={submitting} onClick={cancel}>
                Cancel
              </Button>
              <Button type="submit" variant="contained" disabled={submitting}>
                {submitting ? "Starting Consultation…" : "Start Consultation"}
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
}
