import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import Recommendations from "./Recommendations";

describe("Recommendations page", () => {
  it("renders the page heading", () => {
    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>
    );
    expect(
      screen.getByText("Covered Call Recommendations")
    ).toBeInTheDocument();
  });

  it("renders the symbol input and submit button", () => {
    render(
      <MemoryRouter>
        <Recommendations />
      </MemoryRouter>
    );
    expect(screen.getByPlaceholderText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("Get Recommendations")).toBeInTheDocument();
  });
});
