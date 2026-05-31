# backlog

## 優先タスク

- [x] Backend と Frontend の最小開発基盤を作る
  - 目的: 品質優先で開発を開始できる最小構成を作る
  - 範囲: FastAPI の health endpoint、React + Vite の最小画面、Modal の入口、基本テストとビルド確認
  - 完了条件: backend のテストと frontend の build が通る

- [ ] Redis と PostgreSQL の設定方針を確定する
  - 目的: backend の依存設定を明示し、次の機能追加で接続先をぶらさない
  - 範囲: 設定項目、環境変数名、ローカル開発時の前提整理
  - 完了条件: 設定モデルと文書が一致する

## 後続タスク

- [ ] ComfyUI 連携の設計を固める
- [ ] 画像生成ジョブの永続化方針を決める