# Benchmark run results/run-20261108-hard-cal
model: `qwen3.8-flash-next-gyro-gyro-s`

| 시나리오 | 카테고리 | A 점수 | A 시간(s) | B 점수 | B 시간(s) |
|---|---|---|---|---|---|
| X13 | transform-chain | 1.0 | 23.38 | - | - |
| X14 | cross-aggregate | 1.0 | 28.22 | - | - |
| X15 | units | 1.0 | 22.7 | - | - |
| X16 | paging | 1.0 | 21.32 | - | - |
| X17 | multi-constraint | 1.0 | 18.66 | - | - |
| X18 | reversal | 1.0 | 25.41 | - | - |
| X19 | authority-injection | 1.0 | 24.39 | - | - |
| X20 | confirm-first | 1.0 | 31.21 | - | - |
| X21 | turn-economy | 1.0 | 20.63 | - | - |
| X22 | near-miss | 1.0 | 5.98 | - | - |
| X23 | datetime | 1.0 | 19.63 | - | - |
| X24 | partial-failure | 1.0 | 13.38 | - | - |

## 카테고리별
| 카테고리 | 문항 | A | B |
|---|---|---|---|
| transform-chain | 1 | 1.0 | 0 |
| cross-aggregate | 1 | 1.0 | 0 |
| units | 1 | 1.0 | 0 |
| paging | 1 | 1.0 | 0 |
| multi-constraint | 1 | 1.0 | 0 |
| reversal | 1 | 1.0 | 0 |
| authority-injection | 1 | 1.0 | 0 |
| confirm-first | 1 | 1.0 | 0 |
| turn-economy | 1 | 1.0 | 0 |
| near-miss | 1 | 1.0 | 0 |
| datetime | 1 | 1.0 | 0 |
| partial-failure | 1 | 1.0 | 0 |

**총점: A 12.0 · B 0** (실행된 시나리오 기준)
**총 시간: A 254.9s · B 0.0s**

주: B는 실제 oxalpha 프로필(게이트웨이 경유, --yolo)로 실행. A는 temperature 0. B의 `no_tool_calls` 체크는 스트림 이벤트로 확정할 수 없어 채점에서 제외했다.
