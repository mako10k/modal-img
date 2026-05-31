# modal-img

品質優先で構築する画像生成サービスの開発用リポジトリ。

## 現在のスコープ

- FastAPI の最小 API を提供する
- Modal から FastAPI を公開できる入口を持つ
- React + Vite の最小画面を提供する
- backend テストと frontend build を開発の最低ラインにする
- 軽量環境では frontend を静的配信前提で運用する
- Redis / PostgreSQL の接続ファクトリと依存ヘルスチェックを提供する
- ComfyUI 連携の API 入口と workflow 境界を提供する
- ジョブ永続化の repository / queue publisher 境界を提供する
- PostgreSQL job insert と Redis 通知の実クライアントを提供する
- ComfyUI `/prompt` 送信と submission state transition を提供する

## ディレクトリ構成

- backend: FastAPI と Modal の最小構成
- frontend: React + Vite の最小構成
- docs: 状態管理とバックログ

## ローカル開発

### backend

```bash
cd backend
python3.12 -m venv ../.venv
. ../.venv/bin/activate
pip install -e .[dev,modal]
pytest
```

PostgreSQL を使う前に sql/init_generation_jobs.sql を適用して generation_jobs テーブルを作成する。
既存の generation_jobs テーブルが旧スキーマの場合は sql/upgrade_generation_jobs.sql を追加で適用し、`workflow_id` から `comfyui_prompt_id` への移行、不足カラムの追加、`comfyui_prompt_id` の nullable 化、旧 `accepted` 状態の `queued` への正規化を行う。

backend 設定は backend/.env.example の環境変数名に合わせる。

- MODAL_IMG_APP_ENV: 実行環境名
- MODAL_IMG_REDIS_URL: Redis 接続先
- MODAL_IMG_POSTGRES_DSN: PostgreSQL 接続先
- MODAL_IMG_GENERATION_QUEUE_KEY: Redis のジョブ通知キュー名
- MODAL_IMG_COMFYUI_BASE_URL: ComfyUI API の base URL
- MODAL_IMG_COMFYUI_TIMEOUT_SECONDS: ComfyUI API 呼び出し timeout 秒
- MODAL_IMG_COMFYUI_CHECKPOINT: 生成に使う checkpoint 名
- MODAL_IMG_COMFYUI_OUTPUT_PREFIX: ComfyUI 保存画像の prefix
- MODAL_IMG_FRONTEND_ORIGIN: frontend の公開 origin

health endpoint は Redis の `PING`、PostgreSQL の `SELECT 1`、ComfyUI の `/system_stats` を実行し、依存状態を返す。
ローカルで依存サービスが起動していない場合は `degraded` を返す前提とする。

生成 API の入口は `POST /v1/generations` で、現在は ComfyUI `/prompt` に workflow を送信する。
永続化は PostgreSQL を正本、Redis を通知経路として扱い、状態は `submitting -> queued / submission_failed / queue_publish_failed` で管理する。
queued への状態更新自体が失敗した場合は、job を `submitting` のまま残しつつ `comfyui_prompt_id` と error detail を保持して 502 を返す。
API の error detail では `submission_failed` / `queue_publish_failed` / `queue_state_update_failed` を返し、`queue_state_update_failed` は永続化状態ではなく API 側の失敗分類として扱う。
外部実行系の識別子は `workflow_id` ではなく `comfyui_prompt_id` として扱う。
backend は `MODAL_IMG_FRONTEND_ORIGIN` を CORS 許可 origin として使う。

### frontend

```bash
cd frontend
npm install
npm run build
npm run serve:lite
```

軽量環境では dev server 常駐ではなく、build 済みアセットを vite preview で配信する前提とする。
