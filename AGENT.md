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

## レビュー運用

- 1 ターンにつき 1 論理コミットを基本とする
- コミット前に差分全体へ consistency-review を実行する
- レビューでは style より先に整合性、対称性、更新漏れ、テストと文書の追従を確認する
- Backend の契約変更では API、service、tests、docs の対応関係を確認する
- Frontend の build や serve 方針を変えた場合は軽量環境前提が README と設定に残っているか確認する
- タスク完了時は docs/status.md と必要なら docs/backlog.md を更新してからコミットする

## レビュー観点

- settings と .env.example と README が一致しているか
- API 入口と service 境界と docs が一致しているか
- Backend の変更に対して pytest が更新されているか
- Frontend の変更に対して build 前提と軽量配信前提が崩れていないか

## 完了時の更新

- docs/status.md に完了内容、残課題、次回作業候補を記録する
- 必要なら docs/backlog.md を更新する