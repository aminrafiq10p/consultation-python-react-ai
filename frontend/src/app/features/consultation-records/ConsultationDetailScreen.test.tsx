import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ConsultationApiError } from "./consultationApi";
import {
  ConsultationDetailScreen,
  type ConsultationDetailService,
} from "./ConsultationDetailScreen";
import type { ConsultationMessage, ConsultationRecord } from "./consultationTypes";

const record: ConsultationRecord = {
  id: "consultation-42",
  patient_name: "Amina Khan",
  primary_concern: "Persistent knee pain",
  recommended_procedure: "Orthopedic consultation",
  status: "PENDING",
};

const userMessage: ConsultationMessage = {
  id: "11111111-1111-4111-8111-111111111111",
  consultation_id: record.id,
  role: "USER",
  content: "My first question",
  structured_payload: null,
  created_at: "2026-08-13T10:00:00Z",
};

const assistantMessage: ConsultationMessage = {
  id: "22222222-2222-4222-8222-222222222222",
  consultation_id: record.id,
  role: "ASSISTANT",
  content: "My first answer",
  structured_payload: null,
  created_at: "2026-08-13T10:00:01Z",
};

const serviceFor = (
  overrides: Partial<ConsultationDetailService> = {},
): ConsultationDetailService => ({
  detail: vi.fn().mockResolvedValue(record),
  messages: vi.fn().mockResolvedValue({ items: [] }),
  submitMessage: vi.fn(),
  ...overrides,
});

const renderScreen = (
  service: ConsultationDetailService,
  path = `/consultations/${record.id}`,
) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/consultations/:consultationId"
          element={<ConsultationDetailScreen service={service} />}
        />
      </Routes>
    </MemoryRouter>,
  );

