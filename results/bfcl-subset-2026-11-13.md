# BFCL v3 부분집합 (AST 200) — Gyro-S vs Gemma 4 26B (2026-11-13)

공인 벤치 병행 측정. 공식 하네스(bfcl-eval 2025.8.6.2)의 생성·채점(AST 체커)을 그대로 사용.

## 조건

- 부분집합: BFCL v3 AST 카테고리 4종 × 각 50개 = 200케이스 (simple/multiple/parallel/parallel_multiple, ID 0–49 고정 — `results/run-20261113-bfcl/ids_full.json`)
- 온도 0, 단발(single-turn) 네이티브 함수호출, 동시 10스레드
- Gyro-S: Strata :8080 OpenAI 호환 엔드포인트 (상주 서빙 그대로)
- Gemma 4 26B-A4B Q4_K_M: Ollama :11434 OpenAI 호환 엔드포인트 — **이 경로는 think off 불가**(thinking 포함 측정). 우리 코어 24의 네이티브 API(think off) 조건과 다름
- 연결 방식: bfcl-eval OSS 경로는 프롬프팅 전용이라, 두 모델을 API 모델로 등록(OpenAICompletionsHandler + OPENAI_BASE_URL)해 네이티브 FC로 측정. 함수명의 점(.)은 하네스가 밑줄로 바꿔 보내고 채점 시 되돌림(underscore_to_dot=True — 공식 설정)
- 부분집합 채점은 공식 `ast_file_runner`를 부분집합에 직접 호출 (이 버전 CLI에 partial-eval 없음)

## 결과

| 카테고리 | Gyro-S | Gemma 4 26B |
|---|---|---|
| simple (50) | 96% (48) | **98% (49)** |
| multiple (50) | 90% (45) | **96% (48)** |
| parallel (50) | **84% (42)** | 80% (40) |
| parallel_multiple (50) | **86% (43)** | 80% (40) |
| **전체 (200)** | **89.0% (178)** | 88.5% (177) |
| 벽시계 (200케이스, 10스레드) | 1,227초 | **618초** |
| 정답 1건당 시간 | 6.9초 | **3.5초** |

## 실패 패턴

- 양쪽 다 **parallel 계열의 호출 개수 오류(wrong_count)가 최대 실패 요인** — Gemma 16건, Gyro 10건. 병렬 호출을 요구하면 일부를 빠뜨리는 경향이 공통.
- 그 외는 산발적: 매칭 실패(cannot_find_match) Gyro 7 / Gemma 5, 값 오류 등 소수.
- 형식 오류·파싱 실패는 0건 — 두 모델 다 네이티브 FC 형식은 안정적.

## 해석

- 공인 벤치에서도 동점(1케이스 차이). 우리 코어 24(23.0 동점)와 같은 결론이 다른 벤치에서 재현됨.
- 시간 우위는 Gemma 유지지만, 동시 부하 조건에서는 격차가 7배(코어 24 순차 측정)→2배로 좁혀짐. Ollama가 요청을 직렬 처리하는 영향 + thinking 포함 조건.
- 카테고리별로는 Gemma가 단발 선택(simple·multiple)에 강하고, Gyro-S가 병렬 구성(parallel 계열)에 소폭 강함.

원본: 맥미니 `~/agent-work/bfcl/` (result/·score/), 요약 `results/run-20261113-bfcl/`
