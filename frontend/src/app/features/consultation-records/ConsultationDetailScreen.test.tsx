import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ConsultationApiError } from "./consultationApi";
import {
  ConsultationDetailScreen,
  type ConsultationDetailService,
} from "./ConsultationDetailScreen";
import type { ConsultationRecord } from "./consultationTypes";

const record: ConsultationRecord = {
  id: "consultation-42",
  patient_name: "Amina Khan",
  primary_concern: "Persistent knee pain",
  recommended_procedure: "Orthopedic consultation",
  status: "PENDING",
};

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
  it("passes the route identifier to the detail service", async () => {
    const detail = vi.fn().mockResolvedValue(record);

    renderScreen({ detail });

    expect(await screen.findByText(record.patient_name)).toBeInTheDocument();
    expect(detail).toHaveBeenCalledWith(record.id);
  });

  it("renders the four approved user-facing fields", async () => {
    renderScreen({ detail: vi.fn().mockResolvedValue(record) });

    expect(await screen.findByText(record.patient_name)).toBeInTheDocument();
    expect(screen.getByText(record.primary_concern)).toBeInTheDocument();
    expect(screen.getByText(record.recommended_procedure)).toBeInTheDocument();
    expect(screen.getByText(record.status)).toBeInTheDocument();
  });

  it("shows a visible loading state without fake detail data", () => {
    renderScreen({
      detail: vi.fn(() => new Promise<ConsultationRecord>(() => undefined)),
    });

    expect(screen.getByRole("status")).toHaveTextContent("Loading consultation details");
    expect(screen.queryByText(record.patient_name)).not.toBeInTheDocument();
  });

  it("shows the unavailable-detail state for the approved not-found outcome", async () => {
    renderScreen({
      detail: vi.fn().mockRejectedValue(new ConsultationApiError("not-found")),
    });

    expect(await screen.findByText(/Consultation not found/)).toBeInTheDocument();
    expect(screen.queryByText(/could not be loaded/)).not.toBeInTheDocument();
  });

  it("shows a distinct safe recoverable error for other failures", async () => {
    renderScreen({
      detail: vi.fn().mockRejectedValue(new Error("private server detail")),
    });

    expect(
      await screen.findByText("Consultation details could not be loaded. Please try again."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Consultation not found/)).not.toBeInTheDocument();
    expect(screen.queryByText("private server detail")).not.toBeInTheDocument();
  });
});
