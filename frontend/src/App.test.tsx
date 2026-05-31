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
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: "job-2",
          status: "completed",
          execution_id: "fc-123",
          error_message: null,
          result_image_data_url: "data:image/png;base64,abc",
          result_mime_type: "image/png",
        }),
      }) as typeof fetch;

    render(<App />);

    await screen.findByText("development");
    fireEvent.click(
      screen.getByRole("button", { name: "生成依頼を送信" }),
    );

    await screen.findByText("completed");
    expect(screen.getByText("job-2")).toBeInTheDocument();
    expect(screen.getAllByText("fc-123")).toHaveLength(2);
    expect(screen.getByAltText("Generated preview")).toBeInTheDocument();
  });

  it("renders quality-first defaults in the generation form", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
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
    }) as typeof fetch;

    render(<App />);

    await screen.findByText("development");
    expect(screen.getByLabelText("Width")).toHaveValue(768);
    expect(screen.getByLabelText("Height")).toHaveValue(768);
    expect(screen.getByLabelText("Steps")).toHaveValue(24);
    expect(screen.getByLabelText("Prompt")).toHaveValue(
      "cinematic editorial portrait, natural skin texture, moody practical lighting, 85mm lens, shallow depth of field, highly detailed, photorealistic",
    );
    expect(screen.getByText(/steps は 12-30/)).toBeInTheDocument();
  });

  it("keeps tracking queue publish failures that already spawned a job", async () => {
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
        ok: false,
        json: async () => ({
          detail: {
            job_id: "job-3",
            status: "queue_publish_failed",
            message: "RuntimeError: redis push failed",
            execution_id: "fc-queue-1",
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: "job-3",
          status: "completed",
          execution_id: "fc-queue-1",
          error_message: null,
          result_image_data_url: "data:image/png;base64,abc",
          result_mime_type: "image/png",
        }),
      }) as typeof fetch;

    render(<App />);

    await screen.findByText("development");
    fireEvent.click(
      screen.getByRole("button", { name: "生成依頼を送信" }),
    );

    await screen.findByText("completed");
    expect(screen.getAllByText("fc-queue-1")).toHaveLength(2);
    expect(screen.getByAltText("Generated preview")).toBeInTheDocument();
  });

  it("keeps tracking queue state update failures that already spawned a job", async () => {
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
        ok: false,
        json: async () => ({
          detail: {
            job_id: "job-4",
            status: "queue_state_update_failed",
            message: "RuntimeError: postgres update failed",
            execution_id: "fc-state-1",
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: "job-4",
          status: "completed",
          execution_id: "fc-state-1",
          error_message: null,
          result_image_data_url: "data:image/png;base64,abc",
          result_mime_type: "image/png",
        }),
      }) as typeof fetch;

    render(<App />);

    await screen.findByText("development");
    fireEvent.click(
      screen.getByRole("button", { name: "生成依頼を送信" }),
    );

    await screen.findByText("completed");
    expect(screen.getAllByText("fc-state-1")).toHaveLength(2);
    expect(screen.getByAltText("Generated preview")).toBeInTheDocument();
  });
});