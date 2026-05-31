import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

type HealthResponse = {
  status: string;
  environment: string;
  dependencies: Record<string, string>;
};

type GenerationAccepted = {
  job_id: string;
  status: string;
  execution_id: string;
};

type GenerationStatus = {
  job_id: string;
  status: string;
  execution_id: string | null;
  error_message: string | null;
  result_image_data_url: string | null;
  result_mime_type: string | null;
};

type FailureDetail = {
  job_id?: string;
  status?: string;
  message?: string;
  execution_id?: string;
};

type ErrorResponse = {
  detail?: FailureDetail;
};

type GenerationForm = {
  prompt: string;
  negativePrompt: string;
  width: string;
  height: string;
  steps: string;
};

const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const INITIAL_FORM: GenerationForm = {
  prompt: "high detail portrait, cinematic lighting, natural skin texture",
  negativePrompt: "blurry, low contrast, malformed hands",
  width: "1024",
  height: "1024",
  steps: "4",
};

const TERMINAL_JOB_STATUSES = new Set([
  "completed",
  "execution_failed",
  "submission_failed",
]);

function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/$/, "");
}

function formatTimestamp(value: string | null): string {
  if (value === null) {
    return "未実行";
  }

  return new Date(value).toLocaleString("ja-JP", {
    hour12: false,
  });
}

