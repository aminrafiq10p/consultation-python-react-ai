import type { DashboardResponse } from "./dashboardTypes";

type FetchTransport = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

const DASHBOARD_KEYS = [
  "total_consultations",
  "booked_appointments",
  "conversion_rate",
] as const;
const ACTIVITY_TYPES = [
  "conversation_started",
  "consultation_completed",
  "appointment_booked",
] as const;
const isActivityType = (value: unknown): value is (typeof ACTIVITY_TYPES)[number] =>
  ACTIVITY_TYPES.includes(value as (typeof ACTIVITY_TYPES)[number]);

const apiUrl = (path: string): string => {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
  return `${baseUrl}${path}`;
};

export class DashboardApiError extends Error {
  constructor() {
    super("Dashboard metrics could not be retrieved.");
    this.name = "DashboardApiError";
  }
}

const isNonnegativeSafeInteger = (value: unknown): value is number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= 0;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const hasExactKeys = (value: Record<string, unknown>, keys: readonly string[]) =>
  Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));

const isUuid = (value: unknown): value is string =>
  typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);

const isDate = (value: unknown): value is string => {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(parsed.valueOf()) && parsed.toISOString().slice(0, 10) === value;
};

const isDateTime = (value: unknown): value is string =>
  typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) && !Number.isNaN(Date.parse(value));

const dashboardFromResponse = (value: unknown): DashboardResponse => {
  if (!isRecord(value) || !hasExactKeys(value, [...DASHBOARD_KEYS, "consultation_trends", "recent_activity", "pending_clinical_reviews"])) {
    throw new DashboardApiError();
  }

  const metrics = value;
  const { total_consultations: totalConsultations, booked_appointments: bookedAppointments, conversion_rate: conversionRate } = metrics;

  if (
    !isNonnegativeSafeInteger(totalConsultations) ||
    !isNonnegativeSafeInteger(bookedAppointments) ||
    typeof conversionRate !== "number" ||
    !Number.isFinite(conversionRate) ||
    conversionRate < 0 ||
    conversionRate > 100 ||
    bookedAppointments > totalConsultations ||
    (totalConsultations === 0 &&
      (bookedAppointments !== 0 || conversionRate !== 0))
  ) {
    throw new DashboardApiError();
  }

  const trends = metrics.consultation_trends;
  const activity = metrics.recent_activity;
  const reviews = metrics.pending_clinical_reviews;
  if (!Array.isArray(trends) || !Array.isArray(activity) || !Array.isArray(reviews)) throw new DashboardApiError();
  const parsedTrends = trends.map((item) => {
    if (!isRecord(item) || !hasExactKeys(item, ["day", "consultation_count"]) || !isDate(item.day) || !isNonnegativeSafeInteger(item.consultation_count) || item.consultation_count < 1) throw new DashboardApiError();
    return { day: item.day, consultation_count: item.consultation_count };
  });
  const parsedActivity = activity.map((item) => {
    if (!isRecord(item) || !hasExactKeys(item, ["activity_type", "consultation_id", "timestamp"]) || !isActivityType(item.activity_type) || !isUuid(item.consultation_id) || !isDateTime(item.timestamp)) throw new DashboardApiError();
    return { activity_type: item.activity_type, consultation_id: item.consultation_id, timestamp: item.timestamp };
  });
  const parsedReviews = reviews.map((item) => {
    if (!isRecord(item) || !hasExactKeys(item, ["consultation_id", "patient_name", "primary_concern", "recommended_procedure", "status"]) || !isUuid(item.consultation_id) || typeof item.patient_name !== "string" || item.patient_name.length < 1 || typeof item.primary_concern !== "string" || item.primary_concern.length < 1 || typeof item.recommended_procedure !== "string" || item.status !== "PENDING") throw new DashboardApiError();
    return { consultation_id: item.consultation_id, patient_name: item.patient_name, primary_concern: item.primary_concern, recommended_procedure: item.recommended_procedure, status: "PENDING" as const };
  });
  return {
    total_consultations: totalConsultations,
    booked_appointments: bookedAppointments,
    conversion_rate: conversionRate,
    consultation_trends: parsedTrends,
    recent_activity: parsedActivity,
    pending_clinical_reviews: parsedReviews,
  };
};

export const createDashboardApi = (
  transport: FetchTransport = globalThis.fetch.bind(globalThis),
) => ({
  async getMetrics(): Promise<DashboardResponse> {
    try {
      const response = await transport(apiUrl("/api/v1/dashboard"), {
        method: "GET",
      });
      if (response.status !== 200) throw new DashboardApiError();
      return dashboardFromResponse(await response.json());
    } catch {
      throw new DashboardApiError();
    }
  },
});

export const dashboardApi = createDashboardApi();
