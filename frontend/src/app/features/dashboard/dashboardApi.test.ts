import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardApiError, createDashboardApi } from "./dashboardApi";

const populatedMetrics = {
  total_consultations: 4,
  booked_appointments: 1,
  conversion_rate: 25,
};

const jsonResponse = (body: unknown, status = 200) =>
  new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const responseWithJsonValue = (body: unknown): Response =>
  ({ status: 200, json: vi.fn().mockResolvedValue(body) }) as unknown as Response;

beforeEach(() => {
  vi.stubEnv("VITE_API_BASE_URL", "");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("dashboardApi", () => {
  it("makes exactly one bodyless GET to the dashboard endpoint", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(populatedMetrics));

    await expect(createDashboardApi(transport).getMetrics()).resolves.toEqual(
      populatedMetrics,
    );

    expect(transport).toHaveBeenCalledTimes(1);
    expect(transport).toHaveBeenCalledWith("/api/v1/dashboard", {
      method: "GET",
    });
    const [url, init] = transport.mock.calls[0];
    expect(String(url)).not.toContain("?");
    expect(init).not.toHaveProperty("body");
  });

  it("uses the configured browser-safe API base URL", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://localhost:5000/");
    const transport = vi.fn().mockResolvedValue(jsonResponse(populatedMetrics));

    await createDashboardApi(transport).getMetrics();

    expect(transport).toHaveBeenCalledWith(
      "http://localhost:5000/api/v1/dashboard",
      { method: "GET" },
    );
  });

  it("accepts the exact populated response without changing conversion", async () => {
    const metrics = { ...populatedMetrics, conversion_rate: 24.99 };
    const transport = vi.fn().mockResolvedValue(jsonResponse(metrics));

    const result = await createDashboardApi(transport).getMetrics();

    expect(result).toEqual(metrics);
    expect(result.conversion_rate).toBe(24.99);
  });

  it("accepts the all-zero response", async () => {
    const metrics = {
      total_consultations: 0,
      booked_appointments: 0,
      conversion_rate: 0,
    };
    const transport = vi.fn().mockResolvedValue(jsonResponse(metrics));

    await expect(createDashboardApi(transport).getMetrics()).resolves.toEqual(metrics);
  });

  it.each([
    ["missing total", { booked_appointments: 1, conversion_rate: 25 }],
    ["missing booked", { total_consultations: 4, conversion_rate: 25 }],
    ["missing conversion", { total_consultations: 4, booked_appointments: 1 }],
    ["extra field", { ...populatedMetrics, extra: true }],
    ["null", null],
    ["array", [populatedMetrics]],
    ["primitive", "metrics"],
  ])("rejects an invalid response shape: %s", async (_name, body) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body));

    await expect(createDashboardApi(transport).getMetrics()).rejects.toEqual(
      new DashboardApiError(),
    );
  });

  it.each([
    ["negative total", { ...populatedMetrics, total_consultations: -1 }],
    ["fractional total", { ...populatedMetrics, total_consultations: 4.5 }],
    ["string total", { ...populatedMetrics, total_consultations: "4" }],
    ["unsafe total", { ...populatedMetrics, total_consultations: 2 ** 53 }],
    ["negative booked", { ...populatedMetrics, booked_appointments: -1 }],
    ["fractional booked", { ...populatedMetrics, booked_appointments: 1.5 }],
    ["string booked", { ...populatedMetrics, booked_appointments: "1" }],
    ["unsafe booked", { ...populatedMetrics, booked_appointments: 2 ** 53 }],
    ["booked above total", { ...populatedMetrics, booked_appointments: 5 }],
    [
      "zero total with bookings",
      { total_consultations: 0, booked_appointments: 1, conversion_rate: 0 },
    ],
    [
      "zero total with conversion",
      { total_consultations: 0, booked_appointments: 0, conversion_rate: 1 },
    ],
    ["negative conversion", { ...populatedMetrics, conversion_rate: -0.01 }],
    ["conversion above 100", { ...populatedMetrics, conversion_rate: 100.01 }],
    ["string conversion", { ...populatedMetrics, conversion_rate: "25" }],
  ])("rejects invalid metric values: %s", async (_name, body) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body));

    await expect(createDashboardApi(transport).getMetrics()).rejects.toEqual(
      new DashboardApiError(),
    );
  });

  it.each([
    ["NaN total", { ...populatedMetrics, total_consultations: Number.NaN }],
    ["infinite total", { ...populatedMetrics, total_consultations: Infinity }],
    ["NaN booked", { ...populatedMetrics, booked_appointments: Number.NaN }],
    ["infinite booked", { ...populatedMetrics, booked_appointments: Infinity }],
    ["NaN conversion", { ...populatedMetrics, conversion_rate: Number.NaN }],
    ["infinite conversion", { ...populatedMetrics, conversion_rate: Infinity }],
  ])("rejects non-finite runtime values: %s", async (_name, body) => {
    const transport = vi.fn().mockResolvedValue(responseWithJsonValue(body));

    await expect(createDashboardApi(transport).getMetrics()).rejects.toEqual(
      new DashboardApiError(),
    );
  });

  it("maps malformed JSON to the safe retrieval error", async () => {
    const transport = vi
      .fn()
      .mockResolvedValue(new Response("not-json", { status: 200 }));

    await expect(createDashboardApi(transport).getMetrics()).rejects.toEqual(
      new DashboardApiError(),
    );
  });

  it.each([201, 204, 400, 404, 500])(
    "maps HTTP %i to the safe retrieval error without retrying",
    async (status) => {
      const transport = vi
        .fn()
        .mockResolvedValue(jsonResponse({ error: "sensitive detail" }, status));

      const request = createDashboardApi(transport).getMetrics();

      await expect(request).rejects.toEqual(new DashboardApiError());
      await expect(request).rejects.not.toThrow("sensitive detail");
      expect(transport).toHaveBeenCalledTimes(1);
    },
  );

  it("maps a network rejection safely without retrying", async () => {
    const transport = vi
      .fn()
      .mockRejectedValue(new Error("private network failure detail"));

    const request = createDashboardApi(transport).getMetrics();

    await expect(request).rejects.toEqual(new DashboardApiError());
    await expect(request).rejects.not.toThrow("private network failure detail");
    expect(transport).toHaveBeenCalledTimes(1);
  });
});
