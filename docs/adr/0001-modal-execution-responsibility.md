# ADR 0001: Generation execution responsibility belongs to Modal

- Status: accepted
- Date: 2026-05-31
- Decision Makers: user

## Context

- 一時的に backend 直結の ComfyUI 前提へ drift していた
- ユーザーは、生成実行責務を Modal 側に置くことを繰り返し要求した
- backend は受付、状態管理、永続化、結果参照の入口に留める必要がある

## Decision

- 画像生成の実行責務は Modal 側に置く
- FastAPI backend は受付、オーケストレーション、状態管理、永続化、結果参照 API を担う
- ComfyUI を使う場合も backend の外部正本依存にはせず、Modal 実行内部の実装詳細として閉じ込める

## Alternatives Considered

- backend から raw ComfyUI endpoint を正本の実行先として使い続ける
  - 却下理由: ユーザーの明示方針と不一致で、責務分解も崩れる

## Consequences

- backend には Modal execution gateway と結果参照経路が必要になる
- ComfyUI 固有要素は互換整理の対象になり、正本契約から外していく必要がある

## Evidence

- [AGENT.md](AGENT.md)
- [README.md](README.md)
- [docs/comfyui-design.md](docs/comfyui-design.md)
- [docs/persistence-design.md](docs/persistence-design.md)
- commit [bfb181d](https://github.com/mako10k/modal-img/commit/bfb181d)

## Source Input

- ユーザー指示: 画像生成側は Modal であること。backend 直結 ComfyUI は方向性の誤りであること