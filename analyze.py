#!/usr/bin/env python3
"""상세 지표 분석: 체크 단위 부분점수 + 궤적 지표를 전 런 summary.json에서 소급 계산.
궤적 지표 정의 (전부 call_log에서 계산 가능):
- calls/turns: 총 호출 수 / 사용 턴 수
- parallel%: parallel_group>1 인 호출 비율
- terminal%: terminal 호출 비율
- escape: 샌드박스 밖 절대경로를 참조한 호출 수 (자기 샌드박스 경로는 제외)
주의: 도구 결과는 기록되지 않아 오류·복구 횟수는 소급 불가 (러너 계측 과제)."""
import glob, json, os

def arg_strings(args):
    out = []
    for v in (args or {}).values():
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, (list, dict)):
            out.append(json.dumps(v, ensure_ascii=False))
    return out

def traj(rec):
    calls = [c for c in rec.get("calls", []) if isinstance(c, dict) and "name" in c]
    n = len(calls)
    if n == 0:
        return dict(calls=0, turns=0, parallel=0.0, terminal=0.0, escape=0)
    turns = max(c.get("turn", 0) for c in calls) + 1
    parallel = sum(1 for c in calls if (c.get("parallel_group") or 1) > 1) / n
    terminal = sum(1 for c in calls if c["name"] == "terminal") / n
    sandbox_marker = f"/runs/A/{rec['id']}/sandbox"
    escape = 0
    for c in calls:
        for s in arg_strings(c.get("arguments")):
            if ("/Users/" in s and sandbox_marker not in s) or "cd ~" in s or "$HOME" in s:
                escape += 1
                break
    return dict(calls=n, turns=turns, parallel=round(parallel, 2),
                terminal=round(terminal, 2), escape=escape)

def main():
    rows = []
    for p in sorted(glob.glob("results/run-*/summary.json")):
        run = os.path.basename(os.path.dirname(p))
        d = json.load(open(p))
        recs = [r for r in d["records"] if r["arm"] == "A"]
        if not recs:
            continue
        agg = dict(run=run, n=len(recs), score=sum(r["score"] for r in recs),
                   chk_pass=0, chk_total=0, calls=0, turns=0, escape=0,
                   api=0.0, uncached=0, completion=0, per=[])
        for r in recs:
            cp = sum(1 for c in r["checks"] if c["pass"])
            ct = len(r["checks"])
            t = traj(r)
            u = (r["extra"] or {}).get("usage") or {}
            unc = u.get("prompt_tokens", 0) - ((u.get("prompt_tokens_details") or {}).get("cached_tokens", 0))
            agg["chk_pass"] += cp; agg["chk_total"] += ct
            agg["calls"] += t["calls"]; agg["turns"] += t["turns"]; agg["escape"] += t["escape"]
            agg["api"] += (r["extra"] or {}).get("api_seconds", 0)
            agg["uncached"] += unc; agg["completion"] += u.get("completion_tokens", 0)
            agg["per"].append((r["id"], r["score"], cp, ct, t))
        rows.append(agg)
    for a in rows:
        print(f"== {a['run']}  문항 {a['n']}  시나리오점수 {a['score']:.1f}  "
              f"체크점수 {a['chk_pass']}/{a['chk_total']} ({a['chk_pass']/a['chk_total']*100:.1f}%)  "
              f"호출 {a['calls']} (문항당 {a['calls']/a['n']:.1f})  턴합 {a['turns']}  "
              f"밖접근 {a['escape']}  api {a['api']:.0f}s  비캐시입력 {a['uncached']}  출력 {a['completion']}")
    # 스포트라이트: 시나리오 점수와 체크 점수가 갈리는 기록
    print("\n-- 스포트라이트 (점수 괴리·궤적 특이) --")
    for a in rows:
        for sid, sc, cp, ct, t in a["per"]:
            if (sc < 1.0 and cp > 0) or t["escape"] > 0 or t["terminal"] >= 0.5:
                print(f"{a['run']} {sid}: 시나리오 {sc} vs 체크 {cp}/{ct} | "
                      f"호출 {t['calls']} 턴 {t['turns']} 병렬 {t['parallel']} 터미널 {t['terminal']} 밖접근 {t['escape']}")

if __name__ == "__main__":
    main()
