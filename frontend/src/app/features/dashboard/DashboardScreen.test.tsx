import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { DashboardScreen, type DashboardMetricsService } from "./DashboardScreen";
import type { DashboardMetrics } from "./dashboardTypes";

const populatedMetrics: DashboardMetrics = {
  total_consultations: 3,
  booked_appointments: 1,
  conversion_rate: 33.33,
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
    const request = deferred<DashboardMetrics>();
    const getMetrics = vi.fn(() => request.promise);

    renderScreen({ getMetrics });

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading dashboard metrics");
    expect(screen.queryByRole("heading", { name: "Total consultations" })).not.toBeInTheDocument();
    expect(getMetrics).toHaveBeenCalledTimes(1);
  });

  it("renders the three server-returned metrics with presentation-only formatting", async () => {
    renderScreen({ getMetrics: vi.fn().mockResolvedValue(populatedMetrics) });

    expect(await screen.findByRole("heading", { name: "Total consultations" })).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Booked appointments" })).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Conversion rate" })).toBeInTheDocument();
    expect(screen.getByText("33.33%")).toBeInTheDocument();
  });

  it.each([
    [25, "25.00%"],
    [100, "100.00%"],
  ])("formats a received conversion rate of %s as %s", async (conversionRate, expected) => {
    renderScreen({
      getMetrics: vi.fn().mockResolvedValue({
        total_consultations: 4,
        booked_appointments: 1,
        conversion_rate: conversionRate,
      }),
    });

    expect(await screen.findByText(expected)).toBeInTheDocument();
  });

  it("renders zero data as a successful result", async () => {
    renderScreen({
      getMetrics: vi.fn().mockResolvedValue({
        total_consultations: 0,
        booked_appointments: 0,
        conversion_rate: 0,
      }),
    });

    expect(await screen.findByText("0.00%")).toBeInTheDocument();
    expect(screen.getAllByText("0")).toHaveLength(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows one safe recoverable error without metrics or automatic retries", async () => {
    const getMetrics = vi.fn().mockRejectedValue(new Error("private backend detail"));
    renderScreen({ getMetrics });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Dashboard metrics could not be loaded. Please try again.",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.queryByText("private backend detail")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Total consultations" })).not.toBeInTheDocument();
    await waitFor(() => expect(getMetrics).toHaveBeenCalledTimes(1));
  });

  it("makes one explicit retry, shows pending state, and recovers", async () => {
    const retry = deferred<DashboardMetrics>();
    const getMetrics = vi
      .fn()
      .mockRejectedValueOnce(new Error("failed"))
      .mockImplementationOnce(() => retry.promise);
    renderScreen({ getMetrics });

    await userEvent.click(await screen.findByRole("button", { name: "Retry" }));

    expect(getMetrics).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("status")).toHaveTextContent("Loading dashboard metrics");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Total consultations" })).not.toBeInTheDocument();

    retry.resolve(populatedMetrics);

    expect(await screen.findByText("33.33%")).toBeInTheDocument();
    expect(getMetrics).toHaveBeenCalledTimes(2);
  });

  it("ignores a pending result after unmount", async () => {
    const request = deferred<DashboardMetrics>();
    const { unmount } = renderScreen({ getMetrics: vi.fn(() => request.promise) });

    unmount();
    request.resolve(populatedMetrics);

    await Promise.resolve();
  });
});
