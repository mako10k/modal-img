# ADR 0003: MVP evaluation criteria are go/no-go judgement for the Modal direction

- Status: accepted
- Date: 2026-05-31
- Decision Makers: user

## Context

- この repo では、単に画像を 1 枚返すだけなのか、次の継続判断に使える demo を作るのかが途中でぶれていた
- ユーザーは、MVP を Modal での画像生成について続けるかやめるかを判断するための demo と位置付けた
- ComfyUI 風 UI や Stable Diffusion ツール風 UI は、判断に不要なら目的化しないことも明示された

## Decision

- この repo の MVP 評価軸は、Modal 上の画像生成について go / no-go を判断できる demo になっているかどうかである
- 単に GPU で画像が 1 枚返るだけでは MVP 達成とみなさない
- 比較 UI、多機能 UI、自由入力性は、go / no-go 判断に必要と合意された場合のみ追加する
- ComfyUI や既存 Stable Diffusion ツール風の UI は、判断 demo に不要なら実装しない

## Alternatives Considered

- GPU で 1 枚返ったら MVP とみなす
  - 却下理由: 技術実証と継続判断を混同するため
- 比較 UI や汎用 UI を先に整える
  - 却下理由: 判断に不要な周辺機能へ drift しやすい

## Consequences

- 品質評価と継続判断に直接効かない機能は後回しになる
- 実装が動いていても、判断材料として弱ければ MVP 達成とは扱わない

## Evidence

- [AGENT.md](AGENT.md)
- commit [039147d](https://github.com/mako10k/modal-img/commit/039147d)

## Source Input

- ユーザー指示: MVP は Modal での画像生成を Grok Aurora に近づける方向で、進むかやめるかを判断できる demo であること