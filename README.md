# modal-img

品質優先で構築する画像生成サービスの開発用リポジトリ。

## 現在のスコープ

- FastAPI の最小 API を提供する
- Modal から FastAPI を公開できる入口を持つ
- React + Vite の最小画面を提供する
- backend テストと frontend build を開発の最低ラインにする
- 軽量環境では frontend を静的配信前提で運用する

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
```

backend 設定は backend/.env.example の環境変数名に合わせる。

- MODAL_IMG_APP_ENV: 実行環境名
- MODAL_IMG_REDIS_URL: Redis 接続先
- MODAL_IMG_POSTGRES_DSN: PostgreSQL 接続先
- MODAL_IMG_FRONTEND_ORIGIN: frontend の公開 origin
- MODAL_IMG_FRONTEND_MODE: lightweight 環境では static を使う

### frontend

```bash
cd frontend
npm install
npm run build
npm run serve:lite
```

軽量環境では dev server 常駐ではなく、build 済みアセットを vite preview で配信する前提とする。
