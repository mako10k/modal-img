# ComfyUI integration

## 方向性の訂正

- 正本のアーキテクチャでは、画像生成の実行責務は Modal 側に置く
- ComfyUI は backend が直接運用責務を持つ外部実行系ではなく、採用する場合も Modal 実行内部のエンジンとして扱う
- backend から raw ComfyUI endpoint を直接叩く現在の実装は暫定 drift であり、これを将来方針として拡張しない
- この文書の `ComfySubmissionGateway` 記述は現状実装の記録であり、優先仕様ではない

## 目的

現状の direct ComfyUI 実装 drift を棚卸しし、Modal が生成実行責務を持つ方向へ戻すための差分を明確にする。

## 正本の責務境界

- API 入口: FastAPI backend
- 実行オーケストレーション: Modal
- 画像生成エンジン: Modal 内部に閉じ込めた実装詳細
- 永続化責務: `GenerationJobRepository` と `GenerationQueuePublisher`

backend から raw ComfyUI `/prompt` を叩く経路は、この正本境界と食い違うため、今後の新規開発では増築対象にしない。

## 現在の境界

- API 入口: `POST /v1/generations`
- ジョブ投入層: `GenerationService.submit_text_to_image`
- Modal 実行境界: `ModalSubmissionGateway.enqueue_workflow`
- 永続化責務: `GenerationJobRepository` と `GenerationQueuePublisher`

## リクエストの流れ

1. API が `GenerationRequest` を受け取る
2. `GenerationService` が PostgreSQL に `submitting` 状態の job を保存する
3. PostgreSQL への初期保存に失敗した場合、API は `persistence_failed` を返して処理を中断する
4. `GenerationService` が text-to-image 用 workflow を組み立てる
5. `ModalSubmissionGateway` が workflow を Modal worker function に `spawn` する
6. 成功時は `GenerationJobRepository` が job を `queued` へ更新する
7. 成功時は `GenerationQueuePublisher` が Redis へ受付通知を送る
8. API は `job_id` と `execution_id` を返す
9. 失敗時は `GenerationJobRepository` が job を `submission_failed` へ更新し、API は 502 を返す
10. Redis 通知失敗時は `GenerationJobRepository` が job を `queue_publish_failed` へ更新し、API は 502 を返す
11. queued への状態更新自体が失敗した場合、API は 502 を返し、job は `submitting` のまま残しつつ内部 execution 識別子と error detail を保持して後続の再整合対象にする
12. failure 状態への更新自体が落ちた場合も API は 502 を返し、error detail に state update error を含める

`persistence_failed` と `queue_state_update_failed` は永続化状態ではなく、API error detail の分類として扱う。

## 現状実装の記録

- workflow は引き続き ComfyUI 互換 graph を生成している
- backend は raw ComfyUI endpoint ではなく Modal worker function へ `spawn` する
- API、gateway、状態遷移の契約を現状実装としてテストで固定している

この節は Modal 主導へ戻した現状実装の記録であり、ComfyUI 固有要素はまだ内部互換として残っている。
- 画像取得やジョブ状態照会は後続タスクへ分離する

## 現在の実装対応

- `backend/app/generation.py`: request model、workflow builder、service、状態遷移
- `backend/app/modal_execution.py`: Modal worker gateway
- `backend/app/main.py`: 生成 API 入口
- `backend/tests/test_generation.py`: 入口と workflow / 状態遷移のテスト
- `backend/tests/test_modal_execution.py`: Modal gateway のテスト
- `docs/persistence-design.md`: 永続化方針

## 次の修正方針

- Modal 実行完了後の結果反映と状態取得 API を追加する
- backend の settings / docs から残っている raw ComfyUI 互換表現をさらに縮退させる
- ComfyUI 固有の識別子や health check は、Modal 内部実装へ押し戻せるかを先に検討する
- backend の後続機能追加は、Modal 実行境界への移行完了まで direct ComfyUI 経路を深掘りしない