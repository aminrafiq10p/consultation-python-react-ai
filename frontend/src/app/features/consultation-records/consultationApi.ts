import {
  CONSULTATION_STATUSES,
  MESSAGE_ROLES,
  type ConsultationListCriteria,
  type ConsultationListResponse,
  type ConsultationMessage,
  type ConsultationMessageExchange,
  type ConsultationMessageHistory,
  type ConsultationRecord,
  type ConsultationStatus,
  type MessageRole,
  type StructuredPayload,
  type StructuredPayloadScalar,
} from "./consultationTypes";

type FetchTransport = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

export type ConsultationApiErrorKind =
  | "not-found"
  | "validation"
  | "retrieval"
  | "submission"
  | "ai-generation";

export class ConsultationApiError extends Error {
  constructor(
    readonly kind: ConsultationApiErrorKind,
    readonly persistedUserMessage?: ConsultationMessage,
  ) {
    const messages: Record<ConsultationApiErrorKind, string> = {
      "not-found": "Consultation was not found.",
      validation: "The consultation request was invalid.",
      retrieval: "Consultation data could not be retrieved.",
      submission: "The consultation message could not be submitted.",
      "ai-generation": "The assistant response is temporarily unavailable.",
    };
    super(messages[kind]);
    this.name = "ConsultationApiError";
  }
}

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ISO_TIMESTAMP_PATTERN =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

const isStatus = (value: unknown): value is ConsultationStatus =>
  typeof value === "string" &&
  CONSULTATION_STATUSES.includes(value as ConsultationStatus);

const isMessageRole = (value: unknown): value is MessageRole =>
  typeof value === "string" && MESSAGE_ROLES.includes(value as MessageRole);

const isScalar = (value: unknown): value is StructuredPayloadScalar =>
  value === null ||
  typeof value === "string" ||
  typeof value === "boolean" ||
  (typeof value === "number" && Number.isFinite(value));

const structuredPayloadFromResponse = (value: unknown): StructuredPayload | null => {
  if (value === null) return null;
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new ConsultationApiError("retrieval");
  }

  const payload: StructuredPayload = {};
  for (const [key, item] of Object.entries(value)) {
    if (isScalar(item)) {
      payload[key] = item;
    } else if (Array.isArray(item) && item.every(isScalar)) {
      payload[key] = [...item];
    } else {
      throw new ConsultationApiError("retrieval");
    }
  }
  return payload;
};

const messageFromResponse = (value: unknown): ConsultationMessage => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ConsultationApiError("retrieval");
  }

  const message = value as Record<string, unknown>;
  if (
    typeof message.id !== "string" ||
    !UUID_PATTERN.test(message.id) ||
    typeof message.consultation_id !== "string" ||
    !UUID_PATTERN.test(message.consultation_id) ||
    !isMessageRole(message.role) ||
    typeof message.content !== "string" ||
    message.content.trim().length === 0 ||
    typeof message.created_at !== "string" ||
    !ISO_TIMESTAMP_PATTERN.test(message.created_at) ||
    Number.isNaN(Date.parse(message.created_at))
  ) {
    throw new ConsultationApiError("retrieval");
  }

  const structuredPayload = structuredPayloadFromResponse(
    message.structured_payload,
  );
  if (message.role === "USER" && structuredPayload !== null) {
    throw new ConsultationApiError("retrieval");
  }

  return {
    id: message.id,
    consultation_id: message.consultation_id,
    role: message.role,
    content: message.content,
    structured_payload: structuredPayload,
    created_at: message.created_at,
  };
};

const recordFromResponse = (value: unknown): ConsultationRecord => {
  if (typeof value !== "object" || value === null) {
    throw new ConsultationApiError("retrieval");
  }

  const record = value as Record<string, unknown>;
  if (
    typeof record.id !== "string" ||
    typeof record.patient_name !== "string" ||
    typeof record.primary_concern !== "string" ||
    typeof record.recommended_procedure !== "string" ||
    !isStatus(record.status)
  ) {
    throw new ConsultationApiError("retrieval");
  }

  return {
    id: record.id,
    patient_name: record.patient_name,
    primary_concern: record.primary_concern,
    recommended_procedure: record.recommended_procedure,
    status: record.status,
  };
};

const jsonResponse = async (response: Response): Promise<unknown> => {
  if (!response.ok) {
    throw new ConsultationApiError("retrieval");
  }

  try {
    return await response.json();
  } catch {
    throw new ConsultationApiError("retrieval");
  }
};

