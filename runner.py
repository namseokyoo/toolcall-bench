#!/usr/bin/env python3
"""Tool-calling benchmark runner: Arm A (raw Strata) vs Arm B (Hermes oxalpha).

Runs ON the Mac mini (needs 127.0.0.1:8080 Strata + hermes CLI for arm B).
Stdlib only. Usage:
  python3 runner.py --arm both [--only S1,M2] [--out results/RUN_ID]
Outputs per-scenario records + summary.json + summary.md under --out.
"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.request
import difflib

HERE = os.path.dirname(os.path.abspath(__file__))
STRATA = "http://127.0.0.1:8080/v1"
MAX_TURNS = 8

# ---------------------------------------------------------------- checks
def load_json_from_text(text):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        i, j = text.find(opener), text.rfind(closer)
        if i >= 0 and j > i:
            try:
                return json.loads(text[i:j + 1])
            except Exception:
                continue
    return None

def _contains(hay, needle):
    if needle in hay:
        return True
    # Numeric tolerance: "7,006,652" in the answer should match needle "7006652".
    if any(ch.isdigit() for ch in needle):
        squish = lambda s: s.replace(",", "").replace(" ", "").replace("，", "")
        return squish(needle) in squish(hay)
    return False

def run_checks(scn, sandbox, answer, call_log):
    """Returns (score, [ {check, pass, detail} ]). score in {0, 0.5, 1}."""
    results = []
    for chk in scn["checks"]:
        t = chk["type"]
        ok, detail = False, ""
        try:
            if t == "answer_contains":
                ok = _contains(answer, chk["text"]); detail = "answer contains" if ok else "missing in answer"
            elif t == "answer_contains_any":
                ok = any(_contains(answer, x) for x in chk["texts"]); detail = "matched one" if ok else "none matched"
            elif t == "answer_not_contains":
                ok = not _contains(answer, chk["text"]); detail = "absent (good)" if ok else "LEAKED into answer"
            elif t == "answer_json_equals":
                got = load_json_from_text(answer)
                ok = got == chk["object"]; detail = f"parsed={got!r}"
            elif t == "no_tool_calls":
                ok = len(call_log) == 0; detail = f"{len(call_log)} tool calls made"
            elif t in ("file_equals", "file_contains", "file_not_contains", "file_absent", "json_equals"):
                p = os.path.join(sandbox, chk["path"])
                if t == "file_absent":
                    ok = not os.path.exists(p); detail = "absent" if ok else "still exists"
                elif not os.path.exists(p):
                    ok, detail = False, "file missing"
                elif t == "json_equals":
                    got = json.loads(open(p, encoding="utf-8").read())
                    ok = got == chk["object"]; detail = f"parsed={got!r}"
                else:
                    content = open(p, encoding="utf-8").read()
                    if t == "file_equals":
                        ok = content.strip() == chk["content"].strip(); detail = f"content={content.strip()!r}"
                    elif t == "file_contains":
                        ok = _contains(content, chk["text"]); detail = "found" if ok else "not in file"
                    else:
                        ok = not _contains(content, chk["text"]); detail = "absent (good)" if ok else "still in file"
            else:
                detail = f"unknown check type {t}"
        except Exception as e:
            ok, detail = False, f"check error: {e}"
        results.append({"check": chk, "pass": ok, "detail": detail})
    score = 1.0 if all(r["pass"] for r in results) else 0.0
    # N2-style partial credit: answer right but an unnecessary tool call was made.
    if score == 0.0:
        failed = [r for r in results if not r["pass"]]
        if len(failed) == 1 and failed[0]["check"]["type"] == "no_tool_calls" and \
           any(r["check"]["type"].startswith("answer_") and r["pass"] for r in results):
            score = 0.5
    return score, results

# ---------------------------------------------------------------- arm A
DANGER = re.compile(r"(\brm\b[^|;&]*(-[a-z]*[rf][a-z]*\s+)+(/|~|\$HOME|\.\.)\b)|(\bmkfs\b)|(\bdd\b[^|;&]*of=/dev/)|(\bshutdown\b|\breboot\b)|(:\(\)\s*\{)")

def sandbox_path(sandbox, path):
    p = os.path.realpath(os.path.join(sandbox, path)) if not os.path.isabs(path) \
        else os.path.realpath(path)
    return p

def exec_tool(sandbox, name, args, violations):
    """Execute one tool call inside the sandbox; return result text."""
    try:
        if name == "terminal":
            cmd = args.get("command", "")
            if DANGER.search(cmd):
                violations.append(f"dangerous terminal attempt blocked: {cmd[:120]}")
                return "Error: command blocked by benchmark harness (destructive pattern)."
            timeout = min(int(args.get("timeout") or 60), 120)
            r = subprocess.run(["bash", "-c", cmd], cwd=sandbox, capture_output=True,
                               text=True, timeout=timeout)
            out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
            return (f"[exit {r.returncode}]\n" + out)[:4000] or "[exit 0] (no output)"
        if name == "read_file":
            p = sandbox_path(sandbox, args["path"])
            if not os.path.realpath(p).startswith(os.path.realpath(sandbox)):
                return "Error: path outside working directory."
            if not os.path.exists(p):
                sibs = os.listdir(sandbox)
                sug = difflib.get_close_matches(os.path.basename(args["path"]), sibs, n=3)
                return f"Error: file not found: {args['path']}" + (f". Similar files: {', '.join(sug)}" if sug else "")
            lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            off = int(args.get("offset") or 1); lim = int(args.get("limit") or 2000)
            sel = lines[off - 1: off - 1 + lim]
            return "\n".join(f"{off + i}|{ln}" for i, ln in enumerate(sel)) or "(empty file)"
        if name == "write_file":
            p = sandbox_path(sandbox, args["path"])
            if not os.path.realpath(p).startswith(os.path.realpath(sandbox)):
                return "Error: path outside working directory."
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(args.get("content", ""))
            return f"Wrote {args['path']} ({len(args.get('content',''))} chars)."
        if name == "patch":
            p = sandbox_path(sandbox, args["path"])
            if not os.path.exists(p):
                return f"Error: file not found: {args['path']}"
            c = open(p, encoding="utf-8").read()
            old, new = args.get("old_string", ""), args.get("new_string", "")
            if old not in c:
                return "Error: old_string not found in file."
            c = c.replace(old, new) if args.get("replace_all") else c.replace(old, new, 1)
            open(p, "w", encoding="utf-8").write(c)
            return "Patch applied."
        if name == "search_files":
            pat = args.get("pattern", "")
            base = sandbox_path(sandbox, args.get("path") or ".")
            target = args.get("target") or "content"
            rx = re.compile(pat)
            hits, total = [], 0
            for root, _dirs, files in os.walk(base):
                for fn in sorted(files):
                    fp = os.path.join(root, fn)
                    rel = os.path.relpath(fp, sandbox)
                    if target in ("files", "both") and rx.search(rel):
                        total += 1
                        if len(hits) < int(args.get("limit") or 50):
                            hits.append(f"{rel} (filename match)")
                    if target == "files":
                        continue
                    try:
                        for i, ln in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
                            if rx.search(ln):
                                total += 1
                                if len(hits) < int(args.get("limit") or 50):
                                    hits.append(f"{rel}:{i}: {ln.rstrip()}")
                    except Exception:
                        continue
            return "\n".join(hits) + f"\n({total} total matches)" if hits else "(no matches)"
        return f"Error: unknown tool {name}"
    except subprocess.TimeoutExpired:
        return "Error: command timed out."
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

def strata_model_id(fallback):
    try:
        req = urllib.request.Request(STRATA + "/models")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data["data"][0]["id"]
    except Exception:
        return fallback

def run_arm_a(scn, sandbox, tools, model):
    messages = [{"role": "user", "content": scn["prompt"]}]
    call_log, violations, api_seconds, usage = [], [], 0.0, {}
    answer = ""
    for turn in range(MAX_TURNS):
        body = {"model": model, "messages": messages, "tools": tools,
                "tool_choice": "auto", "temperature": 0}
        req = urllib.request.Request(STRATA + "/chat/completions",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=600) as r:
            resp = json.loads(r.read())
        api_seconds += time.time() - t0
        if resp.get("usage"):
            usage = resp["usage"]
        msg = resp["choices"][0]["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            answer = msg.get("content") or ""
            break
        for c in calls:
            fn = c["function"]["name"]
            raw = c["function"].get("arguments") or "{}"
            try:
                args = json.loads(raw)
            except Exception:
                args = {}
            call_log.append({"turn": turn, "name": fn, "arguments": args,
                             "parallel_group": len(calls)})
            result = exec_tool(sandbox, fn, args, violations)
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
    else:
        answer = "(max turns reached)"
    return answer, call_log, violations, {"api_seconds": round(api_seconds, 2), "usage": usage}

# ---------------------------------------------------------------- arm B
def run_arm_b(scn, sandbox, timeout_b):
    prompt_file = os.path.join(sandbox, "..", "prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(scn["prompt"])
    env = dict(os.environ)
    env["PATH"] = os.path.expanduser("~/.local/bin") + ":/opt/homebrew/bin:" + env.get("PATH", "")
    cmd = ["hermes", "--profile", "oxalpha", "chat", "--query-file", prompt_file,
           "--oneshot", "-Q", "--format", "stream-json", "--in", sandbox, "--yolo"]
    raw_path = os.path.join(sandbox, "..", "b_events.jsonl")
    answer, tokens, duration_ms, event_types = "", {}, None, {}
    with open(raw_path, "w", encoding="utf-8") as raw:
        proc = subprocess.run(cmd, cwd=sandbox, env=env, capture_output=True,
                              text=True, timeout=timeout_b)
        raw.write(proc.stdout)
        if proc.stderr:
            raw.write("\n[stderr]\n" + proc.stderr[-2000:])
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        t = e.get("type", "?")
        event_types[t] = event_types.get(t, 0) + 1
        if t == "result":
            answer = e.get("text") or ""
            tokens = e.get("tokens") or {}
            duration_ms = e.get("duration_ms")
    tool_events = sum(v for k, v in event_types.items() if "tool" in k)
    return answer, tool_events, {"tokens": tokens, "duration_ms": duration_ms,
                                  "event_types": event_types}

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["A", "B", "both"], default="both")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--timeout-b", type=int, default=420)
    a = ap.parse_args()

    scenarios = json.load(open(os.path.join(HERE, "scenarios.json"), encoding="utf-8"))
    tools_doc = json.load(open(os.path.join(HERE, "tools.json"), encoding="utf-8"))
    tools = tools_doc["tools"]
    model = strata_model_id(scenarios["meta"]["model"])
    only = set(x.strip() for x in a.only.split(",") if x.strip())
    run_id = a.out or time.strftime("results/%Y%m%d-%H%M%S")
    out_root = os.path.join(HERE, run_id)
    os.makedirs(out_root, exist_ok=True)
    arms = ["A", "B"] if a.arm == "both" else [a.arm]

    records = []
    for scn in scenarios["scenarios"]:
        if only and scn["id"] not in only:
            continue
        for arm in arms:
            sdir = os.path.join(out_root, "runs", arm, scn["id"])
            sandbox = os.path.join(sdir, "sandbox")
            os.makedirs(sandbox, exist_ok=True)
            for rel, content in (scn.get("setup", {}).get("files") or {}).items():
                p = os.path.join(sandbox, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content)
            t0 = time.time()
            extra, call_log, violations = {}, [], []
            try:
                if arm == "A":
                    answer, call_log, violations, extra = run_arm_a(scn, sandbox, tools, model)
                else:
                    answer, n_tool_events, extra = run_arm_b(scn, sandbox, a.timeout_b)
                    call_log = [{"tool_events_observed": n_tool_events}]
            except Exception as e:
                answer = f"(runner error: {type(e).__name__}: {e})"
            wall = round(time.time() - t0, 2)
            score, check_results = run_checks(scn, sandbox, answer, call_log if arm == "A" else [])
            if violations:
                score = 0.0
            rec = {"id": scn["id"], "category": scn["category"], "arm": arm,
                   "score": score, "wall_seconds": wall, "answer": answer,
                   "calls": call_log, "violations": violations, "extra": extra,
                   "checks": check_results}
            records.append(rec)
            print(f"[{arm}] {scn['id']:>4} score={score} wall={wall}s calls={len(call_log)} "
                  f"{'VIOLATION' if violations else ''}", flush=True)
            with open(os.path.join(sdir, "record.json"), "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False, indent=1)

    with open(os.path.join(out_root, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "model": model, "records": records}, f,
                  ensure_ascii=False, indent=1)
    lines = [f"# Benchmark run {run_id}", f"model: `{model}`", "",
             "| 시나리오 | 카테고리 | A 점수 | A 시간(s) | B 점수 | B 시간(s) |",
             "|---|---|---|---|---|---|"]
    by_id = {}
    for r in records:
        by_id.setdefault(r["id"], {})[r["arm"]] = r
    tot = {"A": [0, 0.0], "B": [0, 0.0]}
    cats = {}
    for scn in scenarios["scenarios"]:
        if scn["id"] not in by_id:
            continue
        row = by_id[scn["id"]]
        cells = []
        for arm in ("A", "B"):
            r = row.get(arm)
            cells += [str(r["score"]) if r else "-", str(r["wall_seconds"]) if r else "-"]
            if r:
                tot[arm][0] += r["score"]; tot[arm][1] += r["wall_seconds"]
                c = cats.setdefault(scn["category"], {"A": 0, "B": 0, "n": 0})
                c[arm] += r["score"]
        for arm in ("A", "B"):
            if row.get(arm):
                cats[scn["category"]]["n"] += 1 if arm == "A" or not row.get("A") else 0
                break
        lines.append(f"| {scn['id']} | {scn['category']} | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |")
    lines += ["", "## 카테고리별", "| 카테고리 | 문항 | A | B |", "|---|---|---|---|"]
    for c, v in cats.items():
        lines.append(f"| {c} | {v['n']} | {v['A']} | {v['B']} |")
    lines += ["", f"**총점: A {tot['A'][0]} · B {tot['B'][0]}** (실행된 시나리오 기준)",
              f"**총 시간: A {round(tot['A'][1],1)}s · B {round(tot['B'][1],1)}s**", "",
              "주: B는 실제 oxalpha 프로필(게이트웨이 경유, --yolo)로 실행. A는 temperature 0. "
              "B의 `no_tool_calls` 체크는 스트림 이벤트로 확정할 수 없어 채점에서 제외했다."]
    with open(os.path.join(out_root, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
