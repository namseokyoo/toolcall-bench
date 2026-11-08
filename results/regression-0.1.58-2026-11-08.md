# Regression re-run — Strata 0.2.12 (engine 0.1.58), 2026-11-08

Harness A arm (direct API) re-run after the 0.2.12 update, to check for
score/speed regressions against earlier engine versions.

## Conditions

- Mac mini M5 Pro, 64 GB, engine/Control **0.1.58** (Strata 0.2.12)
- Model: Qwen3.8-Flash-Next **Gyro-S** pack, streaming mode (`--mmap-experts`),
  context 131072, temperature 0
- Drafter: DFlash2, `--spec 6`, **effective `--draft-conf 0.5`** — Control 0.1.58
  overrides the profile's 0.8 with its tuned value (profile file unchanged)
- Production instance on :8080, Hermes gateways resident (mostly idle)
- A 68 GB GGUF download was writing to the same SSD during the run
  (timings may carry disk-contention noise; scores are unaffected)

## Result

- **Score 23.0 / 24** — only A3 (safety) failed, the same single failure as
  every previous run
- **Total 391.6 s**, per-scenario median ≈ 9.6 s
- Outlier: N3 172.0 s (multi-turn nocall; 108.7–222.0 s across past runs)

## Comparison (conditions differ — read with care)

| Run | Engine | Score | Total | Median | Conditions |
|---|---|---|---|---|---|
| 2026-10-24 baseline | 0.1.47 | 23.0 | 372.6 s | — | solo instance |
| 2026-11-04 DFlash2 | 0.1.56 | 23.0 | 524.1 s | 18.7 s | two instances sharing the machine, conf 0.8 |
| 2026-11-08 (this) | 0.1.58 | 23.0 | 391.6 s | ≈9.6 s | single instance + gateways, 68 GB download writing, conf 0.5 |

Totals are **not** a pure engine delta: instance sharing and disk contention
differ per run. What this run establishes: **no score regression on 0.1.58**,
and wall-clock is in the normal band for this machine.
