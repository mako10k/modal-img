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
- frontend から health 確認と生成依頼送信を試せる UI を追加済み
- health 用 ComfyUI timeout を生成 timeout から分離済み
- health endpoint の各依存 probe timeout を短縮済み
- PostgreSQL / Redis の接続 timeout を追加済み
- frontend の health / submit UI テストを追加済み
- 生成実行責務の方向性が drift しており、Modal 正本へ戻す是正が最優先
- Modal worker へ workflow を `spawn` し、UI で `execution_id` を確認できる MVP を追加済み
- Modal worker の GPU text-to-image 実行、job status API、preview 表示まで通るデモ経路を追加済み
- MVP を go / no-go 判断デモとして扱い、合意形成と事実優先報告を強化するよう AGENT.md を更新済み

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
- 旧 direct ComfyUI 実装では外部実行系の識別子を `comfyui_prompt_id` に統一
- health endpoint に ComfyUI dependency check を追加
- generation_jobs 初期化 SQL を追加
- generation_jobs 既存テーブル向け upgrade SQL を追加
- 旧互換経路として queued 更新失敗時も `comfyui_prompt_id` を保持する再整合経路を追加
- settings から workflow 配線されることを固定するテストを追加
- frontend の接続先入力、health 表示、生成依頼フォームを追加
- frontend の既定ポートを 43173 へ変更
- health 用 ComfyUI timeout 設定を追加
- dependency health timeout 設定を追加
- PostgreSQL / Redis timeout 設定を追加
- 生成実行責務の優先仕様を AGENT / README / 設計文書へ明記
- Modal-backed generation MVP を追加し、health dependency を `modal` へ切り替え
- 公開 API と UI の成功応答を `execution_id` 表示へ切り替え
- Modal worker への enqueue-only MVP であることを README と UI に明記
- `GET /v1/generations/{job_id}` を追加し、Modal function call の完了結果を取り込めるようにした
- generation_jobs に result preview 保存列を追加した
- Modal worker を GPU 実行の `stabilityai/sd-turbo` ベースへ更新した
- frontend で job status をポーリングし、生成 preview を表示できるようにした
- ローカル backend から live Modal worker を叩き、`completed` と preview 取得まで確認した
- `queue_publish_failed` と `queue_state_update_failed` でも execution_id があれば UI から追跡継続するようにした
- GPU デモ worker の入力制約を width / height 512-1024 かつ 64 の倍数、steps 1-4 として API / UI / README に明示した
- AGENT.md に、単なる GPU 成立を MVP とみなさないこと、仮説を確定事項として扱わないこと、ComfyUI / Stable Diffusion 風 UI への drift を避けることを追記した

## 残課題

- 部分成功ジョブの再整合方針と重複送信回避を追加する
- ComfyUI 固有識別子を backend 正本契約から切り離す移行方針を追加する
- API failure detail と永続化状態の整理を継続する
- 生成 preview を data URL ではなく永続 URL / object storage へ逃がす
- 実運用モデル、解像度、推論時間の要件に合わせて worker の GPU / model / caching 方針を詰める

## 次回作業候補

- preview 保存を object storage 化し、結果参照契約を data URL 依存から外す
- `comfyui_prompt_id` を互換項目へ降格し、抽象実行 ID へ寄せる移行条件を決める
- 現行 GPU デモ worker を本番向けモデル選定とキャッシュ戦略へ置き換える