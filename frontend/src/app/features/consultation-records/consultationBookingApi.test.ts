import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConsultationApiError, createConsultationApi } from "./consultationApi";
import type { AppointmentBookingRequest } from "./consultationTypes";

const consultationId = "4a7f9139-19d1-4734-8bf5-dcd234d99d31";
const recommendationId = "44444444-4444-4444-8444-444444444444";
const request: AppointmentBookingRequest = {
  recommendation_id: recommendationId,
  scheduled_at: "2026-08-20T19:30:00+05:00",
  location: "Downtown Clinic",
};
const appointment = {
  id: "77777777-7777-4777-8777-777777777777",
  consultation_id: consultationId,
  recommendation: {
    id: recommendationId,
    treatment: "Physical therapy assessment",
  },
  scheduled_at: "2026-08-20T14:30:00Z",
  location: "Downtown Clinic",
  created_at: "2026-08-17T12:00:00+00:00",
};

const jsonResponse = (body: unknown, status = 201) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

beforeEach(() => vi.stubEnv("VITE_API_BASE_URL", ""));
afterEach(() => vi.unstubAllEnvs());

describe("consultationApi appointment booking", () => {
  it("sends exactly one POST to the approved path with only the approved body", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(appointment));

    await expect(
      createConsultationApi(transport).bookAppointment(consultationId, request),
    ).resolves.toEqual(appointment);

    expect(transport).toHaveBeenCalledTimes(1);
    expect(transport).toHaveBeenCalledWith(
      `/api/v1/consultations/${consultationId}/appointments`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recommendation_id: recommendationId,
          scheduled_at: request.scheduled_at,
          location: request.location,
        }),
      },
    );
  });

  it.each([
    ["appointment UUID", { ...appointment, id: "not-a-uuid" }],
    ["consultation UUID", { ...appointment, consultation_id: "not-a-uuid" }],
    [
      "consultation linkage",
      { ...appointment, consultation_id: "88888888-8888-4888-8888-888888888888" },
    ],
    [
      "recommendation UUID",
      { ...appointment, recommendation: { ...appointment.recommendation, id: "bad" } },
    ],
    [
      "recommendation linkage",
      {
        ...appointment,
        recommendation: {
          ...appointment.recommendation,
          id: "55555555-5555-4555-8555-555555555555",
        },
      },
    ],
    [
      "nonblank treatment",
      { ...appointment, recommendation: { ...appointment.recommendation, treatment: " " } },
    ],
    ["explicit-offset scheduled_at", { ...appointment, scheduled_at: "2026-08-20T14:30:00" }],
    ["valid scheduled_at calendar date", { ...appointment, scheduled_at: "2026-02-30T14:30:00Z" }],
    ["explicit-offset created_at", { ...appointment, created_at: "2026-08-17" }],
    ["valid created_at timestamp", { ...appointment, created_at: "2026-08-17T25:00:00Z" }],
    ["nonblank location", { ...appointment, location: "   " }],
    ["normalized location", { ...appointment, location: " Downtown Clinic " }],
    ["location length", { ...appointment, location: "a".repeat(201) }],
    ["nested recommendation", { ...appointment, recommendation: null }],
    ["response object", null],
  ])("rejects malformed success: %s", async (_name, body) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body));

    await expect(
      createConsultationApi(transport).bookAppointment(consultationId, request),
    ).rejects.toEqual(new ConsultationApiError("booking-submission"));
  });

  it("counts Unicode code points when validating the normalized location", async () => {
    const valid = { ...appointment, location: "😀".repeat(200) };
    const transport = vi.fn().mockResolvedValue(jsonResponse(valid));

    await expect(
      createConsultationApi(transport).bookAppointment(consultationId, request),
    ).resolves.toEqual(valid);
  });

  it("requires exact 201 success", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(appointment, 200));

    await expect(
      createConsultationApi(transport).bookAppointment(consultationId, request),
    ).rejects.toEqual(new ConsultationApiError("booking-submission"));
  });

  it.each([
    [400, { error: "Invalid request" }, "booking-validation"],
    [404, { error: "Consultation not found" }, "booking-consultation-not-found"],
    [404, { error: "Recommendation not found" }, "booking-recommendation-not-found"],
    [
      409,
      { error: "Safe message", code: "RECOMMENDATION_NOT_BOOKABLE" },
      "recommendation-not-bookable",
    ],
    [
      409,
      { error: "Safe message", code: "CONSULTATION_NOT_BOOKABLE" },
      "consultation-not-bookable",
    ],
    [
      409,
      { error: "Safe message", code: "APPOINTMENT_ALREADY_EXISTS" },
      "appointment-already-exists",
    ],
  ] as const)("maps exact booking error %#", async (status, body, kind) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body, status));

    await expect(
      createConsultationApi(transport).bookAppointment(consultationId, request),
    ).rejects.toMatchObject({ kind });
  });

  it.each([
    [500, { error: "database detail" }],
    [400, { error: "different validation detail" }],
    [404, { error: "unknown resource" }],
    [409, { error: "safe", code: "UNKNOWN_CONFLICT" }],
    [409, { code: "APPOINTMENT_ALREADY_EXISTS" }],
  ])("maps unexpected status/envelope %# safely", async (status, body) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body, status));
    const result = createConsultationApi(transport).bookAppointment(
      consultationId,
      request,
    );

    await expect(result).rejects.toEqual(
      new ConsultationApiError("booking-submission"),
    );
    await expect(result).rejects.not.toThrow(/database detail|different validation detail/);
  });

  it("maps malformed JSON safely", async () => {
    const transport = vi.fn().mockResolvedValue(new Response("not-json", { status: 201 }));

    await expect(
      createConsultationApi(transport).bookAppointment(consultationId, request),
    ).rejects.toEqual(new ConsultationApiError("booking-submission"));
  });

  it("does not retry an ambiguous network failure", async () => {
    const transport = vi.fn().mockRejectedValue(new Error("response lost after commit"));
    const result = createConsultationApi(transport).bookAppointment(
      consultationId,
      request,
    );

    await expect(result).rejects.toEqual(
      new ConsultationApiError("booking-submission"),
    );
    await expect(result).rejects.not.toThrow("response lost after commit");
    expect(transport).toHaveBeenCalledTimes(1);
  });
});
