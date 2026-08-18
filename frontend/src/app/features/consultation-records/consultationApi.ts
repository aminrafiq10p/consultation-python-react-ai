import {
  CONSULTATION_STATUSES,
  MESSAGE_ROLES,
  type Appointment,
  type AppointmentBookingRequest,
  type ConsultationListCriteria,
  type ConsultationListResponse,
  type ConsultationCreationRequest,
  type ConsultationMessage,
  type ConsultationMessageExchange,
  type ConsultationMessageHistory,
  type ConsultationRecord,
  type ConsultationSummary,
  type ConsultationStatus,
  type MessageRole,
  type Recommendation,
  type StructuredPayload,
  type StructuredPayloadScalar,
} from "./consultationTypes";

type FetchTransport = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

const apiUrl = (path: string): string => {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
  return `${baseUrl}${path}`;
};

export type ConsultationApiErrorKind =
  | "not-found"
  | "validation"
  | "retrieval"
  | "submission"
  | "creation-validation"
  | "creation-submission"
  | "ai-generation"
  | "summary-not-available"
  | "summary-not-eligible"
  | "summary-generation"
  | "not-restartable"
  | "conversation-closed"
  | "booking-validation"
  | "booking-consultation-not-found"
  | "booking-recommendation-not-found"
  | "recommendation-not-bookable"
  | "consultation-not-bookable"
  | "appointment-already-exists"
  | "booking-submission";

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
      "creation-validation": "The consultation details were invalid.",
      "creation-submission":
        "Creation could not be confirmed. Check consultation records before retrying.",
      "ai-generation": "The assistant response is temporarily unavailable.",
      "summary-not-available": "A consultation summary is not available.",
      "summary-not-eligible": "The consultation is not eligible for a summary.",
      "summary-generation": "The consultation summary could not be generated.",
      "not-restartable": "The consultation cannot be restarted.",
      "conversation-closed": "The consultation conversation is closed.",
      "booking-validation": "The appointment request was invalid.",
      "booking-consultation-not-found": "The consultation was not found.",
      "booking-recommendation-not-found": "The recommendation was not found.",
      "recommendation-not-bookable": "The recommendation cannot be booked.",
      "consultation-not-bookable": "The consultation cannot be booked.",
      "appointment-already-exists": "An appointment already exists.",
      "booking-submission":
        "The appointment could not be confirmed. Check consultation records before retrying.",
    };
    super(messages[kind]);
    this.name = "ConsultationApiError";
  }
}

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ISO_TIMESTAMP_PATTERN =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-](\d{2}):(\d{2}))$/;

const isExplicitOffsetTimestamp = (value: unknown): value is string => {
  if (typeof value !== "string") return false;
  const match = ISO_TIMESTAMP_PATTERN.exec(value);
  if (!match || Number.isNaN(Date.parse(value))) return false;

  const [, year, month, day, hour, minute, second, offsetHour, offsetMinute] =
    match;
  const yearNumber = Number(year);
  const monthNumber = Number(month);
  const dayNumber = Number(day);
  const daysInMonth = new Date(Date.UTC(yearNumber, monthNumber, 0)).getUTCDate();

  return (
    monthNumber >= 1 &&
    monthNumber <= 12 &&
    dayNumber >= 1 &&
    dayNumber <= daysInMonth &&
    Number(hour) <= 23 &&
    Number(minute) <= 59 &&
    Number(second) <= 59 &&
    (offsetHour === undefined ||
      (Number(offsetHour) <= 23 && Number(offsetMinute) <= 59))
  );
};

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
    !isExplicitOffsetTimestamp(message.created_at)
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
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ConsultationApiError("retrieval");
  }

  const record = value as Record<string, unknown>;
  if (
    typeof record.id !== "string" ||
    !UUID_PATTERN.test(record.id) ||
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

const creationRecordFromResponse = (
  value: unknown,
  request: ConsultationCreationRequest,
): ConsultationRecord => {
  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value) ||
    Object.keys(value).length !== 5 ||
    ![
      "id",
      "patient_name",
      "primary_concern",
      "recommended_procedure",
      "status",
    ].every((key) => Object.prototype.hasOwnProperty.call(value, key))
  ) {
    throw new ConsultationApiError("creation-submission");
  }

  let record: ConsultationRecord;
  try {
    record = recordFromResponse(value);
  } catch {
    throw new ConsultationApiError("creation-submission");
  }
  if (
    record.patient_name !== request.patient_name ||
    record.primary_concern !== request.primary_concern ||
    record.recommended_procedure !== "" ||
    record.status !== "PENDING"
  ) {
    throw new ConsultationApiError("creation-submission");
  }
  return record;
};

