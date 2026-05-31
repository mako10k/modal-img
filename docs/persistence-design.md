# Job persistence design

## 方向性の訂正

- 正本のアーキテクチャでは、生成実行の責務は Modal 側に置く
- 永続化設計は backend 直結の ComfyUI 前提を固定するためではなく、受付と状態管理の境界を安定化するためにある
- `comfyui_prompt_id` を含む現行保存項目は暫定実装の記録であり、将来方針として固定しない

## 目的

生成 API が受けたジョブを、後続のワーカー処理と参照系から追える形で残す。

## 正本方針

- PostgreSQL: ジョブの正本を保持する
- Redis: 新規ジョブ受付をワーカーへ通知する
- API: 先に `submitting` 状態を保存し、Modal 側の実行受付成功時に `queued` へ更新して Redis に通知する
- API: 初期保存自体が失敗した場合は `persistence_failed` を返し、実行系には送信しない
- API: 実行受付失敗時は `submission_failed` へ更新し、Redis 通知は行わない
- API: Redis 通知失敗時は `queue_publish_failed` へ更新する
- API: queued への状態更新自体が失敗した場合、job は `submitting` のまま残しつつ外部実行識別子と error detail を保持し、API は 502 を返す
- API: failure 状態への更新自体が失敗した場合も API は 502 を返し、error detail に state update error を含める

`persistence_failed` と `queue_state_update_failed` は永続化状態ではなく、API error detail の分類として扱う。

## 現状実装の記録

- `GenerationJobRepository.create_job`: PostgreSQL 永続化境界
- `GenerationJobRepository.mark_job_queued`: 現状実装では ComfyUI 成功時の状態更新境界
- `GenerationJobRepository.mark_job_submission_failed`: 現状実装では ComfyUI 失敗時の状態更新境界
- `GenerationJobRepository.mark_job_queue_publish_failed`: Redis 通知失敗時の状態更新境界
- `GenerationJobRepository.mark_job_queue_state_update_failed`: queued 更新失敗時に再整合情報を残す境界
- `GenerationQueuePublisher.publish_job_requested`: Redis 通知境界
- `GenerationService.submit_text_to_image`: workflow 投入、保存、通知の順序を管理する

この節は current implementation の記録であり、backend 直結 ComfyUI を正本仕様として固定する意図はない。

## 保存する最小項目

- `job_id`
- `execution_id`
- `status`
- `error_message`
- `prompt`
- `negative_prompt`
- `width`
- `height`
- `steps`

現状実装では `execution_id` の具体値として `comfyui_prompt_id` を保存しているが、これは移行対象とする。

## 今回の実装範囲

- generation service が `submitting -> queued / submission_failed / queue_publish_failed` を管理する
- generation service が初期保存失敗を `persistence_failed` として返す
- PostgreSQL repository が insert と状態更新を行う
- Redis queue publisher が `queued` ジョブだけを通知する
- 現状実装の `queued` 更新失敗は再整合対象として `submitting` のまま扱い、`comfyui_prompt_id` と error detail を保持する

## 後続で追加するもの

- ジョブ取得 API と状態遷移
- Modal 実行完了後の結果反映
- `comfyui_prompt_id` を抽象 `execution_id` へ寄せる互換整理