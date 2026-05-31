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
  steps: "30",
};

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
        setSubmitError(
          detail ?? { message: `request failed: ${response.status}` },
        );
        return;
      }

      setSubmission(data as GenerationAccepted);
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

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">modal-img</p>
        <h1>Quality-first execution queue console</h1>
        <p className="lead">
          health 確認と Modal への enqueue を、同じ画面からそのまま試せる最小 UI。
          いまの MVP は execution_id の可視化までを対象にしています。
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
                name="prompt"
                onChange={handleFieldChange}
                rows={4}
                value={form.prompt}
              />
            </label>

            <label className="field field-full">
              <span>Negative prompt</span>
              <textarea
                name="negativePrompt"
                onChange={handleFieldChange}
                rows={3}
                value={form.negativePrompt}
              />
            </label>

            <label className="field">
              <span>Width</span>
              <input
                min="256"
                max="2048"
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
                min="256"
                max="2048"
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
                max="100"
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

          {submission === null && submitError === null ? (
            <p className="message message-muted">
              まず health を見て backend 接続を確認し、そのあと enqueue を送信して execution_id を確認してください。
            </p>
          ) : null}
        </article>
      </section>
    </main>
  );
}

export default App;
