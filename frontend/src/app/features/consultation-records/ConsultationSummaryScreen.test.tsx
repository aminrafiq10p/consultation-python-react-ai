import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation, useParams } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AppointmentUnavailableScreen } from "./AppointmentUnavailableScreen";
import { ConsultationApiError } from "./consultationApi";
import {
  ConsultationSummaryScreen,
  type ConsultationSummaryService,
} from "./ConsultationSummaryScreen";
import type { ConsultationRecord, ConsultationSummary } from "./consultationTypes";

const consultationId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const firstRecommendationId = "11111111-1111-4111-8111-111111111111";
const secondRecommendationId = "22222222-2222-4222-8222-222222222222";

const summary: ConsultationSummary = {
  id: "33333333-3333-4333-8333-333333333333",
  consultation_id: consultationId,
  patient_summary: "Persistent knee pain after exercise.\nNo injury was reported.",
  recommended_treatments: [
    { id: firstRecommendationId, treatment: "Physical therapy", position: 1 },
    { id: secondRecommendationId, treatment: "Orthopedic review", position: 2 },
  ],
  recommendation_rationale: "Conservative care can precede specialist review.",
  created_at: "2026-08-17T10:00:00Z",
};

const restarted: ConsultationRecord = {
  id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  patient_name: "Amina Khan",
  primary_concern: "Persistent knee pain",
  recommended_procedure: "",
  status: "PENDING",
};

const serviceFor = (
  overrides: Partial<ConsultationSummaryService> = {},
): ConsultationSummaryService => ({
  summary: vi.fn().mockResolvedValue(summary),
  restartConsultation: vi.fn().mockResolvedValue(restarted),
  ...overrides,
});

function LocationView() {
  const location = useLocation();
  return <span data-testid="location">{location.pathname}{location.search}</span>;
}

function DetailDestination() {
  return <span>New consultation {useParams().consultationId}</span>;
}

const renderScreen = (service: ConsultationSummaryService) =>
  render(
    <MemoryRouter initialEntries={[`/consultations/${consultationId}/summary`]}>
      <LocationView />
      <Routes>
        <Route
          path="/consultations/:consultationId/summary"
          element={<ConsultationSummaryScreen service={service} />}
        />
        <Route path="/consultations/:consultationId" element={<DetailDestination />} />
        <Route
          path="/consultations/:consultationId/appointments/new"
          element={<AppointmentUnavailableScreen />}
        />
      </Routes>
    </MemoryRouter>,
  );

