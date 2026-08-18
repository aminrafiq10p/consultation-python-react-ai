import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppLayout } from "./AppLayout";

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

function renderLayout(pathname: string, desktop = true) {
  setViewport(desktop);
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="*" element={<><h1>Route content</h1><LocationProbe /></>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("AppLayout", () => {
  it("renders the branded desktop shell and ordered navigation", () => {
    renderLayout("/dashboard");
    expect(screen.getByText("Auvia Admin")).toBeInTheDocument();
    expect(screen.getByText("AI Consultation Platform")).toBeInTheDocument();
    const newConsult = screen.getByRole("link", { name: /new consult/i });
    expect(newConsult).toHaveAttribute("href", "/consultations/new");
    expect(newConsult).toBeEnabled();
    const navigation = screen.getByRole("navigation", { name: "Primary navigation" });
    const links = within(navigation).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["Dashboard", "Consultations"]);
    expect(links.map((link) => link.getAttribute("href"))).toEqual(["/dashboard", "/consultations"]);
    expect(screen.getByRole("main")).toContainElement(screen.getByRole("heading", { name: "Route content" }));
  });

  it.each([
    ["/dashboard", "Dashboard"], ["/consultations", "Consultations"],
    ["/consultations/new", "Consultations"],
    ["/consultations/id", "Consultations"], ["/consultations/id/summary", "Consultations"],
    ["/consultations/id/appointments/new", "Consultations"],
  ])("marks only the correct section current at %s", (pathname, activeLabel) => {
    renderLayout(pathname);
    expect(screen.getByRole("link", { name: activeLabel })).toHaveAttribute("aria-current", "page");
    const otherLabel = activeLabel === "Dashboard" ? "Consultations" : "Dashboard";
    expect(screen.getByRole("link", { name: otherLabel })).not.toHaveAttribute("aria-current");
  });

  it("does not select navigation for unrelated lookalike paths", () => {
    renderLayout("/consultations-archive");
    expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("link", { name: "Consultations" })).not.toHaveAttribute("aria-current");
  });

  it("opens mobile navigation and closes it after keyboard link activation", async () => {
    renderLayout("/dashboard", false);
    const user = userEvent.setup();
    expect(screen.queryByRole("navigation", { name: "Primary navigation" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    const navigation = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(navigation).toBeVisible();
    const consultations = within(navigation).getByRole("link", { name: "Consultations" });
    consultations.focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByLabelText("Current location")).toHaveTextContent("/consultations");
    await waitFor(() => expect(navigation).not.toBeVisible());
  });

  it("navigates to New Consultation from the desktop sidebar by keyboard", async () => {
    renderLayout("/dashboard");
    const user = userEvent.setup();
    const newConsult = screen.getByRole("link", { name: /new consult/i });

    newConsult.focus();
    await user.keyboard("{Enter}");

    expect(await screen.findByLabelText("Current location")).toHaveTextContent("/consultations/new");
    expect(screen.getByRole("link", { name: "Consultations" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("navigates to New Consultation from the mobile drawer and closes it", async () => {
    renderLayout("/dashboard", false);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    const navigation = screen.getByRole("navigation", { name: "Primary navigation" });
    const newConsult = screen.getByRole("link", { name: /new consult/i });

    newConsult.focus();
    await user.keyboard("{Enter}");

    expect(await screen.findByLabelText("Current location")).toHaveTextContent("/consultations/new");
    await waitFor(() => expect(navigation).not.toBeVisible());
  });
});
