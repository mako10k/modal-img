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
2. `GenerationService` が text-to-image 用 workflow payload を組み立てる
3. `ComfySubmissionGateway` が workflow を ComfyUI に投入する
4. `GenerationJobRepository` が job record を保存する
5. `GenerationQueuePublisher` が Redis へ受付通知を送る
6. API は `job_id` と `workflow_id` を返す

## 今回の実装方針

- ComfyUI 実接続はまだ入れない
- 先に gateway interface を固定する
- API と workflow 組み立ての契約をテストで固定する
- 永続化の interface を先に固定し、実接続は別タスクへ分離する

## 現在の実装対応

- `backend/app/generation.py`: request model、workflow builder、service、stub gateway、stub persistence
- `backend/app/main.py`: 生成 API 入口
- `backend/tests/test_generation.py`: 入口と workflow 組み立てのテスト
- `docs/persistence-design.md`: 永続化方針