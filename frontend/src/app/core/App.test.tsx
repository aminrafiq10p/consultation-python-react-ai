import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { dashboardApi } from "../features/dashboard/dashboardApi";
import { appointmentApi } from "../features/appointments/appointmentApi";

vi.mock("../features/dashboard/dashboardApi", () => ({
  dashboardApi: { getMetrics: vi.fn() },
}));
vi.mock("../features/appointments/appointmentApi", () => ({
  appointmentApi: { listAppointments: vi.fn() },
}));

const getMetrics = vi.mocked(dashboardApi.getMetrics);
const listAppointments = vi.mocked(appointmentApi.listAppointments);

function RouterProbe() {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output aria-label="Current location">{location.pathname}</output>
      <button onClick={() => navigate(-1)}>Back</button>
    </>
  );
}

beforeEach(() => {
  getMetrics.mockReset();
  getMetrics.mockResolvedValue({
    total_consultations: 4,
    booked_appointments: 1,
    conversion_rate: 25,
    consultation_trends: [],
    recent_activity: [],
    pending_clinical_reviews: [],
  });
  listAppointments.mockResolvedValue({ items: [] });
});

describe("App routes", () => {
  it("renders the dashboard directly inside the shared layout", async () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      within(screen.getByRole("banner")).getByText("AI Consultation Platform"),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(await screen.findByText("25.00%")).toBeInTheDocument();
    expect(getMetrics).toHaveBeenCalledTimes(1);
  });

  it("redirects the root to the dashboard with replacement", async () => {
    render(
      <MemoryRouter initialEntries={["/consultations", "/"]} initialIndex={1}>
        <App />
        <RouterProbe />
      </MemoryRouter>,
    );

    expect(await screen.findByLabelText("Current location")).toHaveTextContent("/dashboard");
    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    expect(await screen.findByLabelText("Current location")).toHaveTextContent("/consultations");
    expect(screen.getByRole("heading", { name: "Consultation Records" })).toBeInTheDocument();
  });

  it.each([
    ["/consultations", "Consultation Records"],
    ["/consultations/new", "New Consultation"],
    ["/consultations/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "Consultation Details"],
    ["/consultations/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/summary", "Consultation Summary"],
  ])("keeps %s directly reachable", (path, heading) => {
    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
  });

  it("renders the appointments destination directly inside the shared layout", async () => {
    render(
      <MemoryRouter initialEntries={["/appointments"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Appointments" })).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent("No appointments have been booked yet.");
    expect(listAppointments).toHaveBeenCalledTimes(1);
  });

  it("resolves the static creation route rather than treating new as a consultation ID", () => {
    render(
      <MemoryRouter initialEntries={["/consultations/new"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "New Consultation" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Consultation Details" })).not.toBeInTheDocument();
  });

  it("registers the real appointment booking route", () => {
    render(
      <MemoryRouter initialEntries={[
        "/consultations/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/appointments/new?recommendation_id=11111111-1111-4111-8111-111111111111",
      ]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Book Appointment" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading appointment details");
    expect(screen.queryByText(/Appointment setup is not available yet/)).not.toBeInTheDocument();
  });
});