describe("ConsultationDetailScreen", () => {
  it("preserves the detail fields and loads conversation for the route identifier", async () => {
    const detail = vi.fn().mockResolvedValue(record);
    const messages = vi.fn().mockResolvedValue({ items: [] });

    renderScreen(serviceFor({ detail, messages }));

    expect(await screen.findByText(record.patient_name)).toBeInTheDocument();
    expect(screen.getByText(record.primary_concern)).toBeInTheDocument();
    expect(screen.getByText(record.recommended_procedure)).toBeInTheDocument();
    expect(screen.getByText(record.status)).toBeInTheDocument();
    expect(detail).toHaveBeenCalledWith(record.id);
    expect(messages).toHaveBeenCalledWith(record.id);
  });

  it("shows detail loading without starting conversation loading", () => {
    renderScreen(
      serviceFor({
        detail: vi.fn(() => new Promise<ConsultationRecord>(() => undefined)),
      }),
    );

    expect(screen.getByRole("status")).toHaveTextContent("Loading consultation details");
    expect(screen.queryByText("AI conversation")).not.toBeInTheDocument();
  });

  it("preserves consultation not-found and safe detail error behavior", async () => {
    const { unmount } = renderScreen(
      serviceFor({
        detail: vi.fn().mockRejectedValue(new ConsultationApiError("not-found")),
      }),
    );
    expect(await screen.findByText(/Consultation not found/)).toBeInTheDocument();
    unmount();

    renderScreen(
      serviceFor({ detail: vi.fn().mockRejectedValue(new Error("private detail")) }),
    );
    expect(
      await screen.findByText("Consultation details could not be loaded. Please try again."),
    ).toBeInTheDocument();
    expect(screen.queryByText("private detail")).not.toBeInTheDocument();
  });

  it("shows distinct conversation loading and empty states", async () => {
    let resolveHistory!: (history: { items: ConsultationMessage[] }) => void;
    const messages = vi.fn(
      () => new Promise<{ items: ConsultationMessage[] }>((resolve) => { resolveHistory = resolve; }),
    );
    renderScreen(serviceFor({ messages }));

    expect(await screen.findByText(/Loading conversation/)).toBeInTheDocument();
    resolveHistory({ items: [] });
    expect(
      await screen.findByText("No messages yet. Start the conversation below."),
    ).toBeInTheDocument();
  });

  it("renders persisted messages in exact service order with timestamps", async () => {
    renderScreen(
      serviceFor({ messages: vi.fn().mockResolvedValue({ items: [assistantMessage, userMessage] }) }),
    );

    const conversation = await screen.findByLabelText("Conversation messages");
    const content = within(conversation).getAllByText(/My first (answer|question)/);
    expect(content.map((element) => element.textContent)).toEqual([
      assistantMessage.content,
      userMessage.content,
    ]);
    expect(screen.getByText(assistantMessage.created_at)).toBeInTheDocument();
    expect(screen.getByText(userMessage.created_at)).toBeInTheDocument();
  });

  it("shows a recoverable conversation retrieval error and retries", async () => {
    const messages = vi
      .fn()
      .mockRejectedValueOnce(new Error("database secret"))
      .mockResolvedValueOnce({ items: [userMessage] });
    renderScreen(serviceFor({ messages }));

    expect(
      await screen.findByText("Conversation could not be loaded. Please try again."),
    ).toBeInTheDocument();
    expect(screen.queryByText("database secret")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText(userMessage.content)).toBeInTheDocument();
    expect(messages).toHaveBeenCalledTimes(2);
  });

  it("uses the existing missing-consultation state when history returns not-found", async () => {
    renderScreen(
      serviceFor({
        messages: vi.fn().mockRejectedValue(new ConsultationApiError("not-found")),
      }),
    );

    expect(await screen.findByText(/Consultation not found/)).toBeInTheDocument();
    expect(screen.queryByText(record.patient_name)).not.toBeInTheDocument();
  });

  it("validates blank and over-limit input without submitting", async () => {
    const submitMessage = vi.fn();
    renderScreen(serviceFor({ submitMessage }));
    const input = await screen.findByRole("textbox", { name: "Message" });

    await userEvent.type(input, "   ");
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(screen.getByText("Enter a message before sending.")).toBeInTheDocument();

    fireEvent.change(input, { target: { value: "x".repeat(4_001) } });
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(screen.getByText("Message must be 4,000 characters or fewer.")).toBeInTheDocument();
    expect(submitMessage).not.toHaveBeenCalled();
  });

  it("does not render a draft as persisted and prevents duplicate pending submissions", async () => {
    const submitMessage = vi.fn(
      () => new Promise<never>(() => undefined),
    );
    renderScreen(serviceFor({ submitMessage }));
    const input = await screen.findByRole("textbox", { name: "Message" });

    await userEvent.type(input, "Pending question");
    expect(screen.queryByLabelText("Conversation messages")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));

    expect(screen.getByRole("button", { name: "Sending…" })).toBeDisabled();
    expect(input).toBeDisabled();
    fireEvent.submit(input.closest("form")!);
    expect(submitMessage).toHaveBeenCalledTimes(1);
    expect(submitMessage).toHaveBeenCalledWith(record.id, "Pending question");
  });

  it("reconciles confirmed exchanges and supports a repeated message", async () => {
    const secondUser = { ...userMessage, id: "33333333-3333-4333-8333-333333333333", content: "Second question" };
    const secondAssistant = { ...assistantMessage, id: "44444444-4444-4444-8444-444444444444", content: "Second answer" };
    const submitMessage = vi
      .fn()
      .mockResolvedValueOnce({ user_message: userMessage, assistant_message: assistantMessage })
      .mockResolvedValueOnce({ user_message: secondUser, assistant_message: secondAssistant });
    renderScreen(serviceFor({ submitMessage }));
    const input = await screen.findByRole("textbox", { name: "Message" });

    await userEvent.type(input, `  ${userMessage.content}  `);
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(await screen.findByText(assistantMessage.content)).toBeInTheDocument();
    expect(input).toHaveValue("");

    await userEvent.type(input, secondUser.content);
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(await screen.findByText(secondAssistant.content)).toBeInTheDocument();
    expect(submitMessage).toHaveBeenNthCalledWith(1, record.id, userMessage.content);
    expect(submitMessage).toHaveBeenNthCalledWith(2, record.id, secondUser.content);
  });

  it("renders supported assistant payload safely while retaining plain text", async () => {
    const payloadMessage: ConsultationMessage = {
      ...assistantMessage,
      content: "<img src=x onerror=alert('secret')> Safe advice",
      structured_payload: {
        urgency: "routine",
        score: 2,
        reviewed: true,
        note: null,
        next_steps: ["rest", "book a clinician"],
      },
    };
    renderScreen(serviceFor({ messages: vi.fn().mockResolvedValue({ items: [payloadMessage] }) }));

    expect(await screen.findByText(payloadMessage.content)).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(screen.getByText("urgency")).toBeInTheDocument();
    expect(screen.getByText("routine")).toBeInTheDocument();
    expect(screen.getByText("rest")).toBeInTheDocument();
    expect(screen.getByText("book a clinician")).toBeInTheDocument();
  });

  it("ignores unsupported nested payload values while retaining assistant text", async () => {
    const malformed = {
      ...assistantMessage,
      structured_payload: { safe: "visible", nested: { provider: "private" } },
    } as unknown as ConsultationMessage;
    renderScreen(serviceFor({ messages: vi.fn().mockResolvedValue({ items: [malformed] }) }));

    expect(await screen.findByText(assistantMessage.content)).toBeInTheDocument();
    expect(screen.getByText("visible")).toBeInTheDocument();
    expect(screen.queryByText("provider")).not.toBeInTheDocument();
    expect(screen.queryByText("private")).not.toBeInTheDocument();
  });

  it("retains the confirmed user on AI failure, reloads history, and fabricates no assistant", async () => {
    let resolveReload!: (history: { items: ConsultationMessage[] }) => void;
    const messages = vi
      .fn()
      .mockResolvedValueOnce({ items: [] })
      .mockImplementationOnce(
        () => new Promise<{ items: ConsultationMessage[] }>((resolve) => { resolveReload = resolve; }),
      );
    const submitMessage = vi.fn().mockRejectedValue(
      new ConsultationApiError("ai-generation", userMessage),
    );
    renderScreen(serviceFor({ messages, submitMessage }));

    await userEvent.type(await screen.findByRole("textbox", { name: "Message" }), userMessage.content);
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));
    expect(await screen.findByText(userMessage.content)).toBeInTheDocument();
    expect(screen.getByText(/assistant is temporarily unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/fabricated/i)).not.toBeInTheDocument();
    expect(messages).toHaveBeenCalledTimes(2);

    resolveReload({ items: [userMessage] });
    await waitFor(() => expect(screen.getByRole("button", { name: "Send message" })).toBeEnabled());
  });

  it("reloads authoritative history after an ambiguous failure without exposing internals", async () => {
    const messages = vi
      .fn()
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [userMessage] });
    const submitMessage = vi.fn().mockRejectedValue(new Error("OPENAI_API_KEY stack trace"));
    renderScreen(serviceFor({ messages, submitMessage }));

    await userEvent.type(await screen.findByRole("textbox", { name: "Message" }), "Ambiguous request");
    await userEvent.click(screen.getByRole("button", { name: "Send message" }));

    expect(await screen.findByText(userMessage.content)).toBeInTheDocument();
    expect(screen.getByText(/Conversation history was reloaded/)).toBeInTheDocument();
    expect(screen.queryByText(/OPENAI_API_KEY/)).not.toBeInTheDocument();
    expect(messages).toHaveBeenCalledTimes(2);
  });
});