const recommendationFromResponse = (value: unknown): Recommendation => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ConsultationApiError("retrieval");
  }

  const recommendation = value as Record<string, unknown>;
  if (
    typeof recommendation.id !== "string" ||
    !UUID_PATTERN.test(recommendation.id) ||
    typeof recommendation.treatment !== "string" ||
    recommendation.treatment.trim().length === 0 ||
    !Number.isInteger(recommendation.position) ||
    (recommendation.position as number) <= 0
  ) {
    throw new ConsultationApiError("retrieval");
  }

  return {
    id: recommendation.id,
    treatment: recommendation.treatment,
    position: recommendation.position as number,
  };
};

const summaryFromResponse = (
  value: unknown,
  consultationId: string,
): ConsultationSummary => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ConsultationApiError("retrieval");
  }

  const summary = value as Record<string, unknown>;
  if (
    typeof summary.id !== "string" ||
    !UUID_PATTERN.test(summary.id) ||
    typeof summary.consultation_id !== "string" ||
    !UUID_PATTERN.test(summary.consultation_id) ||
    summary.consultation_id !== consultationId ||
    typeof summary.patient_summary !== "string" ||
    summary.patient_summary.trim().length === 0 ||
    !Array.isArray(summary.recommended_treatments) ||
    summary.recommended_treatments.length === 0 ||
    !(
      summary.recommendation_rationale === null ||
      (typeof summary.recommendation_rationale === "string" &&
        summary.recommendation_rationale.trim().length > 0)
    ) ||
    typeof summary.created_at !== "string" ||
    !isExplicitOffsetTimestamp(summary.created_at)
  ) {
    throw new ConsultationApiError("retrieval");
  }

  const recommendations = summary.recommended_treatments.map(
    recommendationFromResponse,
  );
  const ids = new Set<string>();
  const positions = new Set<number>();
  let previousPosition = 0;
  for (const recommendation of recommendations) {
    if (
      ids.has(recommendation.id) ||
      positions.has(recommendation.position) ||
      recommendation.position <= previousPosition
    ) {
      throw new ConsultationApiError("retrieval");
    }
    ids.add(recommendation.id);
    positions.add(recommendation.position);
    previousPosition = recommendation.position;
  }

  return {
    id: summary.id,
    consultation_id: summary.consultation_id,
    patient_summary: summary.patient_summary,
    recommended_treatments: recommendations,
    recommendation_rationale: summary.recommendation_rationale,
    created_at: summary.created_at,
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

const hasErrorCode = (value: unknown, code: string): boolean =>
  typeof value === "object" &&
  value !== null &&
  !Array.isArray(value) &&
  typeof (value as Record<string, unknown>).error === "string" &&
  ((value as Record<string, unknown>).error as string).trim().length > 0 &&
  (value as Record<string, unknown>).code === code;

const hasExactError = (value: unknown, message: string): boolean =>
  typeof value === "object" &&
  value !== null &&
  !Array.isArray(value) &&
  Object.keys(value).length === 1 &&
  (value as Record<string, unknown>).error === message;

const appointmentFromResponse = (
  value: unknown,
  consultationId: string,
  recommendationId: string,
): Appointment => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ConsultationApiError("booking-submission");
  }

  const appointment = value as Record<string, unknown>;
  const recommendation = appointment.recommendation;
  if (
    typeof appointment.id !== "string" ||
    !UUID_PATTERN.test(appointment.id) ||
    typeof appointment.consultation_id !== "string" ||
    !UUID_PATTERN.test(appointment.consultation_id) ||
    appointment.consultation_id !== consultationId ||
    typeof recommendation !== "object" ||
    recommendation === null ||
    Array.isArray(recommendation)
  ) {
    throw new ConsultationApiError("booking-submission");
  }

  const persistedRecommendation = recommendation as Record<string, unknown>;
  if (
    typeof persistedRecommendation.id !== "string" ||
    !UUID_PATTERN.test(persistedRecommendation.id) ||
    persistedRecommendation.id !== recommendationId ||
    typeof persistedRecommendation.treatment !== "string" ||
    persistedRecommendation.treatment.trim().length === 0 ||
    !isExplicitOffsetTimestamp(appointment.scheduled_at) ||
    typeof appointment.location !== "string" ||
    appointment.location.trim().length === 0 ||
    appointment.location !== appointment.location.trim() ||
    Array.from(appointment.location).length > 200 ||
    !isExplicitOffsetTimestamp(appointment.created_at)
  ) {
    throw new ConsultationApiError("booking-submission");
  }

  return {
    id: appointment.id,
    consultation_id: appointment.consultation_id,
    recommendation: {
      id: persistedRecommendation.id,
      treatment: persistedRecommendation.treatment,
    },
    scheduled_at: appointment.scheduled_at,
    location: appointment.location,
    created_at: appointment.created_at,
  };
};

