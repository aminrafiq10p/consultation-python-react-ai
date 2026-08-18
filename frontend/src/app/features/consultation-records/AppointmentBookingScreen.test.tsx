import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import {
  AppointmentBookingScreen,
  type AppointmentBookingService,
} from "./AppointmentBookingScreen";
import { ConsultationApiError, type ConsultationApiErrorKind } from "./consultationApi";
import type { Appointment, ConsultationSummary } from "./consultationTypes";

const consultationId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const recommendationId = "11111111-1111-4111-8111-111111111111";
const summary: ConsultationSummary = {
  id: "33333333-3333-4333-8333-333333333333",
  consultation_id: consultationId,
  patient_summary: "Summary",
  recommended_treatments: [
    { id: recommendationId, treatment: "Physical therapy", position: 1 },
    { id: "22222222-2222-4222-8222-222222222222", treatment: "Review", position: 2 },
  ],
  recommendation_rationale: null,
  created_at: "2026-08-17T10:00:00Z",
};
const appointment: Appointment = {
  id: "44444444-4444-4444-8444-444444444444",
  consultation_id: consultationId,
  recommendation: { id: recommendationId, treatment: "Physical therapy" },
  scheduled_at: "2030-01-02T10:30:00.000Z",
  location: "Downtown Clinic",
  created_at: "2026-08-17T12:00:00Z",
};

const serviceFor = (
  overrides: Partial<AppointmentBookingService> = {},
): AppointmentBookingService => ({
  summary: vi.fn().mockResolvedValue(summary),
  bookAppointment: vi.fn().mockResolvedValue(appointment),
  ...overrides,
});

function LocationView() {
  const location = useLocation();
  return <span data-testid="location">{location.pathname}</span>;
}

const renderScreen = (
  service: AppointmentBookingService,
  entry = `/consultations/${consultationId}/appointments/new?recommendation_id=${recommendationId}`,
) => render(
  <MemoryRouter initialEntries={[entry]}>
    <LocationView />
    <Routes>
      <Route path="/consultations/:consultationId?/appointments/new" element={<AppointmentBookingScreen service={service} now={() => new Date("2029-01-01T00:00:00Z")} />} />
      <Route path="/consultations" element={<span>Records destination</span>} />
      <Route path="/consultations/:consultationId/summary" element={<span>Summary destination</span>} />
    </Routes>
  </MemoryRouter>,
);

async function fillValidForm() {
  await userEvent.type(screen.getByLabelText(/Appointment date and time/), "2030-01-02T10:30");
  await userEvent.type(screen.getByLabelText(/Location/), "  Downtown Clinic  ");
}

