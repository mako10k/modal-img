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
- ComfyUI 実クライアントと submission state transition を追加済み
- ComfyUI health dependency check と generation_jobs 初期化 / upgrade 手順を追加済み

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
- ComfyUI `/prompt` gateway を追加
- ComfyUI prompt graph 生成を追加
- `submitting -> queued / submission_failed / queue_publish_failed` の状態遷移を追加
- gateway と失敗時 API 応答のテストを追加
- 外部実行系の識別子を `comfyui_prompt_id` に統一
- health endpoint に ComfyUI dependency check を追加
- generation_jobs 初期化 SQL を追加
- generation_jobs 既存テーブル向け upgrade SQL を追加
- queued 更新失敗時も `comfyui_prompt_id` を保持する再整合経路を追加
- settings から workflow 配線されることを固定するテストを追加

## 残課題

- ジョブ状態取得 API と状態遷移を追加する
- ComfyUI 実行完了後の結果取り込みを追加する
- 部分成功ジョブの再整合方針と重複送信回避を追加する
- API failure detail と永続化状態の整理を継続する

## 次回作業候補

- ジョブ状態取得 API と ComfyUI 実行完了後の状態反映を追加し、部分成功ジョブの再整合方針を固定する