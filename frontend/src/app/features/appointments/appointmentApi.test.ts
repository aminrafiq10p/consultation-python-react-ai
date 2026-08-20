import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppointmentApiError, createAppointmentApi } from "./appointmentApi";
import type { AppointmentListResponse } from "./appointmentTypes";

const appointmentId = "77777777-7777-4777-8777-777777777777";
const consultationId = "4a7f9139-19d1-4734-8bf5-dcd234d99d31";
const recommendationId = "44444444-4444-4444-8444-444444444444";
const item = {
  id: appointmentId,
  consultation_id: consultationId,
  patient_name: "Amina Khan",
  recommendation: { id: recommendationId, treatment: "Physiotherapy" },
  scheduled_at: "2026-08-20T14:30:00Z",
  location: "Downtown Clinic",
  created_at: "2026-08-17T12:00:00+00:00",
};
const responseBody: AppointmentListResponse = { items: [item] };

const jsonResponse = (body: unknown, status = 200) =>
  new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

beforeEach(() => vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test/") );
afterEach(() => vi.unstubAllEnvs());

describe("appointmentApi listAppointments", () => {
  it("sends one GET to the configured endpoint without a body", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(responseBody));

    await expect(createAppointmentApi(transport).listAppointments()).resolves.toEqual(
      responseBody,
    );

    expect(transport).toHaveBeenCalledTimes(1);
    expect(transport).toHaveBeenCalledWith("https://api.example.test/api/v1/appointments", {
      method: "GET",
    });
  });

  it("accepts a valid empty list", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [] }));
    await expect(createAppointmentApi(transport).listAppointments()).resolves.toEqual({
      items: [],
    });
  });

  it.each([
    ["top-level extra key", { items: [], extra: true }],
    ["items not array", { items: {} }],
    ["item extra key", { items: [{ ...item, status: "BOOKED" }] }],
    ["invalid appointment UUID", { items: [{ ...item, id: "bad" }] }],
    ["invalid consultation UUID", { items: [{ ...item, consultation_id: "bad" }] }],
    ["blank patient name", { items: [{ ...item, patient_name: " " }] }],
    ["invalid recommendation shape", { items: [{ ...item, recommendation: { id: recommendationId } }] }],
    ["invalid recommendation UUID", { items: [{ ...item, recommendation: { ...item.recommendation, id: "bad" } }] }],
    ["blank treatment", { items: [{ ...item, recommendation: { ...item.recommendation, treatment: " " } }] }],
    ["timestamp without offset", { items: [{ ...item, scheduled_at: "2026-08-20T14:30:00" }] }],
    ["invalid timestamp date", { items: [{ ...item, scheduled_at: "2026-02-30T14:30:00Z" }] }],
    ["blank location", { items: [{ ...item, location: " " }] }],
    ["invalid created timestamp", { items: [{ ...item, created_at: "2026-08-17" }] }],
    ["duplicate appointment projection", { items: [item, item] }],
  ])("rejects %s", async (_name, body) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body));
    await expect(createAppointmentApi(transport).listAppointments()).rejects.toEqual(
      new AppointmentApiError(),
    );
    expect(transport).toHaveBeenCalledTimes(1);
  });

  it.each([201, 204, 400, 404, 500])("maps HTTP %i safely without retrying", async (status) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ error: "database detail" }, status));
    const request = createAppointmentApi(transport).listAppointments();
    await expect(request).rejects.toEqual(new AppointmentApiError());
    await expect(request).rejects.not.toThrow("database detail");
    expect(transport).toHaveBeenCalledTimes(1);
  });

  it("maps malformed JSON and network/transport failures safely", async () => {
    const malformed = vi.fn().mockResolvedValue(new Response("not-json", { status: 200 }));
    await expect(createAppointmentApi(malformed).listAppointments()).rejects.toEqual(
      new AppointmentApiError(),
    );

    const network = vi.fn().mockRejectedValue(new Error("private transport detail"));
    const request = createAppointmentApi(network).listAppointments();
    await expect(request).rejects.toEqual(new AppointmentApiError());
    await expect(request).rejects.not.toThrow("private transport detail");
    expect(network).toHaveBeenCalledTimes(1);
  });
});
