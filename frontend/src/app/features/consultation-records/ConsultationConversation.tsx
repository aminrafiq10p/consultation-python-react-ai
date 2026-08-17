import {
  Alert,
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useCallback, useEffect, useState } from "react";

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
  const [messages, setMessages] = useState<ConsultationMessage[]>([]);
  const [historyState, setHistoryState] = useState<HistoryState>("loading");
  const [draft, setDraft] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] =
    useState<SubmissionError>(null);
  const [closedByServer, setClosedByServer] = useState(false);

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

  return (
    <Box component="section" aria-labelledby="conversation-heading" sx={{ mt: 3 }}>
      <Typography id="conversation-heading" component="h2" variant="h5" gutterBottom>
        AI conversation
      </Typography>

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
        <Stack aria-label="Conversation messages" spacing={2}>
          {messages.map((message) => (
            <Paper
              key={message.id}
              variant="outlined"
              sx={{
                p: 2,
                alignSelf: message.role === "USER" ? "flex-end" : "flex-start",
                maxWidth: "85%",
                bgcolor: message.role === "USER" ? "primary.50" : "background.paper",
              }}
            >
              <Typography variant="overline">
                {message.role === "USER" ? "You" : "Assistant"}
              </Typography>
              <Typography sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                {message.content}
              </Typography>
              <StructuredPayload message={message} />
              <Typography component="time" dateTime={message.created_at} variant="caption" color="text.secondary">
                {message.created_at}
              </Typography>
            </Paper>
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

      {historyState === "loaded" && consultationStatus !== "PENDING" && (
        <Alert severity="info" sx={{ mt: 2 }}>
          This conversation is read-only. Your previous messages remain available above.
        </Alert>
      )}

      {!readOnly && <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }} noValidate>
        <Stack spacing={1}>
          <TextField
            label="Message"
            multiline
            minRows={3}
            value={draft}
            onChange={(event) => {
              setDraft(event.target.value);
              if (validationError) setValidationError(null);
            }}
            error={validationError !== null}
            helperText={validationError ?? `${draft.length} / ${MAX_MESSAGE_LENGTH}`}
            slotProps={{ htmlInput: { maxLength: MAX_MESSAGE_LENGTH + 1 } }}
            disabled={submitting}
          />
          <Button type="submit" variant="contained" disabled={submitting} sx={{ alignSelf: "flex-start" }}>
            {submitting ? "Sending…" : "Send message"}
          </Button>
        </Stack>
      </Box>}
    </Box>
  );
}
