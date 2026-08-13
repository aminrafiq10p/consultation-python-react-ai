import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ConsultationRecordsScreen, type ConsultationListService } from "./ConsultationRecordsScreen";
import type { ConsultationRecord } from "./consultationTypes";

const record: ConsultationRecord = {
  id: "consultation-42",
  patient_name: "Amina Khan",
  primary_concern: "Persistent knee pain",
  recommended_procedure: "Orthopedic consultation",
  status: "PENDING",
};

const renderScreen = (service: ConsultationListService) =>
  render(
    <MemoryRouter initialEntries={["/consultations"]}>
      <Routes>
        <Route path="/consultations" element={<ConsultationRecordsScreen service={service} />} />
      </Routes>
    </MemoryRouter>,
  );

describe("ConsultationRecordsScreen", () => {
  it("renders every required field from returned records", async () => {
    renderScreen({ list: vi.fn().mockResolvedValue({ items: [record] }) });

    expect(await screen.findByRole("table", { name: "Consultation records" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: record.patient_name })).toBeInTheDocument();
    expect(screen.getByText(record.primary_concern)).toBeInTheDocument();
    expect(screen.getByText(record.recommended_procedure)).toBeInTheDocument();
    expect(screen.getByText(record.status)).toBeInTheDocument();
  });

  it("shows a meaningful loading state", () => {
    renderScreen({
      list: vi.fn(() => new Promise<{ items: ConsultationRecord[] }>(() => undefined)),
    });

    expect(screen.getByRole("status")).toHaveTextContent("Loading consultation records");
  });

  it("shows a successful empty state", async () => {
    renderScreen({ list: vi.fn().mockResolvedValue({ items: [] }) });

    expect(await screen.findByText("No consultation records match your criteria.")).toBeInTheDocument();
  });

  it("shows a safe recoverable error state", async () => {
    renderScreen({ list: vi.fn().mockRejectedValue(new Error("private transport detail")) });

    expect(await screen.findByText("Consultation records could not be loaded. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText("private transport detail")).not.toBeInTheDocument();
  });

  it("forwards search criteria to the service", async () => {
    const list = vi.fn().mockResolvedValue({ items: [] });
    renderScreen({ list });

    await userEvent.type(screen.getByRole("textbox", { name: "Search consultations" }), "knee");

    await waitFor(() => expect(list).toHaveBeenLastCalledWith({ search: "knee", status: undefined }));
  });

  it.each(["PENDING", "BOOKED", "COMPLETED"] as const)("forwards the %s status", async (status) => {
    const list = vi.fn().mockResolvedValue({ items: [] });
    renderScreen({ list });

    await userEvent.click(screen.getByRole("combobox", { name: "Status" }));
    await userEvent.click(screen.getByRole("option", { name: status }));

    await waitFor(() => expect(list).toHaveBeenLastCalledWith({ search: "", status }));
  });

  it("forwards combined search and status criteria", async () => {
    const list = vi.fn().mockResolvedValue({ items: [] });
    renderScreen({ list });

    await userEvent.type(screen.getByRole("textbox", { name: "Search consultations" }), "knee");
    await userEvent.click(screen.getByRole("combobox", { name: "Status" }));
    await userEvent.click(screen.getByRole("option", { name: "BOOKED" }));

    await waitFor(() => expect(list).toHaveBeenLastCalledWith({ search: "knee", status: "BOOKED" }));
  });

  it("removes status criteria when All statuses is selected", async () => {
    const list = vi.fn().mockResolvedValue({ items: [] });
    renderScreen({ list });

    await userEvent.click(screen.getByRole("combobox", { name: "Status" }));
    await userEvent.click(screen.getByRole("option", { name: "PENDING" }));
    await userEvent.click(screen.getByRole("combobox", { name: "Status" }));
    await userEvent.click(screen.getByRole("option", { name: "All statuses" }));

    await waitFor(() => expect(list).toHaveBeenLastCalledWith({ search: "", status: undefined }));
  });

  it("navigates a selected record to its detail route", async () => {
    function CurrentLocation() {
      return <span>{useLocation().pathname}</span>;
    }
    const service = { list: vi.fn().mockResolvedValue({ items: [record] }) };
    render(
      <MemoryRouter initialEntries={["/consultations"]}>
        <Routes>
          <Route path="/consultations" element={<ConsultationRecordsScreen service={service} />} />
          <Route path="/consultations/:consultationId" element={<CurrentLocation />} />
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.click(await screen.findByRole("button", { name: record.patient_name }));

    expect(screen.getByText(`/consultations/${record.id}`)).toBeInTheDocument();
  });
});
