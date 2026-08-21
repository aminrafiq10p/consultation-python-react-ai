import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ConsultationApiError } from "./consultationApi";
import { ConsultationConversation, type ConsultationConversationService } from "./ConsultationConversation";
import type { ConsultationMessage } from "./consultationTypes";

const consultationId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const assistantId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";

const assistantMessage = (action: ConsultationMessage["handoff"]): ConsultationMessage => ({
  id: assistantId,
  consultation_id: consultationId,
  role: "ASSISTANT",
  content: "The assistant prose does not control this action.",
  structured_payload: null,
  handoff: action,
  created_at: "2026-08-20T10:00:00Z",
});

const serviceFor = (
  items: ConsultationMessage[],
  overrides: Partial<ConsultationConversationService> = {},
): ConsultationConversationService => ({
  messages: vi.fn().mockResolvedValue({ items }),
  submitMessage: vi.fn(),
  generateSummary: vi.fn().mockResolvedValue({}),
  ...overrides,
});

const renderConversation = (
  service: ConsultationConversationService,
  initialEntry = `/consultations/${consultationId}`,
  consultationStatus: "PENDING" | "COMPLETED" | "BOOKED" = "PENDING",
) => render(
  <MemoryRouter initialEntries={[initialEntry]}>
    <Routes>
      <Route
        path="/consultations/:consultationId"
        element={
          <ConsultationConversation
            consultationId={consultationId}
            service={service}
            onNotFound={vi.fn()}
            consultationStatus={consultationStatus}
          />
        }
      />
      <Route path="/consultations/:consultationId/summary" element={<div>Summary route</div>} />
      <Route path="/appointments" element={<div>Appointments route</div>} />
    </Routes>
  </MemoryRouter>,
);

describe("ConsultationConversation handoff CTA", () => {
  it.each([
    ["CONTINUE_CONSULTATION", "Continue Consultation"],
    ["GENERATE_SUMMARY", "Generate Summary"],
    ["VIEW_SUMMARY", "View Summary"],
    ["VIEW_APPOINTMENTS", "View Appointments"],
  ] as const)("renders the typed %s CTA", async (action, label) => {
    const service = serviceFor([
      assistantMessage({
        type: "BOOKING_HANDOFF",
        action,
        consultation_id: consultationId,
        target: action === "VIEW_APPOINTMENTS"
          ? "/appointments"
          : action === "VIEW_SUMMARY"
            ? `/consultations/${consultationId}/summary`
            : `/consultations/${consultationId}`,
      }),
    ]);

    renderConversation(service);
    expect(await screen.findByRole("button", { name: label })).toBeInTheDocument();
    expect(screen.getByText("The assistant prose does not control this action.")).toBeInTheDocument();
  });

  it("activates view actions from the keyboard and performs no booking POST", async () => {
    const service = serviceFor([
      assistantMessage({
        type: "BOOKING_HANDOFF",
        action: "VIEW_APPOINTMENTS",
        consultation_id: consultationId,
        target: "/appointments",
      }),
    ]);
    const user = userEvent.setup();

    renderConversation(service);
    const button = await screen.findByRole("button", { name: "View Appointments" });
    button.focus();
    await user.keyboard("{Enter}");

    expect(await screen.findByText("Appointments route")).toBeInTheDocument();
    expect(service.generateSummary).not.toHaveBeenCalled();
    expect(service.submitMessage).not.toHaveBeenCalled();
  });

  it("generates once, disables duplicate activation, and navigates only on success", async () => {
    let resolveSummary!: () => void;
    const generateSummary = vi.fn(() => new Promise<void>((resolve) => {
      resolveSummary = resolve;
    }));
    const service = serviceFor([
      assistantMessage({
        type: "BOOKING_HANDOFF",
        action: "GENERATE_SUMMARY",
        consultation_id: consultationId,
        target: `/consultations/${consultationId}`,
      }),
    ], { generateSummary });
    const user = userEvent.setup();

    renderConversation(service);
    const button = await screen.findByRole("button", { name: "Generate Summary" });
    await user.click(button);
    expect(screen.getByRole("button", { name: "Generating Summary…" })).toBeDisabled();
    expect(generateSummary).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Generating Summary…" }));
    expect(generateSummary).toHaveBeenCalledTimes(1);

    resolveSummary();
    expect(await screen.findByText("Summary route")).toBeInTheDocument();
  });

  it("shows recoverable feedback and remains on the conversation when summary generation fails", async () => {
    const generateSummary = vi.fn().mockRejectedValue(new ConsultationApiError("summary-generation"));
    const service = serviceFor([
      assistantMessage({
        type: "BOOKING_HANDOFF",
        action: "GENERATE_SUMMARY",
        consultation_id: consultationId,
        target: `/consultations/${consultationId}`,
      }),
    ], { generateSummary });

    renderConversation(service);
    await userEvent.click(await screen.findByRole("button", { name: "Generate Summary" }));
    expect(await screen.findByText("The summary could not be generated right now. Please try again.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate Summary" })).toBeEnabled();
    expect(screen.queryByText("Summary route")).not.toBeInTheDocument();
  });

  it("does not create a CTA from assistant prose or malformed metadata", async () => {
    const proseOnly = assistantMessage(null);
    const malformed = {
      ...assistantMessage({
      type: "BOOKING_HANDOFF",
      action: "GENERATE_SUMMARY",
      consultation_id: "not-a-uuid",
      target: `/consultations/${consultationId}/summary`,
      }),
      id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    };
    const service = serviceFor([proseOnly, malformed]);

    renderConversation(service);
    await screen.findAllByText(proseOnly.content);
    expect(screen.queryByRole("button", { name: /Consultation|Summary|Appointments/ })).not.toBeInTheDocument();
  });

  it.each(["COMPLETED", "BOOKED"] as const)(
    "keeps %s conversations read-only after reloading persisted messages",
    async (status) => {
      const service = serviceFor([
        assistantMessage({
          type: "BOOKING_HANDOFF",
          action: "GENERATE_SUMMARY",
          consultation_id: consultationId,
          target: `/consultations/${consultationId}`,
        }),
      ]);

      renderConversation(service, `/consultations/${consultationId}`, status);

      expect(await screen.findByText(/This conversation is read-only/)).toBeInTheDocument();
      expect(screen.queryByRole("textbox", { name: "Message" })).not.toBeInTheDocument();
      expect(service.submitMessage).not.toHaveBeenCalled();
      expect(service.generateSummary).not.toHaveBeenCalled();
    },
  );
});
