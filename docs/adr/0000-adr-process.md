# ADR 0000: Architecture Decision Record process

- Status: accepted
- Date: 2026-05-31
- Decision Makers: user
- Recorded By: GitHub Copilot

## Context

- repo では進捗ログと実装 commit は残っているが、設計判断の一次ソースが不足していた
- repo 外の会話で固まった前提が repo に転記されないまま実装へ進み、エージェントが空白を自分の仮説で埋める事故が起きた
- 特に architecture、runtime、model 選定の判断で、誰が決めたかと何を根拠にしたかが追えなかった

## Decision

- `docs/adr` を architecture decision の正本置き場とする
- architecture、責務分解、runtime、model、provider、永続化正本、MVP 評価軸、公開 API 契約の変更は、実装前に ADR を追加または更新する
- repo 外会話に依存する判断は、ADR に転記されるまで未確定と扱う
- `docs/status.md` は進捗ログとして使い、設計判断の一次ソースにはしない

## Alternatives Considered

- AGENT.md だけで運用する
  - 却下理由: 判断の履歴と承認者が残らず、今回と同じ欠落が再発する
- status.md に決定経緯も混載する
  - 却下理由: 進捗ログと設計正本が混ざり、決定の差し替えや失効を追えない

## Consequences

- 実装前の文書化コストは増える
- その代わり、誰が何を決めたか、何が未確定か、どこまでが仮説かを追えるようになる

## Evidence

- [AGENT.md](AGENT.md)
- [docs/status.md](docs/status.md)
- [docs/backlog.md](docs/backlog.md)
- commit history: bfb181d, ae166e4, 7774b26, 039147d, 7241524

## Source Input

- ユーザーから、浅い RCA とその場しのぎ対策を禁じ、決定経緯を追えるようにする要求があった