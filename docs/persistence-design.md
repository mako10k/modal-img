# Job persistence design

## 目的

生成 API が受けたジョブを、後続のワーカー処理と参照系から追える形で残す。

## 方針

- PostgreSQL: ジョブの正本を保持する
- Redis: 新規ジョブ受付をワーカーへ通知する
- API: 先に `submitting` 状態を保存し、ComfyUI 成功時に `queued` へ更新して Redis に通知する
- API: ComfyUI 失敗時は `submission_failed` へ更新し、Redis 通知は行わない
- API: Redis 通知失敗時は `queue_publish_failed` へ更新する
- API: queued への状態更新自体が失敗した場合、job は `submitting` のまま残しつつ `comfyui_prompt_id` と error detail を保持し、API は 502 を返す
- API: failure 状態への更新自体が失敗した場合も API は 502 を返し、error detail に state update error を含める

`queue_state_update_failed` は永続化状態ではなく、queued 更新失敗を伝える API error detail の分類として扱う。

## 現在の責務境界

- `GenerationJobRepository.create_job`: PostgreSQL 永続化境界
- `GenerationJobRepository.mark_job_queued`: ComfyUI 成功時の状態更新境界
- `GenerationJobRepository.mark_job_submission_failed`: ComfyUI 失敗時の状態更新境界
- `GenerationJobRepository.mark_job_queue_publish_failed`: Redis 通知失敗時の状態更新境界
- `GenerationJobRepository.mark_job_queue_state_update_failed`: queued 更新失敗時に再整合情報を残す境界
- `GenerationQueuePublisher.publish_job_requested`: Redis 通知境界
- `GenerationService.submit_text_to_image`: workflow 投入、保存、通知の順序を管理する

## 保存する最小項目

- `job_id`
- `comfyui_prompt_id`
- `status`
- `error_message`
- `prompt`
- `negative_prompt`
- `width`
- `height`
- `steps`

## 今回の実装範囲

- generation service が `submitting -> queued / submission_failed / queue_publish_failed` を管理する
- PostgreSQL repository が insert と状態更新を行う
- Redis queue publisher が `queued` ジョブだけを通知する
- `queued` 更新失敗は再整合対象として `submitting` のまま扱い、`comfyui_prompt_id` と error detail を保持する

## 後続で追加するもの

- ジョブ取得 API と状態遷移
- ComfyUI 完了後の結果反映