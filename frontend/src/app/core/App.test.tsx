import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App consultation routes", () => {
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
