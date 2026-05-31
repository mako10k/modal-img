# ADR 0002: Generation engine selection remains unresolved until source intent is restored

- Status: proposed
- Date: 2026-05-31
- Decision Makers: user

## Context

- repo 外で行われたチャッピーとの会話をもとに、別の実行方針や model 方針があった可能性がある
- 現在の repo には、その外部会話の内容や `FLEX` に関する明示記録が存在しない
- commit [7241524](https://github.com/mako10k/modal-img/commit/7241524) では、go / no-go 判断に必要な 1 枚の説得力という仮説から `stabilityai/stable-diffusion-xl-base-1.0` を採用した
- この SDXL 採用は、ユーザーが承認した architecture decision としては記録されていない

## Decision

- 生成 engine、runtime、model の最終選定は未確定とする
- 現行の SDXL base 実装は、承認済み正本ではなく暫定の検証実装として扱う
- `FLEX` を含む外部会話起点の候補は、元の意図をユーザーが再提示し、ADR に転記した時点で比較対象に戻す
- この ADR が accepted になるまでは、engine 選定を前提にした追加最適化や横展開を進めない

## Alternatives Considered

- 現行 SDXL 実装をそのまま正式方針とみなす
  - 却下理由: 決定者、根拠、代替案比較が欠けており、今回の不満の原因そのものを再生産する
- repo に記録がないため FLEX 仮説を無視する
  - 却下理由: repo 外の判断材料が失われただけの可能性を切り捨ててしまう

## Consequences

- 現行実装は動作検証には使えるが、正式アーキテクチャの根拠には使えない
- 次に進む前に、元の意図、候補、評価軸、決定者を整理する必要がある

## Evidence

- [AGENT.md](AGENT.md)
- [docs/status.md](docs/status.md)
- commit [7241524](https://github.com/mako10k/modal-img/commit/7241524)

## Source Input

- ユーザー指摘: チャッピーとの会話ベースの前提が引き継がれず、エージェントが勝手に決めたことへの強い不満