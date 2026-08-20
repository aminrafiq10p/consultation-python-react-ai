import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppointmentsScreen, type AppointmentListService } from "./AppointmentsScreen";
import type { AppointmentListItem } from "./appointmentTypes";

const appointment: AppointmentListItem = {
  id: "77777777-7777-4777-8777-777777777777",
  consultation_id: "88888888-8888-4888-8888-888888888888",
  patient_name: "Amina Khan",
  recommendation: { id: "99999999-9999-4999-8999-999999999999", treatment: "Physiotherapy" },
  scheduled_at: "2026-08-20T14:30:00Z",
  location: "Downtown Clinic",
  created_at: "2026-08-17T12:00:00Z",
};

const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
};

function setViewport(desktop: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: desktop && query.includes("min-width"), media: query, onchange: null,
    addListener: vi.fn(), removeListener: vi.fn(), addEventListener: vi.fn(),
    removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
  }));
}

function LocationProbe() {
  return <output aria-label="Current location">{useLocation().pathname}</output>;
}

const renderScreen = (service: AppointmentListService, desktop = true) => {
  setViewport(desktop);
  return render(
    <MemoryRouter initialEntries={["/appointments"]}>
      <Routes>
        <Route path="/appointments" element={<AppointmentsScreen service={service} />} />
        <Route path="/consultations/:consultationId" element={<LocationProbe />} />
      </Routes>
    </MemoryRouter>,
  );
};

afterEach(() => vi.restoreAllMocks());

describe("AppointmentsScreen", () => {
  it("shows an accessible loading state and makes one request on entry", () => {
    const request = deferred<{ items: AppointmentListItem[] }>();
    const listAppointments = vi.fn(() => request.promise);

    renderScreen({ listAppointments });

    expect(screen.getByRole("heading", { name: "Appointments" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading appointments");
    expect(listAppointments).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Amina Khan")).not.toBeInTheDocument();
  });

  it("renders desktop appointments in a restrained table with persisted fields", async () => {
    renderScreen({ listAppointments: vi.fn().mockResolvedValue({ items: [appointment] }) });

    expect(await screen.findByRole("table", { name: "Appointments" })).toBeInTheDocument();
    expect(screen.getByText("Amina Khan")).toBeInTheDocument();
    expect(screen.getByText("Physiotherapy")).toBeInTheDocument();
    expect(screen.getByText("Downtown Clinic")).toBeInTheDocument();
    expect(screen.getByText(appointment.id)).toBeInTheDocument();
    expect(screen.getByText(`Consultation ID: ${appointment.consultation_id}`)).toBeInTheDocument();
    expect(screen.getByText(`Recommendation ID: ${appointment.recommendation.id}`)).toBeInTheDocument();
    expect(screen.getAllByRole("time").map((element) => element.getAttribute("datetime"))).toContain(
      appointment.scheduled_at,
    );
    expect(screen.getAllByRole("time").map((element) => element.getAttribute("datetime"))).toContain(
      appointment.created_at,
    );
    expect(screen.getByRole("link", { name: "View consultation for Amina Khan" })).toHaveAttribute(
      "href",
      `/consultations/${appointment.consultation_id}`,
    );
  });

  it("uses a readable stacked card layout at narrow widths without a table", async () => {
    renderScreen({ listAppointments: vi.fn().mockResolvedValue({ items: [appointment] }) }, false);

    expect(await screen.findByRole("article")).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: "Appointments" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Amina Khan" })).toBeInTheDocument();
    expect(screen.getByText("Downtown Clinic")).toBeInTheDocument();
    expect(screen.getByText(appointment.id)).toHaveStyle({ overflowWrap: "anywhere" });
  });

  it("navigates to the persisted related consultation through one keyboard-accessible action", async () => {
    renderScreen({ listAppointments: vi.fn().mockResolvedValue({ items: [appointment] }) });
    const user = userEvent.setup();

    const link = await screen.findByRole("link", { name: "View consultation for Amina Khan" });
    expect(screen.getAllByRole("link", { name: "View consultation for Amina Khan" })).toHaveLength(1);
    link.focus();
    await user.keyboard("{Enter}");

    expect(await screen.findByLabelText("Current location")).toHaveTextContent(
      `/consultations/${appointment.consultation_id}`,
    );
  });

  it("distinguishes an empty successful response", async () => {
    renderScreen({ listAppointments: vi.fn().mockResolvedValue({ items: [] }) });

    expect(await screen.findByRole("alert")).toHaveTextContent("No appointments have been booked yet.");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("shows a safe recoverable error without an empty state or automatic retry", async () => {
    const listAppointments = vi.fn().mockRejectedValue(new Error("private backend detail"));
    renderScreen({ listAppointments });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Appointments could not be loaded. Please try again.",
    );
    expect(screen.queryByText("private backend detail")).not.toBeInTheDocument();
    expect(screen.queryByText("No appointments have been booked yet.")).not.toBeInTheDocument();
    expect(listAppointments).toHaveBeenCalledTimes(1);
  });

  it("performs exactly one explicit retry and clears the previous result while pending", async () => {
    const retryRequest = deferred<{ items: AppointmentListItem[] }>();
    const listAppointments = vi.fn()
      .mockRejectedValueOnce(new Error("failed"))
      .mockImplementationOnce(() => retryRequest.promise);
    renderScreen({ listAppointments });

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(listAppointments).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("status")).toHaveTextContent("Loading appointments");
    expect(screen.queryByText("Amina Khan")).not.toBeInTheDocument();

    retryRequest.resolve({ items: [appointment] });
    expect(await screen.findByText("Amina Khan")).toBeInTheDocument();
    expect(listAppointments).toHaveBeenCalledTimes(2);
  });
});
