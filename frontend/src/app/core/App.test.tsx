import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App consultation routes", () => {
  it("registers the appointment navigation placeholder without an appointment form", () => {
    render(
      <MemoryRouter initialEntries={[
        "/consultations/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/appointments/new?recommendation_id=11111111-1111-4111-8111-111111111111",
      ]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Appointment" })).toBeInTheDocument();
    expect(screen.getByText(/Appointment setup is not available yet/)).toBeInTheDocument();
    expect(screen.queryByRole("form")).not.toBeInTheDocument();
  });
});