describe("ConsultationSummaryScreen", () => {
  it("retrieves only the persisted summary using the route consultation ID", async () => {
    const getSummary = vi.fn().mockResolvedValue(summary);
    const service = serviceFor({ summary: getSummary });
    renderScreen(service);

    expect(await screen.findByText(/Persistent knee pain after exercise/)).toBeInTheDocument();
    expect(getSummary).toHaveBeenCalledOnce();
    expect(getSummary).toHaveBeenCalledWith(consultationId);
    expect(service.restartConsultation).not.toHaveBeenCalled();
  });

  it("shows loading while persisted summary retrieval is pending", () => {
    renderScreen(serviceFor({
      summary: vi.fn(() => new Promise<ConsultationSummary>(() => undefined)),
    }));

    expect(screen.getByRole("status")).toHaveTextContent("Loading consultation summary");
    expect(screen.queryByRole("button", { name: "Restart Consultation" })).not.toBeInTheDocument();
  });

  it("renders patient text safely, preserves backend order, and shows rationale", async () => {
    renderScreen(serviceFor());

    expect(await screen.findByText(/Persistent knee pain after exercise/)).toBeInTheDocument();
    const choices = within(screen.getByRole("radiogroup", { name: "Recommended treatments" }))
      .getAllByRole("radio");
    expect(choices.map((choice) => choice.getAttribute("value"))).toEqual([
      firstRecommendationId,
      secondRecommendationId,
    ]);
    expect(screen.getByText(summary.recommendation_rationale!)).toBeInTheDocument();

    const unsafe = "<img src=x onerror=alert('private')>";
    const { unmount } = renderScreen(serviceFor({
      summary: vi.fn().mockResolvedValue({ ...summary, patient_summary: unsafe }),
    }));
    expect(await screen.findByText(unsafe)).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    unmount();
  });

  it("omits the rationale section when rationale is null", async () => {
    renderScreen(serviceFor({
      summary: vi.fn().mockResolvedValue({ ...summary, recommendation_rationale: null }),
    }));

    expect(await screen.findByText(/Persistent knee pain after exercise/)).toBeInTheDocument();
    expect(screen.queryByText("Recommendation rationale")).not.toBeInTheDocument();
  });

  it("shows unavailable and missing-consultation states distinctly", async () => {
    const first = renderScreen(serviceFor({
      summary: vi.fn().mockRejectedValue(new ConsultationApiError("summary-not-available")),
    }));
    expect(await screen.findByText(/has not been generated/)).toBeInTheDocument();
    first.unmount();

    renderScreen(serviceFor({
      summary: vi.fn().mockRejectedValue(new ConsultationApiError("not-found")),
    }));
    expect(await screen.findByText(/Consultation not found/)).toBeInTheDocument();
  });

  it("shows a safe recoverable retrieval error and retries", async () => {
    const getSummary = vi.fn()
      .mockRejectedValueOnce(new Error("database password"))
      .mockResolvedValueOnce(summary);
    renderScreen(serviceFor({ summary: getSummary }));

    expect(await screen.findByText(/summary could not be loaded/)).toBeInTheDocument();
    expect(screen.queryByText("database password")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText(/Persistent knee pain after exercise/)).toBeInTheDocument();
    expect(getSummary).toHaveBeenCalledTimes(2);
  });

  it("uses one stable recommendation selection and enables booking only after selection", async () => {
    renderScreen(serviceFor());
    const book = await screen.findByRole("button", { name: "Book Appointment" });
    expect(book).toBeDisabled();

    await userEvent.click(screen.getByRole("radio", { name: "Physical therapy" }));
    expect(screen.getByRole("radio", { name: "Physical therapy" })).toBeChecked();
    expect(book).toBeEnabled();
    await userEvent.click(screen.getByRole("radio", { name: "Orthopedic review" }));
    expect(screen.getByRole("radio", { name: "Physical therapy" })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: "Orthopedic review" })).toBeChecked();
  });

  it("invokes restart once, disables duplicates, and preserves the loaded summary", async () => {
    let resolveRestart!: (record: ConsultationRecord) => void;
    const restartConsultation = vi.fn(
      () => new Promise<ConsultationRecord>((resolve) => { resolveRestart = resolve; }),
    );
    renderScreen(serviceFor({ restartConsultation }));

    await userEvent.click(await screen.findByRole("button", { name: "Restart Consultation" }));
    expect(screen.getByRole("button", { name: "Restarting…" })).toBeDisabled();
    expect(screen.getByText(/Persistent knee pain after exercise/)).toBeInTheDocument();
    expect(restartConsultation).toHaveBeenCalledOnce();
    expect(restartConsultation).toHaveBeenCalledWith(consultationId);

    resolveRestart(restarted);
    expect(await screen.findByText(`New consultation ${restarted.id}`)).toBeInTheDocument();
    expect(screen.getByTestId("location")).toHaveTextContent(`/consultations/${restarted.id}`);
  });

  it.each([
    [new ConsultationApiError("not-restartable"), "This consultation cannot be restarted."],
    [new ConsultationApiError("not-found"), "The source consultation is no longer available."],
    [new Error("private restart detail"), "Consultation could not be restarted. Please try again."],
  ])("shows a safe restart failure and keeps source data", async (error, message) => {
    renderScreen(serviceFor({ restartConsultation: vi.fn().mockRejectedValue(error) }));
    await userEvent.click(await screen.findByRole("button", { name: "Restart Consultation" }));

    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByText(/Persistent knee pain after exercise/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Restart Consultation" })).toBeEnabled();
    expect(screen.queryByText("private restart detail")).not.toBeInTheDocument();
  });

  it("navigates booking with stable IDs and exposes only the unavailable boundary", async () => {
    const service = serviceFor();
    renderScreen(service);

    await userEvent.click(await screen.findByRole("radio", { name: "Orthopedic review" }));
    await userEvent.click(screen.getByRole("button", { name: "Book Appointment" }));

    expect(screen.getByTestId("location")).toHaveTextContent(
      `/consultations/${consultationId}/appointments/new?recommendation_id=${secondRecommendationId}`,
    );
    expect(screen.getByText(/Appointment setup is not available yet/)).toBeInTheDocument();
    expect(screen.queryByRole("form")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/date|time|location/i)).not.toBeInTheDocument();
    expect(service.restartConsultation).not.toHaveBeenCalled();
  });
});
