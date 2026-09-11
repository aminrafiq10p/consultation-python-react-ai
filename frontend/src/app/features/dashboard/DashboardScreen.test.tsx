import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { DashboardScreen, type DashboardMetricsService } from "./DashboardScreen";
import type { DashboardResponse } from "./dashboardTypes";

const populatedMetrics: DashboardResponse = {
  total_consultations: 3,
  booked_appointments: 1,
  conversion_rate: 33.33,
  consultation_trends: [{ day: "2026-08-20", consultation_count: 2 }],
  recent_activity: [],
  pending_clinical_reviews: [],
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

const renderScreen = (service: DashboardMetricsService) =>
  render(
    <MemoryRouter>
      <DashboardScreen service={service} />
    </MemoryRouter>,
  );

describe("DashboardScreen", () => {
  it("loads exactly once on mount and shows no fabricated values while pending", () => {
    const request = deferred<DashboardResponse>();
    const getMetrics = vi.fn(() => request.promise);

    renderScreen({ getMetrics });

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading dashboard");
    expect(screen.queryByRole("heading", { name: "Total Consultations" })).not.toBeInTheDocument();
    expect(getMetrics).toHaveBeenCalledTimes(1);
  });

  it("renders the three server-returned metrics with presentation-only formatting", async () => {
    renderScreen({ getMetrics: vi.fn().mockResolvedValue(populatedMetrics) });

    expect(await screen.findByRole("heading", { name: "Total Consultations" })).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Booked Appointments" })).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Conversion Rate" })).toBeInTheDocument();
    expect(screen.getByText("33.33%")).toBeInTheDocument();
  });

  it("renders real trend, activity, and pending-review projections", async () => {
    const consultationId = "123e4567-e89b-12d3-a456-426614174000";
    renderScreen({
      getMetrics: vi.fn().mockResolvedValue({
        ...populatedMetrics,
        consultation_trends: [{ day: "2026-08-20", consultation_count: 2 }],
        recent_activity: [{ activity_type: "consultation_completed", consultation_id: consultationId, timestamp: "2026-08-20T10:00:00Z" }],
        pending_clinical_reviews: [{ consultation_id: consultationId, patient_name: "Ada Lovelace", primary_concern: "Headache", recommended_procedure: "Consultation", status: "PENDING" }],
      }),
    });

    expect(await screen.findByRole("heading", { name: "Consultation Trends" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /last 30 days/i })).toBeInTheDocument();
    expect(screen.getByText("Consultation completed")).toBeInTheDocument();
    expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ada Lovelace/i })).toHaveAttribute("href", `/consultations/${consultationId}`);
  });

  it("keeps each empty projection explicit without placeholder domain data", async () => {
    renderScreen({ getMetrics: vi.fn().mockResolvedValue({ ...populatedMetrics, consultation_trends: [], recent_activity: [], pending_clinical_reviews: [] }) });

    expect(await screen.findByText("No trend data yet.")).toBeInTheDocument();
    expect(screen.getByText("No recent activity yet.")).toBeInTheDocument();
    expect(screen.getByText("No pending clinical reviews.")).toBeInTheDocument();
    expect(screen.queryByText(/Monthly Revenue|Invite Patient|Generate Report/)).not.toBeInTheDocument();
  });

  it.each([
    [25, "25.00%"],
    [100, "100.00%"],
  ])("formats a received conversion rate of %s as %s", async (conversionRate, expected) => {
    renderScreen({
      getMetrics: vi.fn().mockResolvedValue({ ...populatedMetrics, total_consultations: 4, conversion_rate: conversionRate }),
    });

    expect(await screen.findByText(expected)).toBeInTheDocument();
  });

  it("renders zero data as a successful result", async () => {
    renderScreen({
      getMetrics: vi.fn().mockResolvedValue({ ...populatedMetrics, total_consultations: 0, booked_appointments: 0, conversion_rate: 0, consultation_trends: [] }),
    });

    expect(await screen.findByText("0.00%")).toBeInTheDocument();
    expect(screen.getAllByText("0")).toHaveLength(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows one safe recoverable error without metrics or automatic retries", async () => {
    const getMetrics = vi.fn().mockRejectedValue(new Error("private backend detail"));
    renderScreen({ getMetrics });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Dashboard data could not be loaded. Please try again.",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByText("private backend detail")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Total Consultations" })).not.toBeInTheDocument();
    await waitFor(() => expect(getMetrics).toHaveBeenCalledTimes(1));
  });

  it("makes one explicit retry, shows pending state, and recovers", async () => {
    const retry = deferred<DashboardResponse>();
    const getMetrics = vi
      .fn()
      .mockRejectedValueOnce(new Error("failed"))
      .mockImplementationOnce(() => retry.promise);
    renderScreen({ getMetrics });

    await userEvent.click(await screen.findByRole("button", { name: "Retry" }));

    expect(getMetrics).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("status")).toHaveTextContent("Loading dashboard");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Total Consultations" })).not.toBeInTheDocument();

    retry.resolve(populatedMetrics);

    expect(await screen.findByText("33.33%")).toBeInTheDocument();
    expect(getMetrics).toHaveBeenCalledTimes(2);
  });

  it("ignores a pending result after unmount", async () => {
    const request = deferred<DashboardResponse>();
    const { unmount } = renderScreen({ getMetrics: vi.fn(() => request.promise) });

    unmount();
    request.resolve(populatedMetrics);

    await Promise.resolve();
  });
});
