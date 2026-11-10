import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App, Dashboard } from "../src/app/App";
import type { Results } from "../src/shared/data/types";
import raw from "../public/data/results.json";

const results = raw as unknown as Results;
const ok = (body: unknown) => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) } as Response);
afterEach(cleanup);

describe("states", () => {
  it("shows a skeleton while loading", () => {
    render(<App fetcher={() => new Promise<Response>(() => {})} />);
    expect(screen.getByRole("status", { name: "Loading results" })).toBeTruthy();
  });
  it("explains a failure and retries", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce({ ok: false, status: 503 } as Response).mockImplementation(() => ok(results));
    render(<App fetcher={fetcher as unknown as (u: string) => Promise<Response>} />);
    expect((await screen.findByRole("alert")).textContent).toContain("503");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.getByRole("heading", { level: 1 })).toBeTruthy());
  });
  it("names the command when there are no results", () => {
    render(<Dashboard results={{ ...results, heldout: null, dev: { tenants: [], variants: {} } }} />);
    expect(screen.getByText(/make eval && make report/)).toBeTruthy();
  });
  it("names the command when there are no activations", () => {
    render(<Dashboard results={{ ...results, activation: [] }} />);
    expect(screen.getByText(/scripts\/activate.py/)).toBeTruthy();
  });
});

describe("content", () => {
  it("draws one bar per customer with its numbers", () => {
    render(<Dashboard results={results} />);
    const run = results.heldout ?? results.dev;
    expect(screen.getAllByRole("img").length).toBe(run.tenants.length);
    const a = run.variants["activated"].tenants[run.tenants[0]];
    expect(screen.getAllByText(new RegExp(`${(100 * a.auto_clear).toFixed(1)}%`)).length).toBeGreaterThan(0);
  });
  it("switches to the development months", () => {
    render(<Dashboard results={results} />);
    fireEvent.click(screen.getByRole("radio", { name: /Development/ }));
    expect(screen.getByText(/built and measured on/)).toBeTruthy();
  });
});
