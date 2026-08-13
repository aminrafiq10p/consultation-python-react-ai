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

const userMessage = {
  id: "11111111-1111-4111-8111-111111111111",
  consultation_id: record.id,
  role: "USER" as const,
  content: "What should I do next?",
  structured_payload: null,
  created_at: "2026-08-13T10:00:00+00:00",
};

const assistantMessage = {
  id: "22222222-2222-4222-8222-222222222222",
  consultation_id: record.id,
  role: "ASSISTANT" as const,
  content: "Here are some next steps.",
  structured_payload: {
    urgent: false,
    score: 2,
    note: null,
    topics: ["pain", 2, true, null],
  },
  created_at: "2026-08-13T10:00:01Z",
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

  it("requests and validates conversation history", async () => {
    const transport = vi
      .fn()
      .mockResolvedValue(jsonResponse({ items: [userMessage, assistantMessage] }));

    await expect(createConsultationApi(transport).messages(record.id)).resolves.toEqual({
      items: [userMessage, assistantMessage],
    });
    expect(transport).toHaveBeenCalledWith(
      `/api/v1/consultations/${record.id}/messages`,
      { method: "GET" },
    );
  });

  it("supports an empty conversation history", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [] }));

    await expect(createConsultationApi(transport).messages(record.id)).resolves.toEqual({
      items: [],
    });
  });

  it.each([userMessage, assistantMessage])(
    "accepts persisted $role messages",
    async (message) => {
      const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [message] }));

      await expect(createConsultationApi(transport).messages(record.id)).resolves.toEqual({
        items: [message],
      });
    },
  );

  it("accepts text-only assistant messages", async () => {
    const textOnly = { ...assistantMessage, structured_payload: null };
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [textOnly] }));

    await expect(createConsultationApi(transport).messages(record.id)).resolves.toEqual({
      items: [textOnly],
    });
  });

  it.each([
    ["invalid role", { ...assistantMessage, role: "SYSTEM" }],
    [
      "nested structured object",
      { ...assistantMessage, structured_payload: { unsafe: { nested: true } } },
    ],
    [
      "nested structured array",
      { ...assistantMessage, structured_payload: { unsafe: [["nested"]] } },
    ],
    ["user structured data", { ...userMessage, structured_payload: { unsafe: true } }],
    ["invalid identifier", { ...assistantMessage, id: "not-a-uuid" }],
    ["blank content", { ...assistantMessage, content: "   " }],
    ["invalid timestamp", { ...assistantMessage, created_at: "yesterday" }],
  ])("rejects a message with %s safely", async (_name, message) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [message] }));

    await expect(createConsultationApi(transport).messages(record.id)).rejects.toEqual(
      new ConsultationApiError("retrieval"),
    );
  });

  it("submits content and validates the persisted exchange", async () => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse({
        user_message: userMessage,
        assistant_message: assistantMessage,
      }),
    );

    await expect(
      createConsultationApi(transport).submitMessage(record.id, "Question"),
    ).resolves.toEqual({
      user_message: userMessage,
      assistant_message: assistantMessage,
    });
    expect(transport).toHaveBeenCalledWith(
      `/api/v1/consultations/${record.id}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: "Question" }),
      },
    );
  });

  it.each(["messages", "submitMessage"] as const)(
    "maps %s missing consultations to not-found",
    async (method) => {
      const transport = vi.fn().mockResolvedValue(jsonResponse({ error: "safe" }, 404));
      const api = createConsultationApi(transport);
      const request =
        method === "messages"
          ? api.messages(record.id)
          : api.submitMessage(record.id, "Question");

      await expect(request).rejects.toMatchObject({ kind: "not-found" });
    },
  );

  it.each(["messages", "submitMessage"] as const)(
    "maps %s invalid requests to validation",
    async (method) => {
      const transport = vi.fn().mockResolvedValue(jsonResponse({ error: "safe" }, 400));
      const api = createConsultationApi(transport);
      const request =
        method === "messages"
          ? api.messages(record.id)
          : api.submitMessage(record.id, "Question");

      await expect(request).rejects.toMatchObject({ kind: "validation" });
    },
  );

  it("maps a valid 503 recovery to a persisted-user AI failure", async () => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          error: "Assistant response is temporarily unavailable",
          code: "AI_GENERATION_FAILED",
          user_message: userMessage,
        },
        503,
      ),
    );

    await expect(
      createConsultationApi(transport).submitMessage(record.id, "Question"),
    ).rejects.toMatchObject({
      kind: "ai-generation",
      persistedUserMessage: userMessage,
    });
  });

  it.each([
    ["missing recovery message", undefined],
    ["assistant recovery message", assistantMessage],
    ["malformed recovery message", { ...userMessage, role: "SYSTEM" }],
    ["nested recovery payload", { ...userMessage, structured_payload: { bad: {} } }],
  ])("maps a 503 with %s to generic submission failure", async (_name, recovery) => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          error: "provider secret detail",
          code: "AI_GENERATION_FAILED",
          user_message: recovery,
        },
        503,
      ),
    );

    const request = createConsultationApi(transport).submitMessage(record.id, "Question");
    await expect(request).rejects.toEqual(new ConsultationApiError("submission"));
    await expect(request).rejects.not.toThrow("provider secret detail");
  });

  it("requires the approved recovery code", async () => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse(
        { code: "UPSTREAM_FAILED", user_message: userMessage },
        503,
      ),
    );

    await expect(
      createConsultationApi(transport).submitMessage(record.id, "Question"),
    ).rejects.toEqual(new ConsultationApiError("submission"));
  });

  it.each([
    ["server response", vi.fn().mockResolvedValue(jsonResponse({ error: "raw detail" }, 500))],
    ["network rejection", vi.fn().mockRejectedValue(new Error("provider raw detail"))],
  ])("maps generic submission %s safely", async (_name, transport) => {
    const request = createConsultationApi(transport).submitMessage(record.id, "Question");

    await expect(request).rejects.toEqual(new ConsultationApiError("submission"));
    await expect(request).rejects.not.toThrow(/raw detail/);
  });

  it("rejects malformed successful exchanges as submission failures", async () => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse({
        user_message: userMessage,
        assistant_message: { ...assistantMessage, role: "USER" },
      }),
    );

    await expect(
      createConsultationApi(transport).submitMessage(record.id, "Question"),
    ).rejects.toEqual(new ConsultationApiError("submission"));
  });
});
