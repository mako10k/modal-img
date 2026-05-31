# backlog

## 優先タスク

- [ ] 生成実行責務を Modal 正本へ戻す
  - 目的: 直近の drift で生じた backend 直結 ComfyUI 前提を止め、生成実行責務を Modal に戻す
  - 範囲: AGENT、README、設計文書、settings、health、generation service、テストの責務整理
  - 完了条件: backend が raw ComfyUI 常駐前提を正本仕様として持たず、Modal 実行境界が文書と実装で一致する

- [x] Backend と Frontend の最小開発基盤を作る
  - 目的: 品質優先で開発を開始できる最小構成を作る
  - 範囲: FastAPI の health endpoint、React + Vite の最小画面、Modal の入口、基本テストとビルド確認
  - 完了条件: backend のテストと frontend の build が通る

- [x] Redis と PostgreSQL の設定方針を確定する
  - 目的: backend の依存設定を明示し、次の機能追加で接続先をぶらさない
  - 範囲: 設定項目、環境変数名、ローカル開発時の前提整理
  - 完了条件: 設定モデルと文書が一致する

- [x] Redis と PostgreSQL の実接続クライアントを追加する
  - 目的: 設定済み接続先を実際のジョブ基盤へつなぐ
  - 範囲: 接続ファクトリ、ヘルスチェック、ローカル開発前提の整理
  - 完了条件: 接続初期化コードとテスト方針が揃う

- [x] ComfyUI 連携の設計を固める
  - 目的: 画像生成ジョブの責務境界を先に確定し、接続済み基盤の上に実装を載せる
  - 範囲: API 入口、ジョブ投入、ComfyUI 呼び出し境界、永続化責務の分離
  - 完了条件: 最小の設計文書と実装入口が一致する

## 後続タスク

- [x] 画像生成ジョブの永続化方針を決める
  - 目的: 生成 API が受けた job を後続処理と参照系から追える形にする
  - 範囲: PostgreSQL を正本、Redis を通知経路とする責務分離、保存項目、service の呼び出し順序
  - 完了条件: 設計文書と generation service の persistence 境界が一致する

- [x] PostgreSQL への job insert と Redis 通知の実装を追加する
  - 目的: persistence 境界を実クライアントへ置き換え、生成 API から実際に保存と通知を行う
  - 範囲: repository 実装、queue publisher 実装、接続エラー時の扱い、テスト
  - 完了条件: generation API が実クライアントを通じて保存と通知を行う

- [x] ComfyUI 実クライアントを gateway へ接続する
  - 目的: stub gateway を実際の ComfyUI 呼び出しへ置き換え、生成依頼を外部実行系へ渡す
  - 範囲: gateway 実装、接続設定、失敗時の扱い、テスト
  - 完了条件: generation API が workflow を ComfyUI へ送信できる
  - 注記: これは現状実装の到達点であり、正本アーキテクチャではない。今後は Modal 実行境界へ戻す

- [ ] ジョブ状態取得 API と結果反映を追加する
  - 目的: 受け付けた job の進行状況と結果を参照できるようにする
  - 範囲: PostgreSQL 読み出し、Modal 実行完了結果の反映、状態取得 API、部分成功ジョブの再整合 / 重複送信回避、テスト
  - 完了条件: job_id から状態を取得でき、完了時の結果反映方針と部分成功ジョブの回復方針が Modal 実行境界と一致する

- [ ] 外部実行識別子を Modal 主導の抽象 ID へ寄せる
  - 目的: `comfyui_prompt_id` を backend 公開契約の中心に据えたまま固定しない
  - 範囲: API 応答、永続化項目、README、status、テストの互換整理
  - 完了条件: ComfyUI 固有識別子が backend の正本契約ではなく、必要な互換範囲だけが明示される