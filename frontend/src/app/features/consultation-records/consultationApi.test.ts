import { describe, expect, it, vi } from "vitest";

import {
  ConsultationApiError,
  createConsultationApi,
} from "./consultationApi";

const record = {
  id: "4a7f9139-19d1-4734-8bf5-dcd234d99d31",
  patient_name: "Amina Khan",
  primary_concern: "Persistent knee pain",
  recommended_procedure: "Orthopedic consultation",
  status: "PENDING" as const,
};

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("consultationApi", () => {
  it.each([
    [{}, "/api/v1/consultations"],
    [{ search: "  knee pain  " }, "/api/v1/consultations?search=knee+pain"],
    [{ status: "BOOKED" as const }, "/api/v1/consultations?status=BOOKED"],
    [
      { search: "knee", status: "COMPLETED" as const },
      "/api/v1/consultations?search=knee&status=COMPLETED",
    ],
  ])("constructs the list request for %j", async (criteria, expectedUrl) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [record] }));

    await expect(createConsultationApi(transport).list(criteria)).resolves.toEqual({
      items: [record],
    });
    expect(transport).toHaveBeenCalledWith(expectedUrl, { method: "GET" });
  });

  it("omits blank search and an unselected all-status criterion", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [] }));

    await createConsultationApi(transport).list({ search: "   " });

    expect(transport).toHaveBeenCalledWith("/api/v1/consultations", {
      method: "GET",
    });
  });

  it("requests and maps consultation detail", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(record));

    await expect(
      createConsultationApi(transport).detail(record.id),
    ).resolves.toEqual(record);
    expect(transport).toHaveBeenCalledWith(
      `/api/v1/consultations/${record.id}`,
      { method: "GET" },
    );
  });

  it("translates detail 404 into a not-found outcome", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ error: "Not found" }, 404));

    await expect(createConsultationApi(transport).detail("missing")).rejects.toMatchObject({
      kind: "not-found",
    });
  });

  it.each([
    ["network failure", vi.fn().mockRejectedValue(new Error("connection details"))],
    ["server failure", vi.fn().mockResolvedValue(jsonResponse({ error: "internal" }, 500))],
    ["invalid response", vi.fn().mockResolvedValue(jsonResponse({ items: [{}] }))],
  ])("translates %s into a safe retrieval outcome", async (_name, transport) => {
    const request = createConsultationApi(transport).list();

    await expect(request).rejects.toEqual(new ConsultationApiError("retrieval"));
    await expect(request).rejects.not.toThrow("connection details");
  });
});
