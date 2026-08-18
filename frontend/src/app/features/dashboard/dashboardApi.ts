import type { DashboardMetrics } from "./dashboardTypes";

type FetchTransport = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

const DASHBOARD_KEYS = [
  "total_consultations",
  "booked_appointments",
  "conversion_rate",
] as const;

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

const metricsFromResponse = (value: unknown): DashboardMetrics => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new DashboardApiError();
  }

  const keys = Object.keys(value);
  if (
    keys.length !== DASHBOARD_KEYS.length ||
    !DASHBOARD_KEYS.every((key) => Object.hasOwn(value, key))
  ) {
    throw new DashboardApiError();
  }

  const metrics = value as Record<string, unknown>;
  const totalConsultations = metrics.total_consultations;
  const bookedAppointments = metrics.booked_appointments;
  const conversionRate = metrics.conversion_rate;

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

  return {
    total_consultations: totalConsultations,
    booked_appointments: bookedAppointments,
    conversion_rate: conversionRate,
  };
};

export const createDashboardApi = (
  transport: FetchTransport = globalThis.fetch.bind(globalThis),
) => ({
  async getMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await transport(apiUrl("/api/v1/dashboard"), {
        method: "GET",
      });
      if (response.status !== 200) throw new DashboardApiError();
      return metricsFromResponse(await response.json());
    } catch {
      throw new DashboardApiError();
    }
  },
});

export const dashboardApi = createDashboardApi();
