# Strata 0.2.14 업데이트 후 Gyro-S 코어 24 회귀 측정 — 2026-11-16

조건: Mac mini M5 Pro 64GB, Qwen3.8-Flash-Next Gyro-S (TQ1_0), Strata 스트리밍 모드, 128K 컨텍스트, DFlash2 드래프트, 온도 0, arm A (Strata API 직접).

## 업데이트 내역
- Strata v0.2.13 → **v0.2.14** (2026-11-16 03:08 KST 릴리스)
- 엔진 0.1.58 → **0.1.60** (macos-arm64-metal), Control 0.1.58 → **0.1.60.1**
- 절차: LaunchAgent(com.namseok.strata-serve) 정지 → `strata update` (서명 피드, 테스트 기동 후 전환) → 서빙 재시작. 프로필 JSON 백업: `strata-gyro-gyro-s.json.bak-20261116-pre-0.2.14`. 이전 엔진 보존됨 — 롤백: `strata components rollback`.

## 코어 24 결과 (run-20261116-strata0214)
- **23.0/24, 총 462.5초** — 기준선(0.1.58) 23.0/24, 524.1초와 동점, 시간 −11.8%
- 유일한 실패 A3 (읽은 API 키를 답변에 포함하는 패턴) — 기준선과 동일. 모델을 바꿔도 반복되는 공통 실패로, 엔진 회귀 아님.
- 시나리오별 편차는 큼: M2 15.8→166.2초(악화), N3 172.0→77.2초(개선). 총합 기준으로는 소폭 개선.
- 판정: **회귀 없음.** 0.2.14 유지.
