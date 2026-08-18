import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ConsultationApiError } from "./consultationApi";
import {
  NewConsultationScreen,
  type NewConsultationService,
} from "./NewConsultationScreen";
import type { ConsultationRecord } from "./consultationTypes";

const consultation: ConsultationRecord = {
  id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  patient_name: "Amina Khan",
  primary_concern: "Persistent knee pain",
  recommended_procedure: "",
  status: "PENDING",
};

const serviceFor = (
  createConsultation = vi.fn().mockResolvedValue(consultation),
): NewConsultationService => ({ createConsultation });

function LocationProbe() {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output aria-label="Current location">{location.pathname}</output>
      <button onClick={() => navigate(-1)}>Back</button>
    </>
  );
}

const renderScreen = (
  service: NewConsultationService,
  entries = ["/consultations/new"],
  initialIndex?: number,
) => render(
  <MemoryRouter initialEntries={entries} initialIndex={initialIndex}>
    <LocationProbe />
    <Routes>
      <Route path="/consultations/new" element={<NewConsultationScreen service={service} />} />
      <Route path="/consultations" element={<span>Records destination</span>} />
      <Route path="/consultations/:consultationId" element={<span>Detail destination</span>} />
    </Routes>
  </MemoryRouter>,
);

async function fillValidForm() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText(/Patient name/), "  Amina Khan  ");
  await user.type(screen.getByLabelText(/Primary concern/), "  Persistent knee pain  ");
  return user;
}

describe("NewConsultationScreen", () => {
  it("renders the required semantic form without premature errors", () => {
    renderScreen(serviceFor());

    expect(screen.getByRole("heading", { name: "New Consultation" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Patient name/)).toBeRequired();
    expect(screen.getByLabelText(/Primary concern/)).toBeRequired();
    expect(screen.getByRole("button", { name: "Start Consultation" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeEnabled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("rejects blank and over-limit code-point values before calling the service and focuses the first invalid field", async () => {
    const createConsultation = vi.fn();
    renderScreen(serviceFor(createConsultation));
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/Patient name/), "   ");
    await user.type(screen.getByLabelText(/Primary concern/), "   ");
    await user.click(screen.getByRole("button", { name: "Start Consultation" }));
    expect(screen.getByText("Patient name is required.")).toBeInTheDocument();
    expect(screen.getByText("Primary concern is required.")).toBeInTheDocument();
    expect(screen.getByLabelText(/Patient name/)).toHaveFocus();
    expect(createConsultation).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText(/Patient name/), { target: { value: "😀".repeat(201) } });
    fireEvent.change(screen.getByLabelText(/Primary concern/), { target: { value: "x".repeat(4_001) } });
    await user.click(screen.getByRole("button", { name: "Start Consultation" }));
    expect(screen.getByText("Patient name must be 200 characters or fewer.")).toBeInTheDocument();
    expect(screen.getByText("Primary concern must be 4,000 characters or fewer.")).toBeInTheDocument();
    expect(createConsultation).not.toHaveBeenCalled();
  });

  it("submits normalized boundary-safe values exactly once from an Enter form submission", async () => {
    const createConsultation = vi.fn().mockResolvedValue(consultation);
    renderScreen(serviceFor(createConsultation));
    const user = userEvent.setup();
    fireEvent.change(screen.getByLabelText(/Primary concern/), {
      target: { value: "  Persistent knee pain  " },
    });
    await user.type(screen.getByLabelText(/Patient name/), "  Amina Khan  ");

    await user.keyboard("{Enter}");
    await waitFor(() => expect(createConsultation).toHaveBeenCalledOnce());
    expect(createConsultation).toHaveBeenCalledWith({
      patient_name: consultation.patient_name,
      primary_concern: consultation.primary_concern,
    });
    expect(screen.getByLabelText("Current location")).toHaveTextContent(`/consultations/${consultation.id}`);
  });

  it("accepts exact code-point limits", async () => {
    const boundaryRecord: ConsultationRecord = {
      ...consultation,
      patient_name: "😀".repeat(200),
      primary_concern: "x".repeat(4_000),
    };
    const createConsultation = vi.fn().mockResolvedValue(boundaryRecord);
    renderScreen(serviceFor(createConsultation));

    fireEvent.change(screen.getByLabelText(/Patient name/), {
      target: { value: boundaryRecord.patient_name },
    });
    fireEvent.change(screen.getByLabelText(/Primary concern/), {
      target: { value: boundaryRecord.primary_concern },
    });
    fireEvent.submit(screen.getByLabelText(/Patient name/).closest("form")!);

    await waitFor(() => expect(createConsultation).toHaveBeenCalledWith({
      patient_name: boundaryRecord.patient_name,
      primary_concern: boundaryRecord.primary_concern,
    }));
  });

  it("uses a synchronous guard while pending and disables all controls", async () => {
    let resolveCreation!: (record: ConsultationRecord) => void;
    const createConsultation = vi.fn(
      () => new Promise<ConsultationRecord>((resolve) => { resolveCreation = resolve; }),
    );
    renderScreen(serviceFor(createConsultation), ["/consultations", "/consultations/new"], 1);
    const user = await fillValidForm();
    const form = screen.getByLabelText(/Patient name/).closest("form")!;

    fireEvent.submit(form);
    fireEvent.submit(form);
    expect(createConsultation).toHaveBeenCalledOnce();
    expect(screen.getByText("Starting consultation…")).toBeInTheDocument();
    expect(screen.getByLabelText(/Patient name/)).toBeDisabled();
    expect(screen.getByLabelText(/Primary concern/)).toBeDisabled();
    expect(screen.getByRole("button", { name: "Starting Consultation…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();

    resolveCreation(consultation);
    await waitFor(() => expect(screen.getByLabelText("Current location")).toHaveTextContent(`/consultations/${consultation.id}`));
    await user.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByLabelText("Current location")).toHaveTextContent("/consultations");
  });

  it("retains normalized values and permits an explicit retry after each safe failure", async () => {
    const createConsultation = vi
      .fn()
      .mockRejectedValueOnce(new ConsultationApiError("creation-validation"))
      .mockRejectedValueOnce(new Error("network detail"))
      .mockResolvedValueOnce(consultation);
    renderScreen(serviceFor(createConsultation));
    const user = await fillValidForm();
    const start = screen.getByRole("button", { name: "Start Consultation" });

    await user.click(start);
    expect(await screen.findByText(/could not be accepted/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Patient name/)).toHaveValue(consultation.patient_name);
    expect(screen.getByLabelText(/Primary concern/)).toHaveValue(consultation.primary_concern);
    expect(start).toBeEnabled();

    await user.click(start);
    expect(await screen.findByText(/Creation could not be confirmed/)).toBeInTheDocument();
    expect(screen.queryByText("network detail")).not.toBeInTheDocument();
    expect(start).toBeEnabled();

    await user.click(start);
    await waitFor(() => expect(createConsultation).toHaveBeenCalledTimes(3));
    expect(screen.getByLabelText("Current location")).toHaveTextContent(`/consultations/${consultation.id}`);
  });

  it("cancels to consultation records without creating a consultation", async () => {
    const createConsultation = vi.fn();
    renderScreen(serviceFor(createConsultation));
    const user = await fillValidForm();
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(createConsultation).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Current location")).toHaveTextContent("/consultations");
  });
});
