import {
  CONSULTATION_STATUSES,
  type ConsultationListCriteria,
  type ConsultationListResponse,
  type ConsultationRecord,
  type ConsultationStatus,
} from "./consultationTypes";

type FetchTransport = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

export type ConsultationApiErrorKind = "not-found" | "retrieval";

export class ConsultationApiError extends Error {
  constructor(readonly kind: ConsultationApiErrorKind) {
    super(
      kind === "not-found"
        ? "Consultation was not found."
        : "Consultation data could not be retrieved.",
    );
    this.name = "ConsultationApiError";
  }
}

const isStatus = (value: unknown): value is ConsultationStatus =>
  typeof value === "string" &&
  CONSULTATION_STATUSES.includes(value as ConsultationStatus);

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
): Promise<unknown> => {
  try {
    return await request();
  } catch (error) {
    if (error instanceof ConsultationApiError) {
      throw error;
    }
    throw new ConsultationApiError("retrieval");
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
});

export const consultationApi = createConsultationApi();