const codedErrorKind = async (
  response: Response,
  status: number,
  code: string,
  kind: ConsultationApiErrorKind,
  fallbackKind: ConsultationApiErrorKind,
): Promise<never> => {
  if (response.status === status) {
    const value = await responseBody(response, fallbackKind);
    if (hasErrorCode(value, code)) throw new ConsultationApiError(kind);
  }
  throw new ConsultationApiError(fallbackKind);
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
      jsonResponse(
        await transport(apiUrl(`/api/v1/consultations${suffix}`), { method: "GET" }),
      ),
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
      transport(apiUrl(`/api/v1/consultations/${encodeURIComponent(consultationId)}`), {
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

  async createConsultation(
    request: ConsultationCreationRequest,
  ): Promise<ConsultationRecord> {
    const normalizedRequest = {
      patient_name: request.patient_name.trim(),
      primary_concern: request.primary_concern.trim(),
    };

    const response = await safeRequest(
      () =>
        transport(apiUrl("/api/v1/consultations"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(normalizedRequest),
        }),
      "creation-submission",
    );
    if (!(response instanceof Response)) {
      throw new ConsultationApiError("creation-submission");
    }

    if (response.status === 400) {
      const value = await responseBody(response, "creation-submission");
      if (hasExactError(value, "Invalid request")) {
        throw new ConsultationApiError("creation-validation");
      }
      throw new ConsultationApiError("creation-submission");
    }
    if (response.status !== 201) {
      throw new ConsultationApiError("creation-submission");
    }

    try {
      return creationRecordFromResponse(
        await responseBody(response, "creation-submission"),
        normalizedRequest,
      );
    } catch (error) {
      if (error instanceof ConsultationApiError) throw error;
      throw new ConsultationApiError("creation-submission");
    }
  },

  async messages(consultationId: string): Promise<ConsultationMessageHistory> {
    const response = await safeRequest(() =>
      transport(
        apiUrl(`/api/v1/consultations/${encodeURIComponent(consultationId)}/messages`),
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
          apiUrl(`/api/v1/consultations/${encodeURIComponent(consultationId)}/messages`),
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

    if (response.status === 409) {
      await codedErrorKind(
        response,
        409,
        "CONSULTATION_CONVERSATION_CLOSED",
        "conversation-closed",
        "submission",
      );
    }

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

  async summary(consultationId: string): Promise<ConsultationSummary> {
    const response = await safeRequest(() =>
      transport(
        apiUrl(`/api/v1/consultations/${encodeURIComponent(consultationId)}/summary`),
        { method: "GET" },
      ),
    );
    if (!(response instanceof Response)) throw new ConsultationApiError("retrieval");
    if (response.status === 400) throw new ConsultationApiError("validation");
    if (response.status === 404) throw new ConsultationApiError("not-found");
    if (response.status === 409) {
      await codedErrorKind(
        response,
        409,
        "SUMMARY_NOT_AVAILABLE",
        "summary-not-available",
        "retrieval",
      );
    }
    if (response.status !== 200) throw new ConsultationApiError("retrieval");
    return summaryFromResponse(
      await responseBody(response, "retrieval"),
      consultationId,
    );
  },

  async generateSummary(consultationId: string): Promise<ConsultationSummary> {
    const response = await safeRequest(
      () =>
        transport(
          apiUrl(`/api/v1/consultations/${encodeURIComponent(consultationId)}/summary`),
          { method: "POST" },
        ),
      "submission",
    );
    if (!(response instanceof Response)) throw new ConsultationApiError("submission");
    if (response.status === 400) throw new ConsultationApiError("validation");
    if (response.status === 404) throw new ConsultationApiError("not-found");
    if (response.status === 409) {
      await codedErrorKind(
        response,
        409,
        "SUMMARY_NOT_ELIGIBLE",
        "summary-not-eligible",
        "submission",
      );
    }
    if (response.status === 503) {
      await codedErrorKind(
        response,
        503,
        "SUMMARY_GENERATION_FAILED",
        "summary-generation",
        "submission",
      );
    }
    if (response.status !== 200 && response.status !== 201) {
      throw new ConsultationApiError("submission");
    }
    try {
      return summaryFromResponse(
        await responseBody(response, "submission"),
        consultationId,
      );
    } catch {
      throw new ConsultationApiError("submission");
    }
  },

  async restartConsultation(consultationId: string): Promise<ConsultationRecord> {
    const response = await safeRequest(
      () =>
        transport(
          apiUrl(`/api/v1/consultations/${encodeURIComponent(consultationId)}/restart`),
          { method: "POST" },
        ),
      "submission",
    );
    if (!(response instanceof Response)) throw new ConsultationApiError("submission");
    if (response.status === 400) throw new ConsultationApiError("validation");
    if (response.status === 404) throw new ConsultationApiError("not-found");
    if (response.status === 409) {
      await codedErrorKind(
        response,
        409,
        "CONSULTATION_NOT_RESTARTABLE",
        "not-restartable",
        "submission",
      );
    }
    if (response.status !== 201) throw new ConsultationApiError("submission");
    try {
      return recordFromResponse(await responseBody(response, "submission"));
    } catch {
      throw new ConsultationApiError("submission");
    }
  },

  async bookAppointment(
    consultationId: string,
    request: AppointmentBookingRequest,
  ): Promise<Appointment> {
    const response = await safeRequest(
      () =>
        transport(
          apiUrl(
            `/api/v1/consultations/${encodeURIComponent(consultationId)}/appointments`,
          ),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              recommendation_id: request.recommendation_id,
              scheduled_at: request.scheduled_at,
              location: request.location,
            }),
          },
        ),
      "booking-submission",
    );
    if (!(response instanceof Response)) {
      throw new ConsultationApiError("booking-submission");
    }

    if (response.status === 400) {
      const value = await responseBody(response, "booking-submission");
      if (hasExactError(value, "Invalid request")) {
        throw new ConsultationApiError("booking-validation");
      }
      throw new ConsultationApiError("booking-submission");
    }
    if (response.status === 404) {
      const value = await responseBody(response, "booking-submission");
      if (hasExactError(value, "Consultation not found")) {
        throw new ConsultationApiError("booking-consultation-not-found");
      }
      if (hasExactError(value, "Recommendation not found")) {
        throw new ConsultationApiError("booking-recommendation-not-found");
      }
      throw new ConsultationApiError("booking-submission");
    }
    if (response.status === 409) {
      const value = await responseBody(response, "booking-submission");
      if (hasErrorCode(value, "RECOMMENDATION_NOT_BOOKABLE")) {
        throw new ConsultationApiError("recommendation-not-bookable");
      }
      if (hasErrorCode(value, "CONSULTATION_NOT_BOOKABLE")) {
        throw new ConsultationApiError("consultation-not-bookable");
      }
      if (hasErrorCode(value, "APPOINTMENT_ALREADY_EXISTS")) {
        throw new ConsultationApiError("appointment-already-exists");
      }
      throw new ConsultationApiError("booking-submission");
    }
    if (response.status !== 201) {
      throw new ConsultationApiError("booking-submission");
    }

    try {
      return appointmentFromResponse(
        await responseBody(response, "booking-submission"),
        consultationId,
        request.recommendation_id,
      );
    } catch {
      throw new ConsultationApiError("booking-submission");
    }
  },
});

export const consultationApi = createConsultationApi();