function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [lastHealthCheckAt, setLastHealthCheckAt] = useState<string | null>(
    null,
  );
  const [form, setForm] = useState(INITIAL_FORM);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submission, setSubmission] = useState<GenerationAccepted | null>(null);
  const [submitError, setSubmitError] = useState<FailureDetail | null>(null);
  const [generationStatus, setGenerationStatus] =
    useState<GenerationStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);

  const normalizedApiBaseUrl = useMemo(
    () => normalizeBaseUrl(apiBaseUrl),
    [apiBaseUrl],
  );

  async function refreshHealth() {
    setHealthLoading(true);
    setHealthError(null);

    try {
      const response = await fetch(`${normalizedApiBaseUrl}/health`);
      if (!response.ok) {
        throw new Error(`health request failed: ${response.status}`);
      }

      const data = (await response.json()) as HealthResponse;
      setHealth(data);
      setLastHealthCheckAt(new Date().toISOString());
    } catch (error) {
      setHealth(null);
      setHealthError(
        error instanceof Error
          ? error.message
          : "health request failed unexpectedly",
      );
      setLastHealthCheckAt(new Date().toISOString());
    } finally {
      setHealthLoading(false);
    }
  }

  useEffect(() => {
    void refreshHealth();
  }, []);

  useEffect(() => {
    if (submission === null) {
      return;
    }

    if (
      generationStatus !== null &&
      TERMINAL_JOB_STATUSES.has(generationStatus.status)
    ) {
      return;
    }

    const timer = window.setTimeout(() => {
      void refreshGenerationStatus(submission.job_id);
    }, 2500);

    return () => {
      window.clearTimeout(timer);
    };
  }, [generationStatus?.status, submission, normalizedApiBaseUrl]);

  function handleFieldChange(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitLoading(true);
    setSubmission(null);
    setSubmitError(null);
    setGenerationStatus(null);
    setStatusError(null);

    const payload = {
      prompt: form.prompt,
      negative_prompt: form.negativePrompt || null,
      width: Number(form.width),
      height: Number(form.height),
      steps: Number(form.steps),
    };

    try {
      const response = await fetch(`${normalizedApiBaseUrl}/v1/generations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const data = (await response.json()) as GenerationAccepted | ErrorResponse;

      if (!response.ok) {
        const detail = "detail" in data ? data.detail : undefined;
        if (
          (detail?.status === "queue_publish_failed" ||
            detail?.status === "queue_state_update_failed") &&
          detail.job_id &&
          detail.execution_id
        ) {
          setSubmission({
            job_id: detail.job_id,
            status: detail.status,
            execution_id: detail.execution_id,
          });
          setGenerationStatus({
            job_id: detail.job_id,
            status: detail.status,
            execution_id: detail.execution_id,
            error_message: detail.message ?? null,
            result_image_data_url: null,
            result_mime_type: null,
          });
          void refreshGenerationStatus(detail.job_id);
        }
        setSubmitError(
          detail ?? { message: `request failed: ${response.status}` },
        );
        return;
      }

      const accepted = data as GenerationAccepted;
      setSubmission(accepted);
      setGenerationStatus({
        job_id: accepted.job_id,
        status: accepted.status,
        execution_id: accepted.execution_id,
        error_message: null,
        result_image_data_url: null,
        result_mime_type: null,
      });
      void refreshGenerationStatus(accepted.job_id);
    } catch (error) {
      setSubmitError({
        message:
          error instanceof Error
            ? error.message
            : "generation request failed unexpectedly",
      });
    } finally {
      setSubmitLoading(false);
    }
  }

  async function refreshGenerationStatus(jobId: string) {
    setStatusError(null);

    try {
      const response = await fetch(
        `${normalizedApiBaseUrl}/v1/generations/${jobId}`,
      );
      if (!response.ok) {
        throw new Error(`status request failed: ${response.status}`);
      }

      const data = (await response.json()) as GenerationStatus;
      setGenerationStatus(data);
      if (data.status === "completed") {
        setSubmitError(null);
      }
    } catch (error) {
      setStatusError(
        error instanceof Error
          ? error.message
          : "status request failed unexpectedly",
      );
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">modal-img</p>
        <h1>Quality-first execution queue console</h1>
        <p className="lead">
          health 確認、生成依頼、結果確認までを同じ画面で追える開発 UI。
          Modal 側の実行結果が返れば、そのまま preview まで確認できます。
        </p>
        <div className="hero-strip">
          <span>Backend: FastAPI / Modal</span>
          <span>Queue: Redis / PostgreSQL</span>
          <span>Execution: Modal</span>
        </div>
      </section>

      <section className="workspace">
        <article className="card card-accent">
          <div className="card-header">
            <div>
              <p className="section-label">Connection</p>
              <h2>API endpoint</h2>
            </div>
            <button
              className="ghost-button"
              onClick={() => {
                void refreshHealth();
              }}
              type="button"
            >
              {healthLoading ? "確認中..." : "health 再取得"}
            </button>
          </div>

          <label className="field">
            <span>Backend base URL</span>
            <input
              name="apiBaseUrl"
              onChange={(event) => setApiBaseUrl(event.target.value)}
              placeholder="http://127.0.0.1:8000"
              value={apiBaseUrl}
            />
          </label>

          <div className="status-grid">
            <div className="status-panel">
              <span className="status-label">health</span>
              <strong>
                {health?.status ?? (healthError === null ? "unknown" : "unreachable")}
              </strong>
            </div>
            <div className="status-panel">
              <span className="status-label">environment</span>
              <strong>{health?.environment ?? "-"}</strong>
            </div>
            <div className="status-panel">
              <span className="status-label">last check</span>
              <strong>{formatTimestamp(lastHealthCheckAt)}</strong>
            </div>
          </div>

          {healthError !== null ? (
            <p className="message message-error">
              接続失敗: {healthError}
            </p>
          ) : null}

          <div className="dependency-list">
            {health === null ? (
              <p className="dependency-empty">
                health response がまだありません。
              </p>
            ) : (
              Object.entries(health.dependencies).map(([name, status]) => (
                <div className="dependency-item" key={name}>
                  <span>{name}</span>
                  <span
                    className={status === "ok" ? "pill pill-ok" : "pill pill-warn"}
                  >
                    {status}
                  </span>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="card">
          <div className="card-header">
            <div>
              <p className="section-label">Generate</p>
              <h2>Text-to-image enqueue request</h2>
            </div>
          </div>

          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="field field-full">
              <span>Prompt</span>
              <textarea
                maxLength={2000}
                name="prompt"
                onChange={handleFieldChange}
                rows={4}
                value={form.prompt}
              />
            </label>

            <label className="field field-full">
              <span>Negative prompt</span>
              <textarea
                maxLength={2000}
                name="negativePrompt"
                onChange={handleFieldChange}
                rows={3}
                value={form.negativePrompt}
              />
            </label>

            <label className="field">
              <span>Width</span>
              <input
                min="512"
                max="1024"
                name="width"
                onChange={handleFieldChange}
                step="64"
                type="number"
                value={form.width}
              />
            </label>

            <label className="field">
              <span>Height</span>
              <input
                min="512"
                max="1024"
                name="height"
                onChange={handleFieldChange}
                step="64"
                type="number"
                value={form.height}
              />
            </label>

            <label className="field">
              <span>Steps</span>
              <input
                min="1"
                max="4"
                name="steps"
                onChange={handleFieldChange}
                type="number"
                value={form.steps}
              />
            </label>

            <div className="field field-actions">
              <button className="primary-button" disabled={submitLoading} type="submit">
                {submitLoading ? "送信中..." : "生成依頼を送信"}
              </button>
            </div>

            <p className="message message-muted field-full">
              prompt は 2000 文字まで、width / height は 512-1024 かつ 64 の倍数、steps は 1-4 です。
            </p>
          </form>
        </article>

        <article className="card card-result">
          <div className="card-header">
            <div>
              <p className="section-label">Result</p>
              <h2>Latest API response</h2>
            </div>
          </div>

          {submission !== null ? (
            <div className="result-block result-success">
              <div className="result-row">
                <span>status</span>
                <strong>{submission.status}</strong>
              </div>
              <div className="result-row">
                <span>job_id</span>
                <code>{submission.job_id}</code>
              </div>
              <div className="result-row">
                <span>execution_id</span>
                <code>{submission.execution_id}</code>
              </div>
            </div>
          ) : null}

          {generationStatus !== null ? (
            <div className="result-block result-status">
              <div className="result-row">
                <span>job status</span>
                <strong>{generationStatus.status}</strong>
              </div>
              {generationStatus.execution_id ? (
                <div className="result-row">
                  <span>resolved execution_id</span>
                  <code>{generationStatus.execution_id}</code>
                </div>
              ) : null}
              {generationStatus.error_message ? (
                <p className="message message-error">
                  {generationStatus.error_message}
                </p>
              ) : null}
              {generationStatus.result_image_data_url ? (
                <div className="preview-frame">
                  <img
                    alt="Generated preview"
                    className="preview-image"
                    src={generationStatus.result_image_data_url}
                  />
                </div>
              ) : (
                <p className="message message-muted">
                  {TERMINAL_JOB_STATUSES.has(generationStatus.status)
                    ? "この job は画像 preview なしで終端状態に到達しました。"
                    : "生成結果を確認中です。job status をポーリングしています。"}
                </p>
              )}
            </div>
          ) : null}

          {submitError !== null ? (
            <div className="result-block result-error">
              <div className="result-row">
                <span>status</span>
                <strong>{submitError.status ?? "request_failed"}</strong>
              </div>
              {submitError.job_id ? (
                <div className="result-row">
                  <span>job_id</span>
                  <code>{submitError.job_id}</code>
                </div>
              ) : null}
              {submitError.execution_id ? (
                <div className="result-row">
                  <span>execution_id</span>
                  <code>{submitError.execution_id}</code>
                </div>
              ) : null}
              <p className="message message-error">
                {submitError.message ?? "unknown error"}
              </p>
            </div>
          ) : null}

          {statusError !== null ? (
            <p className="message message-error">
              status 取得失敗: {statusError}
            </p>
          ) : null}

          {submission === null && submitError === null && generationStatus === null ? (
            <p className="message message-muted">
              まず health を見て backend 接続を確認し、そのあと生成依頼を送信して execution_id と preview を確認してください。
            </p>
          ) : null}
        </article>
      </section>
    </main>
  );
}

export default App;