const safeRequest = async (
  request: () => Promise<unknown>,
  fallbackKind: ConsultationApiErrorKind = "retrieval",
): Promise<unknown> => {
  try {
    return await request();
  } catch (error) {
    if (error instanceof ConsultationApiError) {
      throw error;
    }
    throw new ConsultationApiError(fallbackKind);
  }
};

const responseBody = async (
  response: Response,
  fallbackKind: ConsultationApiErrorKind,
): Promise<unknown> => {
  try {
    return await response.json();
  } catch {
    throw new ConsultationApiError(fallbackKind);
  }
};

export const createConsultationApi = (
  transport: FetchTransport = globalThis.fetch.bind(globalThis),
) => ({
  async list(
    criteria: ConsultationListCriteria = {},
  ): Promise<ConsultationListResponse> {
    const query = new URLSearchParams();
    const search = criteria.search?.trim();
    if (search) query.set("search", search);
    if (criteria.status) query.set("status", criteria.status);

    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    const value = await safeRequest(async () =>
      jsonResponse(await transport(`/api/v1/consultations${suffix}`, { method: "GET" })),
    );

    if (typeof value !== "object" || value === null) {
      throw new ConsultationApiError("retrieval");
    }
    const items = (value as Record<string, unknown>).items;
    if (!Array.isArray(items)) {
      throw new ConsultationApiError("retrieval");
    }
    return { items: items.map(recordFromResponse) };
  },

  async detail(consultationId: string): Promise<ConsultationRecord> {
    const response = await safeRequest(() =>
      transport(`/api/v1/consultations/${encodeURIComponent(consultationId)}`, {
        method: "GET",
      }),
    );
    if (!(response instanceof Response)) {
      throw new ConsultationApiError("retrieval");
    }
    if (response.status === 404) {
      throw new ConsultationApiError("not-found");
    }
    return recordFromResponse(await jsonResponse(response));
  },

  async messages(consultationId: string): Promise<ConsultationMessageHistory> {
    const response = await safeRequest(() =>
      transport(
        `/api/v1/consultations/${encodeURIComponent(consultationId)}/messages`,
        { method: "GET" },
      ),
    );
    if (!(response instanceof Response)) {
      throw new ConsultationApiError("retrieval");
    }
    if (response.status === 400) throw new ConsultationApiError("validation");
    if (response.status === 404) throw new ConsultationApiError("not-found");
    if (!response.ok) throw new ConsultationApiError("retrieval");

    const value = await responseBody(response, "retrieval");
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      throw new ConsultationApiError("retrieval");
    }
    const items = (value as Record<string, unknown>).items;
    if (!Array.isArray(items)) throw new ConsultationApiError("retrieval");
    return { items: items.map(messageFromResponse) };
  },

  async submitMessage(
    consultationId: string,
    content: string,
  ): Promise<ConsultationMessageExchange> {
    const response = await safeRequest(
      () =>
        transport(
          `/api/v1/consultations/${encodeURIComponent(consultationId)}/messages`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content }),
          },
        ),
      "submission",
    );
    if (!(response instanceof Response)) {
      throw new ConsultationApiError("submission");
    }
    if (response.status === 400) throw new ConsultationApiError("validation");
    if (response.status === 404) throw new ConsultationApiError("not-found");

    if (response.status === 503) {
      const value = await responseBody(response, "submission");
      if (typeof value === "object" && value !== null && !Array.isArray(value)) {
        const recovery = value as Record<string, unknown>;
        if (recovery.code === "AI_GENERATION_FAILED") {
          try {
            const userMessage = messageFromResponse(recovery.user_message);
            if (userMessage.role === "USER") {
              throw new ConsultationApiError("ai-generation", userMessage);
            }
          } catch (error) {
            if (
              error instanceof ConsultationApiError &&
              error.kind === "ai-generation"
            ) {
              throw error;
            }
          }
        }
      }
      throw new ConsultationApiError("submission");
    }
    if (!response.ok) throw new ConsultationApiError("submission");

    const value = await responseBody(response, "submission");
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      throw new ConsultationApiError("submission");
    }
    const exchange = value as Record<string, unknown>;
    try {
      const userMessage = messageFromResponse(exchange.user_message);
      const assistantMessage = messageFromResponse(exchange.assistant_message);
      if (userMessage.role !== "USER" || assistantMessage.role !== "ASSISTANT") {
        throw new ConsultationApiError("submission");
      }
      return { user_message: userMessage, assistant_message: assistantMessage };
    } catch {
      throw new ConsultationApiError("submission");
    }
  },
});

export const consultationApi = createConsultationApi();
