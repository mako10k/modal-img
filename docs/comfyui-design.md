# ComfyUI integration

## 目的

ComfyUI 連携の責務境界を先に固定し、永続化やジョブワーカーの実装を後続タスクへ分離する。

## 現在の境界

- API 入口: `POST /v1/generations`
- ジョブ投入層: `GenerationService.submit_text_to_image`
- ComfyUI 境界: `ComfySubmissionGateway.enqueue_workflow`
- 永続化責務: `GenerationJobRepository` と `GenerationQueuePublisher`

## リクエストの流れ

1. API が `GenerationRequest` を受け取る
2. `GenerationService` が PostgreSQL に `submitting` 状態の job を保存する
3. `GenerationService` が text-to-image 用 ComfyUI prompt graph を組み立てる
4. `ComfySubmissionGateway` が workflow を ComfyUI `/prompt` に投入する
5. 成功時は `GenerationJobRepository` が job を `queued` へ更新する
6. 成功時は `GenerationQueuePublisher` が Redis へ受付通知を送る
7. API は `job_id` と `comfyui_prompt_id` を返す
8. 失敗時は `GenerationJobRepository` が job を `submission_failed` へ更新し、API は 502 を返す
9. Redis 通知失敗時は `GenerationJobRepository` が job を `queue_publish_failed` へ更新し、API は 502 を返す
10. queued への状態更新自体が失敗した場合、API は 502 を返し、job は `submitting` のまま残しつつ `comfyui_prompt_id` と error detail を保持して後続の再整合対象にする
11. failure 状態への更新自体が落ちた場合も API は 502 を返し、error detail に state update error を含める

`queue_state_update_failed` は永続化状態ではなく、queued 更新に失敗したことを表す API error detail の分類として扱う。

## 今回の実装方針

- ComfyUI への送信は `httpx` ベースの gateway adapter で行う
- workflow は ComfyUI prompt graph を直接生成する
- API、gateway、状態遷移の契約をテストで固定する
- 画像取得やジョブ状態照会は後続タスクへ分離する

## 現在の実装対応

- `backend/app/generation.py`: request model、workflow builder、service、状態遷移
- `backend/app/comfyui.py`: ComfyUI `/prompt` gateway
- `backend/app/main.py`: 生成 API 入口
- `backend/tests/test_generation.py`: 入口と workflow / 状態遷移のテスト
- `backend/tests/test_comfyui.py`: gateway のテスト
- `docs/persistence-design.md`: 永続化方針