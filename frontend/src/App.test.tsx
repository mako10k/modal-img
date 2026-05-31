import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";


describe("App", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("renders dependency health after the initial check", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "degraded",
        environment: "development",
        dependencies: {
          redis: "ok",
          postgres: "error:TimeoutError",
          modal: "error:TimeoutError",
        },
      }),
    }) as typeof fetch;

    render(<App />);

    await screen.findByText("degraded");
    expect(screen.getByText("development")).toBeInTheDocument();
    expect(screen.getByText("redis")).toBeInTheDocument();

    const dependencyErrors = await screen.findAllByText("error:TimeoutError");
    expect(dependencyErrors).toHaveLength(2);
  });

  it("shows structured generation errors from the backend", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "degraded",
          environment: "development",
          dependencies: {
            redis: "ok",
            postgres: "error:TimeoutError",
            modal: "error:TimeoutError",
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({
          detail: {
            job_id: "job-1",
            status: "persistence_failed",
            message: "ConnectionTimeout: connection timeout expired",
          },
        }),
      }) as typeof fetch;

    render(<App />);

    await screen.findByText("degraded");
    fireEvent.click(
      screen.getByRole("button", { name: "生成依頼を送信" }),
    );

    await screen.findByText("persistence_failed");
    expect(screen.getByText("job-1")).toBeInTheDocument();
    expect(
      screen.getByText("ConnectionTimeout: connection timeout expired"),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    });
  });

  it("shows queued modal execution ids from the backend", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "ok",
          environment: "development",
          dependencies: {
            redis: "ok",
            postgres: "ok",
            modal: "ok",
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: "job-2",
          status: "queued",
          execution_id: "fc-123",
        }),
      }) as typeof fetch;

    render(<App />);

    await screen.findByText("development");
    fireEvent.click(
      screen.getByRole("button", { name: "生成依頼を送信" }),
    );

    await screen.findByText("queued");
    expect(screen.getByText("job-2")).toBeInTheDocument();
    expect(screen.getByText("fc-123")).toBeInTheDocument();
  });
});