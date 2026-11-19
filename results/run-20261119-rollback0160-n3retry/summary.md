# Benchmark run results/run-20261119-rollback0160-n3retry
model: `qwen3.8-flash-next-gyro-gyro-s`

| 시나리오 | 카테고리 | A 점수 | A 시간(s) | B 점수 | B 시간(s) |
|---|---|---|---|---|---|
| N3 | nocall | 1.0 | 71.49 | - | - |

## 카테고리별
| 카테고리 | 문항 | A | B |
|---|---|---|---|
| nocall | 1 | 1.0 | 0 |

**총점: A 1.0 · B 0** (실행된 시나리오 기준)
**총 시간: A 71.5s · B 0.0s**

주: B는 실제 oxalpha 프로필(게이트웨이 경유, --yolo)로 실행. A는 temperature 0. B의 `no_tool_calls` 체크는 스트림 이벤트로 확정할 수 없어 채점에서 제외했다.
