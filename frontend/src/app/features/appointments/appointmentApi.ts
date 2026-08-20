import type {
  AppointmentListItem,
  AppointmentListResponse,
} from "./appointmentTypes";

type FetchTransport = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ISO_TIMESTAMP_PATTERN =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-](\d{2}):(\d{2}))$/;

const apiUrl = (path: string): string => {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
  return `${baseUrl}${path}`;
};

export class AppointmentApiError extends Error {
  constructor() {
    super("Appointments could not be retrieved.");
    this.name = "AppointmentApiError";
  }
}

const hasExactKeys = (value: object, keys: readonly string[]): boolean => {
  const actualKeys = Object.keys(value);
  return (
    actualKeys.length === keys.length &&
    keys.every((key) => Object.prototype.hasOwnProperty.call(value, key))
  );
};

const isNonEmptyString = (value: unknown): value is string =>
  typeof value === "string" && value.trim().length > 0;

const isExplicitOffsetTimestamp = (value: unknown): value is string => {
  if (typeof value !== "string") return false;
  const match = ISO_TIMESTAMP_PATTERN.exec(value);
  if (!match || Number.isNaN(Date.parse(value))) return false;

  const [, year, month, day, hour, minute, second, offsetHour, offsetMinute] =
    match;
  const yearNumber = Number(year);
  const monthNumber = Number(month);
  const dayNumber = Number(day);
  const daysInMonth = new Date(
    Date.UTC(yearNumber, monthNumber, 0),
  ).getUTCDate();

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

const appointmentFromResponse = (value: unknown): AppointmentListItem => {
  const itemKeys = [
    "id",
    "consultation_id",
    "patient_name",
    "recommendation",
    "scheduled_at",
    "location",
    "created_at",
  ] as const;

  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value) ||
    !hasExactKeys(value, itemKeys)
  ) {
    throw new AppointmentApiError();
  }

  const item = value as Record<string, unknown>;
  const recommendation = item.recommendation;
  if (
    typeof recommendation !== "object" ||
    recommendation === null ||
    Array.isArray(recommendation) ||
    !hasExactKeys(recommendation, ["id", "treatment"])
  ) {
    throw new AppointmentApiError();
  }

  const recommendationRecord = recommendation as Record<string, unknown>;
  if (
    typeof item.id !== "string" ||
    !UUID_PATTERN.test(item.id) ||
    typeof item.consultation_id !== "string" ||
    !UUID_PATTERN.test(item.consultation_id) ||
    !isNonEmptyString(item.patient_name) ||
    typeof recommendationRecord.id !== "string" ||
    !UUID_PATTERN.test(recommendationRecord.id) ||
    !isNonEmptyString(recommendationRecord.treatment) ||
    !isExplicitOffsetTimestamp(item.scheduled_at) ||
    !isNonEmptyString(item.location) ||
    !isExplicitOffsetTimestamp(item.created_at)
  ) {
    throw new AppointmentApiError();
  }

  return {
    id: item.id,
    consultation_id: item.consultation_id,
    patient_name: item.patient_name,
    recommendation: {
      id: recommendationRecord.id,
      treatment: recommendationRecord.treatment,
    },
    scheduled_at: item.scheduled_at,
    location: item.location,
    created_at: item.created_at,
  };
};

const listFromResponse = (value: unknown): AppointmentListResponse => {
  if (
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value) ||
    !hasExactKeys(value, ["items"])
  ) {
    throw new AppointmentApiError();
  }

  const items = (value as Record<string, unknown>).items;
  if (!Array.isArray(items)) throw new AppointmentApiError();

  const seenAppointmentIds = new Set<string>();
  const validatedItems = items.map((item) => {
    const appointment = appointmentFromResponse(item);
    if (seenAppointmentIds.has(appointment.id)) {
      throw new AppointmentApiError();
    }
    seenAppointmentIds.add(appointment.id);
    return appointment;
  });

  return { items: validatedItems };
};

export const createAppointmentApi = (
  transport: FetchTransport = globalThis.fetch.bind(globalThis),
) => ({
  async listAppointments(): Promise<AppointmentListResponse> {
    try {
      const response = await transport(apiUrl("/api/v1/appointments"), {
        method: "GET",
      });
      if (!(response instanceof Response) || response.status !== 200) {
        throw new AppointmentApiError();
      }
      return listFromResponse(await response.json());
    } catch {
      throw new AppointmentApiError();
    }
  },
});

export const appointmentApi = createAppointmentApi();
