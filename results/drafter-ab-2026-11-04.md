# 드래프터 A/B: MTP vs DFlash2 (2026-11-04)

Strata 0.2.10 (엔진·Control 0.1.56)에서 기본 드래프터가 된 DFlash2와 기존 MTP를
toolcall-bench 하니스 A암(24개 시나리오, temperature 0)으로 비교했다.

## 측정 조건

- 기기: Mac mini M5 Pro 64GB, Qwen3.8-Flash-Next Gyro-S, 스트리밍 모드(`--mmap-experts`, `STRATA_METAL_STREAM=1`), 컨텍스트 128K
- MTP 런: 운용 서버(:8080) 그대로. 설정은 setup 기본값 `--spec 2` + `--mtp` 레이어(5.2GB)
- DFlash2 런: 같은 기기에 별도 인스턴스(:8081)로 기동, 운용 서버는 무중단. 드래프터 팩 `qwen3.8-flash-next-dflash2.q4_0-selq4.pack`(0.52GB, `strata drafting fetch`로 취득), Control 변환값 `--spec 6 --draft-conf 0.8`, `--draft-fallback none`(MTP 미로드)
- 두 런 모두 상대 인스턴스가 상주한 상태에서 측정(조건 대칭). 게이트웨이 실요청은 MTP 런 구간에 대형 프롬프트 2건만 겹침
- 2026-10-24 기준선(A 372.6초)은 엔진 0.1.47·단독 인스턴스 조건이라 총시간 직접 비교 대상이 아니다. 점수(23.0)는 동일하게 유지됨

## 결과

| 지표 | MTP | DFlash2 |
|---|---|---|
| 총점 (24개) | 23.0 | 23.0 |
| 총 시간 | 838.9s | **524.1s (−37.5%)** |
| 시나리오별 중앙값 | 26.20s | **18.73s** |
| 더 빨랐던 시나리오 | 3/24 | **21/24** |
| 서버 로그 디코드 중앙값 | 20.8 tok/s | **25.5 tok/s** |

- 실패 시나리오는 양쪽 모두 A3 하나로 동일.
- N3는 양쪽 다 다중 턴으로 길어졌다(MTP 222.0s / DFlash2 108.7s). A2의 MTP 111.1s는 긴 생성 구간이 겹친 값으로 보이며, 이를 제외해도 순서는 유지된다.
- 원본: `results/run-20261104-mtp/`, `results/run-20261104-dflash2/` (summary.md/json)

## 부수 발견

- Control 0.1.56의 `--drafter dflash2` 인자는 엔진 인자로 번역되면서도 원본이 그대로 함께 넘어가, 엔진이 `unknown argument: --drafter`로 기동 실패한다. 폴백 재시작도 같은 인자를 포함해 실패했다. 프로필에는 엔진 인자(`--draft dflash2 --draft-model <pack> --mtp-draft-vocab <vocab>`)를 직접 써야 한다.
- DFlash2 전환 시 MTP 레이어 5.2GB를 로드하지 않아 그만큼 메모리가 빈다. 드래프터 자체는 약 0.7GB.

## 판정

측정 범위(단일 요청 순차 실행)에서는 DFlash2가 점수 동등, 속도 우세.
동시 요청 조건에서의 DFlash2 동작은 이 측정으로 확인되지 않았다(운용 게이트웨이의 동시 호출이 잦지 않다는 전제에서 별도 확인 항목으로 남김).
운용 서버의 드래프터 전환 여부는 이 결과를 보고 사용자가 결정한다.
