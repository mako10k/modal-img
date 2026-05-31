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
pip install -e .[dev]
pytest
modal deploy modal_worker.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

PostgreSQL を使う前に sql/init_generation_jobs.sql を適用して generation_jobs テーブルを作成する。
既存の generation_jobs テーブルが旧スキーマの場合は sql/upgrade_generation_jobs.sql を追加で適用し、`workflow_id` から `comfyui_prompt_id` への移行、不足カラムの追加、`comfyui_prompt_id` の nullable 化、旧 `accepted` 状態の `queued` への正規化を行う。現在の upgrade では結果 preview 保存用の列も追加する。

backend 設定は backend/.env.example の環境変数名に合わせる。

Modal 実行設定が生成受付の正本で、ComfyUI 関連設定は移行中の legacy 互換として残している。現行の Modal-backed 経路で backend の workflow payload 形状に直接効くのは checkpoint と output prefix だけで、base URL や timeout 系は旧 direct ComfyUI helper 用の残置設定になる。
新規の生成系作業や運用手順は、raw ComfyUI 常駐を前提に組まず、Modal 実行境界へ寄せる移行前提で進める。
ローカルで `POST /v1/generations` を成功させるには、uvicorn 起動前に `modal deploy modal_worker.py` で worker function を deploy しておく必要がある。

- MODAL_IMG_APP_ENV: 実行環境名
- MODAL_IMG_MODAL_APP_NAME: 生成実行を委譲する Modal app 名
- MODAL_IMG_MODAL_TEXT_TO_IMAGE_FUNCTION_NAME: 生成実行を受ける Modal function 名
- MODAL_IMG_MODAL_ENVIRONMENT_NAME: 必要なときだけ明示する Modal environment 名
- MODAL_IMG_REDIS_URL: Redis 接続先
- MODAL_IMG_POSTGRES_DSN: PostgreSQL 接続先
- MODAL_IMG_POSTGRES_CONNECT_TIMEOUT_SECONDS: PostgreSQL 接続 timeout 秒
- MODAL_IMG_REDIS_TIMEOUT_SECONDS: Redis 接続 / 読み書き timeout 秒
- MODAL_IMG_GENERATION_QUEUE_KEY: Redis のジョブ通知キュー名
- MODAL_IMG_COMFYUI_BASE_URL: 旧 direct ComfyUI helper 互換のために残している ComfyUI API の base URL
- MODAL_IMG_COMFYUI_TIMEOUT_SECONDS: 旧 direct ComfyUI helper 互換のために残している timeout 秒
- MODAL_IMG_COMFYUI_HEALTH_TIMEOUT_SECONDS: 旧 direct ComfyUI health 実装の名残として残る移行用 timeout 秒
- MODAL_IMG_DEPENDENCY_HEALTH_TIMEOUT_SECONDS: health endpoint の各依存 probe に掛ける timeout 秒
- MODAL_IMG_COMFYUI_CHECKPOINT: backend の workflow payload 互換でのみ使う checkpoint 名
- MODAL_IMG_COMFYUI_OUTPUT_PREFIX: backend の workflow payload 互換でのみ使う保存 prefix
- MODAL_IMG_FRONTEND_ORIGIN: frontend の公開 origin

health endpoint は Redis の `PING`、PostgreSQL の `SELECT 1`、Modal 実行 function の hydrate による deploy 済み解決確認を行い、依存状態を返す。
ローカルで依存サービスが起動していない場合は `degraded` を返す前提とする。

生成 API の入口は `POST /v1/generations` で、Modal worker の `submit_text_to_image` function に workflow を `spawn` し、受け付け直後の `execution_id` を返す。
永続化は PostgreSQL を正本、Redis を通知経路として扱い、状態は `submitting -> queued / submission_failed / queue_publish_failed` で管理する。
queued への状態更新自体が失敗した場合は、job を `submitting` のまま残しつつ内部 execution 識別子と error detail を保持して 502 を返す。
API の error detail では `persistence_failed` / `submission_failed` / `queue_publish_failed` / `queue_state_update_failed` を返し、`queue_state_update_failed` は永続化状態ではなく API 側の失敗分類として扱う。
API 応答では外部実行系の識別子を `execution_id` として返す。内部永続化では互換のため `comfyui_prompt_id` カラムを当面流用している。
backend は `MODAL_IMG_FRONTEND_ORIGIN` を CORS 許可 origin として使う。

`GET /v1/generations/{job_id}` は execution_id から Modal function call の結果を取得し、完了時は preview 画像を PostgreSQL に保存して返す。

現行 worker は Modal 上で GPU を使って `stabilityai/stable-diffusion-xl-base-1.0` による text-to-image 推論を行い、PNG data URL を返す。これは最終構成ではないが、go / no-go 判断に使える 1 枚の品質を優先するための現行デモ実装である。
`prompt` は 1-2000 文字、`negative_prompt` は 0-2000 文字で受け付ける。
現行の GPU デモ worker は `width` / `height` を 512-1024 かつ 64 の倍数、`steps` を 12-30 の範囲で受け付ける。既定値は 768x768 / 24 steps で、単なる高速性よりも 1 枚の説得力を優先する。

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
