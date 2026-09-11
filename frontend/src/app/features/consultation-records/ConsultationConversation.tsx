import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  List,
  ListItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ConsultationApiError } from "./consultationApi";
import type {
  ConsultationMessage,
  ConsultationMessageExchange,
  ConsultationMessageHistory,
  ConsultationStatus,
  StructuredPayloadScalar,
} from "./consultationTypes";

const MAX_MESSAGE_LENGTH = 4_000;

export interface ConsultationConversationService {
  messages: (consultationId: string) => Promise<ConsultationMessageHistory>;
  submitMessage: (
    consultationId: string,
    content: string,
  ) => Promise<ConsultationMessageExchange>;
  generateSummary?: (consultationId: string) => Promise<unknown>;
}

interface ConsultationConversationProps {
  consultationId: string;
  service: ConsultationConversationService;
  onNotFound: () => void;
  consultationStatus: ConsultationStatus;
  onHistoryLoaded?: (messages: ConsultationMessage[]) => void;
  onConversationClosed?: () => void;
}

type HistoryState = "loading" | "loaded" | "error";
type SubmissionError = "ai-generation" | "conversation-closed" | "generic" | null;

const isScalar = (value: unknown): value is StructuredPayloadScalar =>
  value === null ||
  typeof value === "string" ||
  typeof value === "boolean" ||
  (typeof value === "number" && Number.isFinite(value));

const scalarText = (value: StructuredPayloadScalar) =>
  value === null ? "Not provided" : String(value);

