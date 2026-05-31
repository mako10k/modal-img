# ComfyUI integration

## 目的

ComfyUI 連携の責務境界を先に固定し、永続化やジョブワーカーの実装を後続タスクへ分離する。

## 現在の境界

- API 入口: `POST /v1/generations`
- ジョブ投入層: `GenerationService.submit_text_to_image`
- ComfyUI 境界: `ComfySubmissionGateway.enqueue_workflow`
- 永続化責務: 今回は未実装。後続で PostgreSQL と Redis を接続する

## リクエストの流れ

1. API が `GenerationRequest` を受け取る
2. `GenerationService` が text-to-image 用 workflow payload を組み立てる
3. `ComfySubmissionGateway` が workflow を ComfyUI に投入する
4. API は `job_id` と `workflow_id` を返す

## 今回の実装方針

- ComfyUI 実接続はまだ入れない
- 先に gateway interface を固定する
- API と workflow 組み立ての契約をテストで固定する
- 永続化は別タスクへ分離する

## 現在の実装対応

- `backend/app/generation.py`: request model、workflow builder、service、stub gateway
- `backend/app/main.py`: 生成 API 入口
- `backend/tests/test_generation.py`: 入口と workflow 組み立てのテスト