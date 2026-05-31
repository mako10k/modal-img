# status

## 現在の状態

- GitHub リポジトリを public で運用開始済み
- Backend と Frontend の最小開発基盤を作成済み
- backend テストと frontend build を通した初期状態
- Redis / PostgreSQL の設定モデルと環境変数名を定義済み
- frontend は軽量環境で静的配信前提の起動方針を採用
- Redis / PostgreSQL の接続ファクトリと依存ヘルスチェックを追加済み
- ComfyUI 連携の設計文書と生成 API 入口を追加済み
- 生成ジョブ永続化の方針文書と persistence 境界を追加済み
- PostgreSQL job insert と Redis queue push の実装を追加済み
- コードレビュー運用を custom review agent 前提で定義済み

## 完了した内容

- リポジトリ初期化
- GitHub リポジトリ作成
- GitHub リポジトリ public 化
- AGENT.md と進捗文書を作成
- FastAPI の health endpoint を追加
- Modal の ASGI 入口を追加
- React + Vite の最小画面を追加
- Python 3.12 で backend テストを実行
- frontend build を実行
- Redis / PostgreSQL / frontend 配信方針の設定モデルを追加
- backend の設定テストを追加
- 軽量環境向け frontend serve:lite を追加
- Redis 接続ファクトリを追加
- PostgreSQL 接続ファクトリを追加
- health endpoint に依存ヘルスチェックを追加
- 接続層とヘルスチェックのテストを追加
- ComfyUI 連携の設計文書を追加
- `POST /v1/generations` の最小入口を追加
- workflow builder と stub gateway を追加
- 生成入口のテストを追加
- 永続化方針文書を追加
- generation service に repository / queue publisher 境界を追加
- 生成ジョブ保存と通知のテストを追加
- PostgreSQL repository 実装を追加
- Redis queue publisher 実装を追加
- generation service を実クライアントで配線
- review workflow を AGENT.md と custom review agent に追加

## 残課題

- 画像生成ジョブの永続化と状態管理を設計する
- ComfyUI 実クライアントを gateway へ組み込む
- ジョブ状態取得 API と状態遷移を追加する

## 次回作業候補

- ComfyUI 実クライアントを gateway に接続し、失敗時の状態遷移を定義する