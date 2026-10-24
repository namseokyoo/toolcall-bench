# Benchmark run results/diet-kanban-quick
model: `qwen3.8-flash-next-gyro-gyro-s`

| 시나리오 | 카테고리 | A 점수 | A 시간(s) | B 점수 | B 시간(s) |
|---|---|---|---|---|---|
| S1 | single | - | - | 1.0 | 46.39 |
| M2 | multi | - | - | 1.0 | 52.8 |
| N1 | nocall | - | - | 1.0 | 44.84 |

## 카테고리별
| 카테고리 | 문항 | A | B |
|---|---|---|---|
| single | 1 | 0 | 1.0 |
| multi | 1 | 0 | 1.0 |
| nocall | 1 | 0 | 1.0 |

**총점: A 0 · B 3.0** (실행된 시나리오 기준)
**총 시간: A 0.0s · B 144.0s**

주: B는 실제 oxalpha 프로필(게이트웨이 경유, --yolo)로 실행. A는 temperature 0. B의 `no_tool_calls` 체크는 스트림 이벤트로 확정할 수 없어 채점에서 제외했다.
