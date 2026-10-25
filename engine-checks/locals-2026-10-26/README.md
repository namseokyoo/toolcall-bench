# Locals 내장 벤치 재현 — 맥미니 M5 Pro (2026-10-26)

이 폴더는 이 레포의 하니스(`runner.py`) 결과가 아니다. 에이전트용 맥 로컬 추론 서버 [Locals](https://github.com/Generated-Computers/Locals) (Generated-Computers, 2026-10-12 공개, Apache-2.0)의 **벤더 내장 벤치(`locals bench`)를 내 기기에서 그대로 재현**한 기록이다. 벤더가 공개한 수치와 실측이 얼마나 맞는지를 확인하는 게 목적.

## 실행 환경 · 조건

- 기기: Mac mini **M5 Pro, 64GB** (Locals 인식 GPU 가용 51.8GB)
- Locals 0.2.1 (`uv tool install --python 3.12 locals`)
- 모델: `mlx-community/Qwen3.5-4B-MLX-4bit` (Locals README 차트와 동일 계열)
- 명령: `locals bench --model qwen --sizes 1,2,4,8 --engines locals,mlx`, 요청당 256 토큰
- 실행: 2026-10-26 03:11~03:17 KST, 유휴 확인 후 (게이트웨이 턴 없음, 큐 비어 있음, load ~2)
- **동시 상주**: Strata Gyro-S (Qwen3.8-Flash-Next, :8080) + ComfyUI + Hermes 프로필 3개가 켜진 평소 상태에서 측정. 중지·재시작 없이 진행했다. mlx-lm 단독 속도에 상주 부담이 실렸을 수 있다.
- **커널 미튜닝 상태**: 벤치가 "no tuned kernels for this model on applegpu_g17s yet"를 명시. 즉 튜닝 커널 적용 전 수치이며, 벤더 README 수치는 튜닝 후일 가능성이 있다.

원본 데이터: [bench.json](bench.json)

## 결과 (tok/s, 전체 요청 합산)

| 동시 요청 | Locals | mlx-lm | 배율 | 첫 토큰까지 (Locals / mlx-lm) |
| --- | --- | --- | --- | --- |
| 1 | 91.5 | 51.5 | 1.78x | 0.24s / 1.47s |
| 2 | 183.1 | 141.2 | 1.30x | 0.55s / 3.06s |
| 4 | 282.3 | 199.0 | 1.42x | 0.39s / 3.12s |
| 8 | 304.2 | 247.4 | 1.23x | 0.86s / 3.10s |

## 벤더 README 주장치와 비교 (Qwen3.5-4B, 서버 경유 차트, M5 Pro 24GB 기준)

| 동시 요청 | README mlx-lm | README Locals | README 배율 | 이번 실측 mlx-lm | 이번 실측 Locals | 이번 실측 배율 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 86 | 90 | 1.05x | 51.5 | 91.5 | 1.78x |
| 2 | 151 | 161 | 1.07x | 141.2 | 183.1 | 1.30x |
| 4 | 232 | 253 | 1.09x | 199.0 | 282.3 | 1.42x |
| 8 | 258 | 382 | 1.48x | 247.4 | 304.2 | 1.23x |

읽는 법:

- 1~4동시: 이번 실측 배율이 README보다 높게 나왔다. Locals 절대값은 README와 비슷하거나 높은데(91.5 vs 90, 183.1 vs 161, 282.3 vs 253), mlx-lm이 README보다 낮게 나왔기 때문이다(특히 단독 51.5 vs 86). 상주 중인 Strata가 mlx-lm 단독 속도에 더 부담이 됐을 가능성이 있다.
- 8동시: README의 1.48x(382 tok/s)는 재현되지 않았다. 실측 Locals 304.2 tok/s, 배율 1.23x. 가장 유력한 원인은 커널 미튜닝 상태이고, Strata 상주도 한 요인일 수 있다.
- 첫 토큰 지연은 전 구간에서 Locals가 뚜렷하게 짧았다 (단독 0.24s vs 1.47s, 8동시 0.86s vs 3.10s).

## 판정

Strata 단독 스트림 위주의 워크로드라면, 이번 측정만으로 Strata를 두고 Locals로 갈아탈 이유는 확인되지 않았다. 단독 요청은 벤더 주장 자체가 "동급"이고, 8동시 1.48x는 미튜닝·상주 조건에서 1.2x로만 재현됐다. 다만 동시 에이전트 2~4개를 돌리거나 첫 토큰 지연을 줄여야 하면 Locals는 mlx-lm 대비 1.3~1.4x로 의미가 있다.

## 다음 측정 (예정)

- `locals tune` 적용 후 8동시 재측정 — 이번 수치 갱신
- 이 레포 하니스(`runner.py`)를 Locals 엔드포인트로 실행 — 그 결과는 `results/` 본류에 올린다
