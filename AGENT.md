# AGENT

このリポジトリでは高品質画像生成サービスの構築を目的とする。

## 優先順位

1. 品質
2. 保守性
3. 生成速度

## 技術スタック

- Backend: Python 3.12, FastAPI, Modal, ComfyUI, Redis, PostgreSQL
- Frontend: React, TypeScript, Vite

## 作業ルール

- 作業前に docs/status.md と docs/backlog.md を読む
- 小さな変更で進める
- 1機能ごとに設計、実装、テストまで完了させる
- 未使用コードを追加しない
- 将来機能の先行実装をしない
- 巨大リファクタをしない
- 依存関係の逆転を起こさない

## 完了時の更新

- docs/status.md に完了内容、残課題、次回作業候補を記録する
- 必要なら docs/backlog.md を更新する