describe("AppointmentBookingScreen", () => {
  it("extracts route/query IDs, loads the persisted summary, and displays only the selected treatment read-only", async () => {
    const service = serviceFor();
    renderScreen(service);
    expect(screen.getByRole("status")).toHaveTextContent("Loading appointment details");
    expect(await screen.findByText("Physical therapy")).toBeInTheDocument();
    expect(service.summary).toHaveBeenCalledOnce();
    expect(service.summary).toHaveBeenCalledWith(consultationId);
    expect(screen.queryByDisplayValue("Physical therapy")).not.toBeInTheDocument();
    expect(screen.queryByText("Review")).not.toBeInTheDocument();
  });

  it.each([
    ["missing query", `/consultations/${consultationId}/appointments/new`],
    ["malformed query", `/consultations/${consultationId}/appointments/new?recommendation_id=bad`],
    ["multiple query values", `/consultations/${consultationId}/appointments/new?recommendation_id=${recommendationId}&recommendation_id=${recommendationId}`],
    ["malformed consultation", "/consultations/bad/appointments/new?recommendation_id=" + recommendationId],
  ])("blocks %s context without loading or submission", (_name, entry) => {
    const service = serviceFor();
    renderScreen(service, entry);
    expect(screen.getByText(/booking link is invalid or incomplete/i)).toBeInTheDocument();
    expect(service.summary).not.toHaveBeenCalled();
    expect(service.bookAppointment).not.toHaveBeenCalled();
  });

  it("blocks a recommendation that is absent from the persisted summary", async () => {
    const service = serviceFor();
    renderScreen(service, `/consultations/${consultationId}/appointments/new?recommendation_id=55555555-5555-4555-8555-555555555555`);
    expect(await screen.findByText(/selected recommendation is not available/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Confirm Appointment" })).not.toBeInTheDocument();
  });

  it.each([
    ["not-found", "Consultation not found"],
    ["summary-not-available", "persisted consultation summary is not available"],
    ["retrieval", "Appointment details could not be loaded"],
  ] as const)("shows the distinct %s summary state", async (kind, message) => {
    const service = serviceFor({ summary: vi.fn().mockRejectedValue(new ConsultationApiError(kind)) });
    renderScreen(service);
    expect(await screen.findByText(new RegExp(message, "i"))).toBeInTheDocument();
  });

  it("retries only a recoverable summary retrieval failure", async () => {
    const getSummary = vi.fn().mockRejectedValueOnce(new ConsultationApiError("retrieval")).mockResolvedValue(summary);
    renderScreen(serviceFor({ summary: getSummary }));
    await userEvent.click(await screen.findByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Physical therapy")).toBeInTheDocument();
    expect(getSummary).toHaveBeenCalledTimes(2);
  });

  it("validates required, invalid/nonfuture datetime and normalized location without submitting", async () => {
    const service = serviceFor();
    renderScreen(service);
    await screen.findByText("Physical therapy");
    await userEvent.click(screen.getByRole("button", { name: "Confirm Appointment" }));
    expect(screen.getByText("Appointment date and time are required.")).toBeInTheDocument();
    expect(screen.getByText("Location is required.")).toBeInTheDocument();

    const datetime = screen.getByLabelText(/Appointment date and time/);
    await userEvent.type(datetime, "2028-01-01T10:00");
    await userEvent.type(screen.getByLabelText(/Location/), "   ");
    await userEvent.click(screen.getByRole("button", { name: "Confirm Appointment" }));
    expect(screen.getByText(/must be in the future/)).toBeInTheDocument();
    expect(service.bookAppointment).not.toHaveBeenCalled();
  });

  it("rejects locations over 200 Unicode code points", async () => {
    const service = serviceFor();
    renderScreen(service);
    await screen.findByText("Physical therapy");
    await userEvent.type(screen.getByLabelText(/Appointment date and time/), "2030-01-02T10:30");
    await userEvent.type(screen.getByLabelText(/Location/), "😀".repeat(201));
    await userEvent.click(screen.getByRole("button", { name: "Confirm Appointment" }));
    expect(screen.getByText(/200 characters or fewer/)).toBeInTheDocument();
    expect(service.bookAppointment).not.toHaveBeenCalled();
  });

  it("submits exact IDs once with trimmed location and an explicit-offset ISO instant", async () => {
    let resolve!: (value: Appointment) => void;
    const bookAppointment = vi.fn(() => new Promise<Appointment>((done) => { resolve = done; }));
    renderScreen(serviceFor({ bookAppointment }));
    await screen.findByText("Physical therapy");
    await fillValidForm();
    const submit = screen.getByRole("button", { name: "Confirm Appointment" });
    await userEvent.dblClick(submit);
    expect(bookAppointment).toHaveBeenCalledOnce();
    expect(bookAppointment).toHaveBeenCalledWith(consultationId, {
      recommendation_id: recommendationId,
      scheduled_at: new Date("2030-01-02T10:30").toISOString(),
      location: "Downtown Clinic",
    });
    expect(screen.getByRole("button", { name: "Confirming…" })).toBeDisabled();
    expect(screen.getByLabelText(/Location/)).toBeDisabled();
    resolve(appointment);
  });

  it.each([
    ["booking-validation", /details were not accepted/],
    ["booking-consultation-not-found", /consultation no longer exists/],
    ["booking-recommendation-not-found", /recommendation no longer exists/],
    ["recommendation-not-bookable", /recommendation cannot be booked/],
    ["consultation-not-bookable", /not eligible for appointment booking/],
    ["appointment-already-exists", /appointment already exists/],
    ["booking-submission", /appointment may have been created/],
  ] as [ConsultationApiErrorKind, RegExp][])("maps %s safely and preserves form values", async (kind, message) => {
    const bookAppointment = vi.fn().mockRejectedValue(new ConsultationApiError(kind));
    renderScreen(serviceFor({ bookAppointment }));
    await screen.findByText("Physical therapy");
    await fillValidForm();
    await userEvent.click(screen.getByRole("button", { name: "Confirm Appointment" }));
    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByLabelText(/Appointment date and time/)).toHaveValue("2030-01-02T10:30");
    expect(screen.getByLabelText(/Location/)).toHaveValue("Downtown Clinic");
    expect(bookAppointment).toHaveBeenCalledOnce();
    if (kind === "appointment-already-exists") {
      expect(screen.getByRole("button", { name: "Confirm Appointment" })).toBeDisabled();
    }
  });

  it("navigates to records with replacement only after confirmed success", async () => {
    renderScreen(serviceFor());
    await screen.findByText("Physical therapy");
    await fillValidForm();
    await userEvent.click(screen.getByRole("button", { name: "Confirm Appointment" }));
    expect(await screen.findByText("Records destination")).toBeInTheDocument();
    expect(screen.getByTestId("location")).toHaveTextContent("/consultations");
    expect(window.history.length).toBeGreaterThan(0);
  });

  it("does not automatically retry an ambiguous failure", async () => {
    const bookAppointment = vi.fn().mockRejectedValue(new Error("network"));
    renderScreen(serviceFor({ bookAppointment }));
    await screen.findByText("Physical therapy");
    await fillValidForm();
    await userEvent.click(screen.getByRole("button", { name: "Confirm Appointment" }));
    await waitFor(() => expect(screen.getByText(/appointment may have been created/)).toBeInTheDocument());
    expect(bookAppointment).toHaveBeenCalledOnce();
  });
});
