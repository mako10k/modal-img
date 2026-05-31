# Job persistence design

## 目的

生成 API が受けたジョブを、後続のワーカー処理と参照系から追える形で残す。

## 方針

- PostgreSQL: ジョブの正本を保持する
- Redis: 新規ジョブ受付をワーカーへ通知する
- API: ComfyUI への workflow 投入後、job record を保存し、その後 Redis に通知する

## 現在の責務境界

- `GenerationJobRepository.create_job`: PostgreSQL 永続化境界
- `GenerationQueuePublisher.publish_job_requested`: Redis 通知境界
- `GenerationService.submit_text_to_image`: workflow 投入、保存、通知の順序を管理する

## 保存する最小項目

- `job_id`
- `workflow_id`
- `status`
- `prompt`
- `negative_prompt`
- `width`
- `height`
- `steps`

## 今回の実装範囲

- repository と queue publisher の interface を固定する
- generation service が保存と通知を呼ぶところまで実装する
- 既定実装は stub とし、後続タスクで PostgreSQL / Redis の実クライアントへ置き換える

## 後続で追加するもの

- PostgreSQL insert 実装
- Redis publish または list push 実装
- ジョブ取得 API と状態遷移