# modal-img

品質優先で構築する画像生成サービスの開発用リポジトリ。

## 現在のスコープ

- FastAPI の最小 API を提供する
- Modal から FastAPI を公開できる入口を持つ
- React + Vite の最小画面を提供する
- backend テストと frontend build を開発の最低ラインにする

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

### frontend

```bash
cd frontend
npm install
npm run build
```
