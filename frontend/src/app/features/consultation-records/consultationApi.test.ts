import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

const summary = {
  id: "33333333-3333-4333-8333-333333333333",
  consultation_id: record.id,
  patient_summary: "The patient reports persistent knee pain.",
  recommended_treatments: [
    {
      id: "44444444-4444-4444-8444-444444444444",
      treatment: "Physical therapy assessment",
      position: 1,
    },
    {
      id: "55555555-5555-4555-8555-555555555555",
      treatment: "Orthopedic consultation",
      position: 2,
    },
  ],
  recommendation_rationale: "These options support assessment and mobility.",
  created_at: "2026-08-17T10:00:00+00:00",
};

const restartedRecord = {
  ...record,
  id: "66666666-6666-4666-8666-666666666666",
  recommended_procedure: "",
};

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

beforeEach(() => {
  vi.stubEnv("VITE_API_BASE_URL", "");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("consultationApi", () => {
  it("prepends the configured browser-safe API base URL", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://localhost:5000/");
    const transport = vi.fn().mockResolvedValue(jsonResponse({ items: [] }));

    await createConsultationApi(transport).list();

    expect(transport).toHaveBeenCalledWith(
      "http://localhost:5000/api/v1/consultations",
      { method: "GET" },
    );
  });

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

  it("retrieves and validates a persisted summary from the exact path", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(summary));

    await expect(createConsultationApi(transport).summary(record.id)).resolves.toEqual(
      summary,
    );
    expect(transport).toHaveBeenCalledWith(
      `/api/v1/consultations/${record.id}/summary`,
      { method: "GET" },
    );
  });

  it.each([200, 201])(
    "accepts a validated summary generation response with status %i",
    async (status) => {
      const transport = vi.fn().mockResolvedValue(jsonResponse(summary, status));

      await expect(
        createConsultationApi(transport).generateSummary(record.id),
      ).resolves.toEqual(summary);
      expect(transport).toHaveBeenCalledWith(
        `/api/v1/consultations/${record.id}/summary`,
        { method: "POST" },
      );
      expect(transport.mock.calls[0]?.[1]).not.toHaveProperty("body");
    },
  );

  it("accepts a null recommendation rationale", async () => {
    const withoutRationale = { ...summary, recommendation_rationale: null };
    const transport = vi.fn().mockResolvedValue(jsonResponse(withoutRationale));

    await expect(createConsultationApi(transport).summary(record.id)).resolves.toEqual(
      withoutRationale,
    );
  });

  it.each([
    ["summary identifier", { ...summary, id: "not-an-id" }],
    ["consultation identifier", { ...summary, consultation_id: "not-an-id" }],
    [
      "consultation linkage",
      { ...summary, consultation_id: "77777777-7777-4777-8777-777777777777" },
    ],
    ["blank patient summary", { ...summary, patient_summary: "   " }],
    ["empty recommendations", { ...summary, recommended_treatments: [] }],
    [
      "recommendation identifier",
      {
        ...summary,
        recommended_treatments: [
          { ...summary.recommended_treatments[0], id: "not-an-id" },
        ],
      },
    ],
    [
      "blank treatment",
      {
        ...summary,
        recommended_treatments: [
          { ...summary.recommended_treatments[0], treatment: "  " },
        ],
      },
    ],
    [
      "non-positive position",
      {
        ...summary,
        recommended_treatments: [
          { ...summary.recommended_treatments[0], position: 0 },
        ],
      },
    ],
    [
      "non-integer position",
      {
        ...summary,
        recommended_treatments: [
          { ...summary.recommended_treatments[0], position: 1.5 },
        ],
      },
    ],
    [
      "duplicate recommendation identifiers",
      {
        ...summary,
        recommended_treatments: [
          summary.recommended_treatments[0],
          { ...summary.recommended_treatments[1], id: summary.recommended_treatments[0].id },
        ],
      },
    ],
    [
      "duplicate positions",
      {
        ...summary,
        recommended_treatments: [
          summary.recommended_treatments[0],
          { ...summary.recommended_treatments[1], position: 1 },
        ],
      },
    ],
    [
      "descending positions",
      {
        ...summary,
        recommended_treatments: [
          { ...summary.recommended_treatments[0], position: 2 },
          { ...summary.recommended_treatments[1], position: 1 },
        ],
      },
    ],
    ["blank rationale", { ...summary, recommendation_rationale: "  " }],
    ["invalid timestamp", { ...summary, created_at: "today" }],
  ])("rejects a summary with %s", async (_name, malformedSummary) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(malformedSummary));

    await expect(createConsultationApi(transport).summary(record.id)).rejects.toEqual(
      new ConsultationApiError("retrieval"),
    );
  });

  it.each([
    ["summary", 409, "SUMMARY_NOT_AVAILABLE", "summary-not-available"],
    ["generateSummary", 409, "SUMMARY_NOT_ELIGIBLE", "summary-not-eligible"],
    ["generateSummary", 503, "SUMMARY_GENERATION_FAILED", "summary-generation"],
    ["restartConsultation", 409, "CONSULTATION_NOT_RESTARTABLE", "not-restartable"],
  ] as const)(
    "maps $method status $status and $code exactly",
    async (method, status, code, kind) => {
      const transport = vi
        .fn()
        .mockResolvedValue(jsonResponse({ error: "Safe message", code }, status));
      const api = createConsultationApi(transport);

      await expect(api[method](record.id)).rejects.toMatchObject({ kind });
    },
  );

  it.each([
    [409, { error: "Safe message", code: "WRONG_CODE" }],
    [409, { code: "SUMMARY_NOT_AVAILABLE" }],
    [503, { error: "", code: "SUMMARY_GENERATION_FAILED" }],
    [409, "not an error envelope"],
  ])("maps malformed or mismatched coded error %# safely", async (status, body) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(body, status));
    const request =
      status === 503
        ? createConsultationApi(transport).generateSummary(record.id)
        : createConsultationApi(transport).summary(record.id);

    await expect(request).rejects.toEqual(
      new ConsultationApiError(status === 503 ? "submission" : "retrieval"),
    );
  });

  it("creates a restart with no body and validates the returned consultation", async () => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(restartedRecord, 201));

    await expect(
      createConsultationApi(transport).restartConsultation(record.id),
    ).resolves.toEqual(restartedRecord);
    expect(transport).toHaveBeenCalledWith(
      `/api/v1/consultations/${record.id}/restart`,
      { method: "POST" },
    );
    expect(transport.mock.calls[0]?.[1]).not.toHaveProperty("body");
  });

  it.each([
    { ...restartedRecord, id: "invalid" },
    { ...restartedRecord, status: "UNKNOWN" },
    { ...restartedRecord, patient_name: null },
  ])("rejects malformed restart response %#", async (malformedRecord) => {
    const transport = vi.fn().mockResolvedValue(jsonResponse(malformedRecord, 201));

    await expect(
      createConsultationApi(transport).restartConsultation(record.id),
    ).rejects.toEqual(new ConsultationApiError("submission"));
  });

  it("maps the exact closed-conversation submission error", async () => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse(
        {
          error: "Consultation conversation is closed",
          code: "CONSULTATION_CONVERSATION_CLOSED",
        },
        409,
      ),
    );

    await expect(
      createConsultationApi(transport).submitMessage(record.id, "Question"),
    ).rejects.toMatchObject({ kind: "conversation-closed" });
  });

  it("requires the exact closed-conversation status/code envelope", async () => {
    const transport = vi.fn().mockResolvedValue(
      jsonResponse(
        { error: "raw detail", code: "CONSULTATION_CONVERSATION_CLOSED" },
        503,
      ),
    );

    const request = createConsultationApi(transport).submitMessage(
      record.id,
      "Question",
    );
    await expect(request).rejects.toEqual(new ConsultationApiError("submission"));
    await expect(request).rejects.not.toThrow("raw detail");
  });

  it.each(["summary", "generateSummary", "restartConsultation"] as const)(
    "maps %s missing consultations to not-found",
    async (method) => {
      const transport = vi.fn().mockResolvedValue(jsonResponse({ error: "Safe" }, 404));

      await expect(
        createConsultationApi(transport)[method](record.id),
      ).rejects.toMatchObject({ kind: "not-found" });
    },
  );

  it.each([
    ["summary", "retrieval"],
    ["generateSummary", "submission"],
    ["restartConsultation", "submission"],
  ] as const)("maps malformed %s JSON to a safe %s failure", async (method, kind) => {
    const status = method === "restartConsultation" ? 201 : 200;
    const transport = vi.fn().mockResolvedValue(new Response("not-json", { status }));

    await expect(
      createConsultationApi(transport)[method](record.id),
    ).rejects.toEqual(new ConsultationApiError(kind));
  });

  it.each([
    ["summary", "retrieval"],
    ["generateSummary", "submission"],
    ["restartConsultation", "submission"],
  ] as const)("maps generic %s server errors safely", async (method, kind) => {
    const transport = vi
      .fn()
      .mockResolvedValue(jsonResponse({ error: "SQL constraint detail" }, 500));
    const request = createConsultationApi(transport)[method](record.id);

    await expect(request).rejects.toEqual(new ConsultationApiError(kind));
    await expect(request).rejects.not.toThrow("SQL constraint detail");
  });

  it.each(["summary", "generateSummary", "restartConsultation"] as const)(
    "maps %s transport failures without exposing raw details",
    async (method) => {
      const transport = vi.fn().mockRejectedValue(new Error("SQL/provider secret"));
      const request = createConsultationApi(transport)[method](record.id);

      await expect(request).rejects.not.toThrow(/SQL|provider secret/);
    },
  );
});
