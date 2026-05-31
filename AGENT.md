# AGENT

このリポジトリでは高品質画像生成サービスの構築を目的とする。

## 優先順位

1. 品質
2. 保守性
3. 生成速度

## 技術スタック

- Backend: Python 3.12, FastAPI, Modal, ComfyUI, Redis, PostgreSQL
- Frontend: React, TypeScript, Vite

## 方向性の優先仕様

- 生成実行の責務は Modal 側に置く
- FastAPI backend は受付、状態管理、永続化、結果参照の入口を担う
- ComfyUI を使う場合も、原則として Modal 側の実行内部に閉じ込め、backend から生の ComfyUI endpoint を正本の実行先として増築しない
- backend 直結の ComfyUI gateway や raw `/prompt` 依存は、現時点では暫定 drift として扱い、これを将来方針として正当化しない
- 実装、fixtures、ローカル起動手順がこの方針と食い違う場合は、実装ではなくこの節を優先する

## 作業ルール

- 作業前に docs/status.md と docs/backlog.md を読む
- トータルで安全な対応は、危険なところを早めにつぶすことを優先する
- 小さな変更で進める
- 1機能ごとに設計、実装、テストまで完了させる
- 未使用コードを追加しない
- 将来機能の先行実装をしない
- 巨大リファクタをしない
- 依存関係の逆転を起こさない
- 生成系の変更や起動作業に入る前に、受付、オーケストレーション、実行の責務分解を明文化し、Modal と ComfyUI の担当を取り違えない
- 画像生成で GPU や実行責務が本質的なリスクなら、表示や周辺導線より先にその成立可否を確認し、危険箇所を後回しにしない
- 指示書より実装が先に進んでいる場合、その実装を前提として拡張せず、差分をユーザーに確認してから進める

## レビュー運用

- 1 ターンにつき 1 論理コミットを基本とする
- コミット前に差分全体へ consistency-review を実行する
- レビューでは style より先に整合性、対称性、更新漏れ、テストと文書の追従を確認する
- Backend の契約変更では API、service、tests、docs の対応関係を確認する
- Frontend の build や serve 方針を変えた場合は軽量環境前提が README と設定に残っているか確認する
- 生成実行経路に触れる場合は、Modal が実行責務を持つという優先仕様に反していないかを先に確認する
- タスク完了時は docs/status.md と必要なら docs/backlog.md を更新してからコミットする

## レビュー観点

- settings と .env.example と README が一致しているか
- API 入口と service 境界と docs が一致しているか
- API 入口、Modal 実行境界、内部生成エンジンの責務が混線していないか
- Backend の変更に対して pytest が更新されているか
- Frontend の変更に対して build 前提と軽量配信前提が崩れていないか

## 完了時の更新

- docs/status.md に完了内容、残課題、次回作業候補を記録する
- 必要なら docs/backlog.md を更新する