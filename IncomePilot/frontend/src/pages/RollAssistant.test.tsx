import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import RollAssistant from "./RollAssistant";

describe("RollAssistant page", () => {
  it("renders the page heading", () => {
    render(
      <MemoryRouter>
        <RollAssistant />
      </MemoryRouter>
    );
    expect(screen.getByText("Roll Assistant")).toBeInTheDocument();
  });

  it("renders the evaluate button", () => {
    render(
      <MemoryRouter>
        <RollAssistant />
      </MemoryRouter>
    );
    expect(screen.getByText("Evaluate")).toBeInTheDocument();
  });
});
