# modal-img

品質優先で構築する画像生成サービスの開発用リポジトリ。

## 方向性の訂正

- 正本のアーキテクチャでは、画像生成の実行責務は Modal 側に置く
- FastAPI backend は受付、状態管理、永続化、参照 API の境界として扱う
- ComfyUI を採用する場合も、backend 直結の外部実行先として固定するのではなく、Modal 実行側の内部実装として閉じ込める
- 現在の codebase には backend から raw ComfyUI endpoint を呼ぶ暫定実装が残っているが、これは方向性の drift であり、今後の正当な拡張先ではない
- 生成系の新規作業では、現実装ではなくこの節を優先する

## 現在のスコープ

- FastAPI の最小 API を提供する
- Modal から FastAPI を公開できる入口を持つ
- React + Vite の最小画面を提供する
- React + Vite の UI から health 確認と生成依頼送信を試せる
- backend テストと frontend build を開発の最低ラインにする
- 軽量環境では frontend を静的配信前提で運用する
- Redis / PostgreSQL の接続ファクトリと依存ヘルスチェックを提供する
- Modal 実行境界へ寄せるための生成 API 入口と workflow 境界を整理する
- ジョブ永続化の repository / queue publisher 境界を提供する
- PostgreSQL job insert と Redis 通知の実クライアントを提供する
- 暫定の direct ComfyUI 実装 drift を、Modal 主導の実行境界へ収束させる

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
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

PostgreSQL を使う前に sql/init_generation_jobs.sql を適用して generation_jobs テーブルを作成する。
既存の generation_jobs テーブルが旧スキーマの場合は sql/upgrade_generation_jobs.sql を追加で適用し、`workflow_id` から `comfyui_prompt_id` への移行、不足カラムの追加、`comfyui_prompt_id` の nullable 化、旧 `accepted` 状態の `queued` への正規化を行う。

backend 設定は backend/.env.example の環境変数名に合わせる。

ComfyUI 関連設定は、現行コードに残っている暫定実装を扱うための移行用設定であり、backend 正本の外部依存として固定する意図ではない。
新規の生成系作業や運用手順は、raw ComfyUI 常駐を前提に組まず、Modal 実行境界へ寄せる移行前提で進める。

- MODAL_IMG_APP_ENV: 実行環境名
- MODAL_IMG_REDIS_URL: Redis 接続先
- MODAL_IMG_POSTGRES_DSN: PostgreSQL 接続先
- MODAL_IMG_POSTGRES_CONNECT_TIMEOUT_SECONDS: PostgreSQL 接続 timeout 秒
- MODAL_IMG_REDIS_TIMEOUT_SECONDS: Redis 接続 / 読み書き timeout 秒
- MODAL_IMG_GENERATION_QUEUE_KEY: Redis のジョブ通知キュー名
- MODAL_IMG_COMFYUI_BASE_URL: 暫定実装でのみ使う ComfyUI API の base URL
- MODAL_IMG_COMFYUI_TIMEOUT_SECONDS: 暫定実装でのみ使う ComfyUI API 呼び出し timeout 秒
- MODAL_IMG_COMFYUI_HEALTH_TIMEOUT_SECONDS: 暫定実装でのみ使う ComfyUI health probe の timeout 秒
- MODAL_IMG_DEPENDENCY_HEALTH_TIMEOUT_SECONDS: health endpoint の各依存 probe に掛ける timeout 秒
- MODAL_IMG_COMFYUI_CHECKPOINT: 暫定実装でのみ使う checkpoint 名
- MODAL_IMG_COMFYUI_OUTPUT_PREFIX: 暫定実装でのみ使う ComfyUI 保存画像の prefix
- MODAL_IMG_FRONTEND_ORIGIN: frontend の公開 origin

health endpoint は Redis の `PING`、PostgreSQL の `SELECT 1`、暫定実装では ComfyUI の `/system_stats` を実行し、依存状態を返す。
この ComfyUI probe は移行対象であり、将来方針として維持する前提ではない。
ローカルで依存サービスが起動していない場合は `degraded` を返す前提とする。

生成 API の入口は `POST /v1/generations` で、現状実装では ComfyUI `/prompt` に workflow を送信しているが、これは Modal が生成実行責務を持つ最終形ではない。
永続化は PostgreSQL を正本、Redis を通知経路として扱い、状態は `submitting -> queued / submission_failed / queue_publish_failed` で管理する。
queued への状態更新自体が失敗した場合は、job を `submitting` のまま残しつつ `comfyui_prompt_id` と error detail を保持して 502 を返す。
API の error detail では `persistence_failed` / `submission_failed` / `queue_publish_failed` / `queue_state_update_failed` を返し、`queue_state_update_failed` は永続化状態ではなく API 側の失敗分類として扱う。
現在の暫定実装では外部実行系の識別子を `workflow_id` ではなく `comfyui_prompt_id` として扱うが、これも Modal 主導の抽象識別子へ寄せる移行対象である。
backend は `MODAL_IMG_FRONTEND_ORIGIN` を CORS 許可 origin として使う。

### frontend

```bash
cd frontend
npm install
npm test
npm run build
npm run serve:lite
```

frontend 設定は frontend/.env.example を基準にし、既定では `VITE_API_BASE_URL=http://127.0.0.1:8000` を使う。
軽量環境では dev server 常駐ではなく、build 済みアセットを vite preview で配信する前提とする。
frontend の既定ポートは `http://127.0.0.1:43173` とし、backend の `MODAL_IMG_FRONTEND_ORIGIN` もこれに合わせる。
