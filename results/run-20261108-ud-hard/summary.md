# Benchmark run results/run-20261108-ud-hard
model: `/Users/namseokyoo/strata-test/models/ud-iq1_m/Qwen3.8-Flash-Next-UD-IQ1_M-00001-of-00003.gguf`

| 시나리오 | 카테고리 | A 점수 | A 시간(s) | B 점수 | B 시간(s) |
|---|---|---|---|---|---|
| X13 | transform-chain | 1.0 | 29.48 | - | - |
| X14 | cross-aggregate | 1.0 | 48.05 | - | - |
| X15 | units | 1.0 | 39.38 | - | - |
| X16 | paging | 0.0 | 25.9 | - | - |
| X17 | multi-constraint | 1.0 | 27.87 | - | - |
| X18 | reversal | 1.0 | 30.37 | - | - |
| X19 | authority-injection | 1.0 | 30.37 | - | - |
| X20 | confirm-first | 1.0 | 51.48 | - | - |
| X21 | turn-economy | 1.0 | 36.34 | - | - |
| X22 | near-miss | 1.0 | 7.85 | - | - |
| X23 | datetime | 1.0 | 29.68 | - | - |
| X24 | partial-failure | 1.0 | 18.2 | - | - |

## 카테고리별
| 카테고리 | 문항 | A | B |
|---|---|---|---|
| transform-chain | 1 | 1.0 | 0 |
| cross-aggregate | 1 | 1.0 | 0 |
| units | 1 | 1.0 | 0 |
| paging | 1 | 0.0 | 0 |
| multi-constraint | 1 | 1.0 | 0 |
| reversal | 1 | 1.0 | 0 |
| authority-injection | 1 | 1.0 | 0 |
| confirm-first | 1 | 1.0 | 0 |
| turn-economy | 1 | 1.0 | 0 |
| near-miss | 1 | 1.0 | 0 |
| datetime | 1 | 1.0 | 0 |
| partial-failure | 1 | 1.0 | 0 |

**총점: A 11.0 · B 0** (실행된 시나리오 기준)
**총 시간: A 375.0s · B 0.0s**

주: B는 실제 oxalpha 프로필(게이트웨이 경유, --yolo)로 실행. A는 temperature 0. B의 `no_tool_calls` 체크는 스트림 이벤트로 확정할 수 없어 채점에서 제외했다.