function StructuredPayload({ message }: { message: ConsultationMessage }) {
  if (message.role !== "ASSISTANT" || message.structured_payload === null) {
    return null;
  }

  const supportedEntries = Object.entries(message.structured_payload).filter(
    ([, value]) =>
      isScalar(value) || (Array.isArray(value) && value.every(isScalar)),
  );
  if (supportedEntries.length === 0) return null;

  return (
    <List dense aria-label="Assistant details" sx={{ py: 0 }}>
      {supportedEntries.map(([key, value]) => (
        <ListItem key={key} disableGutters sx={{ display: "block" }}>
          <Typography component="span" variant="subtitle2">
            {key}
          </Typography>
          {Array.isArray(value) ? (
            <List dense sx={{ py: 0, pl: 2 }}>
              {value.map((item, index) => (
                <ListItem key={`${key}-${index}`} disableGutters>
                  <Typography variant="body2">{scalarText(item)}</Typography>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2">{scalarText(value)}</Typography>
          )}
        </ListItem>
      ))}
    </List>
  );
}

const reconcileMessages = (
  current: ConsultationMessage[],
  confirmed: ConsultationMessage[],
) => {
  const replacements = new Map(confirmed.map((message) => [message.id, message]));
  const reconciled = current.map(
    (message) => replacements.get(message.id) ?? message,
  );
  const existingIds = new Set(current.map((message) => message.id));
  return [
    ...reconciled,
    ...confirmed.filter((message) => !existingIds.has(message.id)),
  ];
};

export function ConsultationConversation({
  consultationId,
  service,
  onNotFound,
  consultationStatus,
  onHistoryLoaded,
  onConversationClosed,
}: ConsultationConversationProps) {
  const navigate = useNavigate();
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const [messages, setMessages] = useState<ConsultationMessage[]>([]);
  const [historyState, setHistoryState] = useState<HistoryState>("loading");
  const [draft, setDraft] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] =
    useState<SubmissionError>(null);
  const [closedByServer, setClosedByServer] = useState(false);
  const [handoffError, setHandoffError] = useState<string | null>(null);
  const [handoffPending, setHandoffPending] = useState(false);

  const readOnly = consultationStatus !== "PENDING" || closedByServer;

  const loadHistory = useCallback(async (showLoading = true) => {
    if (showLoading) setHistoryState("loading");
    try {
      const history = await service.messages(consultationId);
      setMessages(history.items);
      onHistoryLoaded?.(history.items);
      setHistoryState("loaded");
    } catch (error) {
      if (error instanceof ConsultationApiError && error.kind === "not-found") {
        onNotFound();
        return;
      }
      setHistoryState("error");
    }
  }, [consultationId, onHistoryLoaded, onNotFound, service]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const validateDraft = () => {
    const trimmedDraft = draft.trim();
    if (trimmedDraft.length === 0) {
      setValidationError("Enter a message before sending.");
      return null;
    }
    if (trimmedDraft.length > MAX_MESSAGE_LENGTH) {
      setValidationError("Message must be 4,000 characters or fewer.");
      return null;
    }
    setValidationError(null);
    return trimmedDraft;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting || readOnly) return;

    const content = validateDraft();
    if (content === null) return;

    setSubmitting(true);
    setSubmissionError(null);
    try {
      const exchange = await service.submitMessage(consultationId, content);
      setMessages((current) =>
        reconcileMessages(current, [
          exchange.user_message,
          exchange.assistant_message,
        ]),
      );
      setDraft("");
    } catch (error) {
      if (error instanceof ConsultationApiError && error.kind === "not-found") {
        onNotFound();
        return;
      }
      if (
        error instanceof ConsultationApiError &&
        error.kind === "conversation-closed"
      ) {
        setClosedByServer(true);
        onConversationClosed?.();
        setSubmissionError("conversation-closed");
      } else if (
        error instanceof ConsultationApiError &&
        error.kind === "ai-generation" &&
        error.persistedUserMessage
      ) {
        setMessages((current) =>
          reconcileMessages(current, [error.persistedUserMessage!]),
        );
        setDraft("");
        setSubmissionError("ai-generation");
      } else {
        setSubmissionError("generic");
      }
      await loadHistory(false);
    } finally {
      setSubmitting(false);
    }
  };

  const activateHandoff = async (message: ConsultationMessage) => {
    const handoff = message.handoff;
    if (!handoff || handoff.consultation_id !== consultationId || handoffPending) return;
    setHandoffError(null);
    if (handoff.action === "CONTINUE_CONSULTATION") {
      composerRef.current?.focus();
      return;
    }
    if (handoff.action === "VIEW_SUMMARY" || handoff.action === "VIEW_APPOINTMENTS") {
      navigate(handoff.target);
      return;
    }
    if (!service.generateSummary) return;
    setHandoffPending(true);
    try {
      await service.generateSummary(consultationId);
      navigate(`/consultations/${consultationId}/summary`);
    } catch (error) {
      setHandoffError(
        error instanceof ConsultationApiError && error.kind === "summary-not-eligible"
          ? "This consultation is not eligible for summary generation. Continue the conversation before trying again."
          : "The summary could not be generated right now. Please try again.",
      );
    } finally {
      setHandoffPending(false);
    }
  };

  const handoffLabel = (message: ConsultationMessage) => {
    switch (message.handoff?.action) {
      case "CONTINUE_CONSULTATION": return "Continue Consultation";
      case "GENERATE_SUMMARY": return "Generate Summary";
      case "VIEW_SUMMARY": return "View Summary";
      case "VIEW_APPOINTMENTS": return "View Appointments";
      default: return null;
    }
  };

  return (
    <Box component="section" aria-labelledby="conversation-heading" sx={{ mt: { xs: 3, md: 4 }, minWidth: 0 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", mb: 1.5 }}>
        <Typography id="conversation-heading" component="h2" variant="h2">AI conversation</Typography>
        <Typography variant="caption" color="text.secondary">Secure consultation workspace</Typography>
      </Box>

      {historyState === "loading" && (
        <Box role="status" sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          <CircularProgress size={24} />
          <span>Loading conversation…</span>
        </Box>
      )}

      {historyState === "error" && (
        <Alert
          severity="error"
          action={<Button onClick={() => void loadHistory()}>Retry</Button>}
        >
          Conversation could not be loaded. Please try again.
        </Alert>
      )}

      {historyState === "loaded" && messages.length === 0 && (
        <Alert severity="info">No messages yet. Start the conversation below.</Alert>
      )}

      {historyState === "loaded" && messages.length > 0 && (
        <Stack role="log" aria-label="Conversation messages" aria-live="polite" spacing={{ xs: 2, md: 2.5 }} sx={{ maxHeight: { xs: 460, md: 560 }, overflowY: "auto", px: { xs: 0.5, md: 1 }, py: 1 }}>
          {messages.map((message) => (
            <Box key={message.id} sx={{ alignSelf: message.role === "USER" ? "flex-end" : "flex-start", width: "100%", maxWidth: { xs: "94%", sm: "82%", md: "76%" } }}>
              <Box sx={{ display: "flex", gap: 1.25, alignItems: "flex-start", flexDirection: message.role === "USER" ? "row-reverse" : "row" }}>
                <Box aria-hidden sx={{ width: 30, height: 30, flexShrink: 0, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: message.role === "USER" ? "common.black" : "primary.light", color: message.role === "USER" ? "common.white" : "primary.dark", fontSize: 12, fontWeight: 800 }}>{message.role === "USER" ? "You" : "AI"}</Box>
                <Paper variant="outlined" sx={{ flex: 1, minWidth: 0, p: { xs: 1.75, md: 2.25 }, borderRadius: message.role === "USER" ? "16px 4px 16px 16px" : "4px 16px 16px 16px", bgcolor: message.role === "USER" ? "#edf1f5" : "background.paper", borderLeft: message.role === "ASSISTANT" ? "3px solid" : undefined, borderLeftColor: "primary.main", boxShadow: message.role === "ASSISTANT" ? "0 5px 18px rgba(26, 42, 65, 0.06)" : "none" }}>
                  <Typography variant="overline" sx={{ color: message.role === "ASSISTANT" ? "primary.dark" : "text.secondary", fontWeight: 800 }}>{message.role === "USER" ? "You" : "Auvia AI"}</Typography>
                  <Typography sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{message.content}</Typography>
                  {message.role === "ASSISTANT" && message.structured_payload !== null && <Divider sx={{ my: 1.5 }} />}
                  <StructuredPayload message={message} />
                  <Typography component="time" dateTime={message.created_at} variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>{message.created_at}</Typography>
                </Paper>
              </Box>
              {handoffLabel(message) && message.handoff?.consultation_id === consultationId && <Button variant="outlined" size="small" onClick={() => void activateHandoff(message)} disabled={handoffPending} sx={{ mt: 1, ml: { xs: 0, sm: message.role === "USER" ? 0 : 5 }, maxWidth: "100%", whiteSpace: "normal", textAlign: "left" }}>{handoffPending && message.handoff?.action === "GENERATE_SUMMARY" ? "Generating Summary…" : handoffLabel(message)}</Button>}
            </Box>
          ))}
        </Stack>
      )}

      {submissionError === "ai-generation" && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Your message was saved, but the assistant is temporarily unavailable. You can try again later.
        </Alert>
      )}
      {submissionError === "generic" && (
        <Alert severity="error" sx={{ mt: 2 }}>
          The message could not be completed. Conversation history was reloaded; please try again.
        </Alert>
      )}

      {submissionError === "conversation-closed" && (
        <Alert severity="info" sx={{ mt: 2 }}>
          This consultation is complete. The conversation is now read-only.
        </Alert>
      )}

      {handoffError && <Alert severity="warning" sx={{ mt: 2 }}>{handoffError}</Alert>}

      {historyState === "loaded" && consultationStatus !== "PENDING" && (
        <Alert severity="info" sx={{ mt: 2 }}>
          This conversation is read-only. Your previous messages remain available above.
        </Alert>
      )}

      {!readOnly && <Box component="form" onSubmit={handleSubmit} sx={{ mt: { xs: 3, md: 4 }, p: { xs: 1.5, sm: 2 }, border: 1, borderColor: "divider", borderRadius: 2, bgcolor: "background.paper", boxShadow: "0 5px 18px rgba(26, 42, 65, 0.06)" }} noValidate>
        <Stack spacing={1.25}>
          <TextField
            label="Message"
            placeholder="Ask Auvia about this consultation…"
            multiline
            minRows={2}
            value={draft}
            inputRef={composerRef}
            onChange={(event) => {
              setDraft(event.target.value);
              if (validationError) setValidationError(null);
            }}
            error={validationError !== null}
            helperText={validationError ?? `${draft.length} / ${MAX_MESSAGE_LENGTH}`}
            slotProps={{ htmlInput: { maxLength: MAX_MESSAGE_LENGTH + 1 } }}
            disabled={submitting}
          />
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2 }}>
            <Typography variant="caption" color="text.secondary">Auvia AI can make mistakes. Verify clinical information.</Typography>
            <Button type="submit" variant="contained" disabled={submitting} sx={{ minWidth: 132, flexShrink: 0 }}>
              {submitting ? "Sending…" : "Send message"}
            </Button>
          </Box>
        </Stack>
      </Box>}
    </Box>
  );
}
