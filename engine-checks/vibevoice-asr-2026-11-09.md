# VibeVoice-ASR 3-way check (2026-11-09, Mac mini M5 Pro 64GB)

Question: can VibeVoice replace the WatchNote STT leg (Groq whisper-large-v3-turbo + pyannote)?

## Arms & conditions
- **7B full**: microsoft/VibeVoice-ASR FP16 (17.3GB), MPS, official repo processor + modular model (transformers 4.57 venv; native transformers 5.22 processor lacks preprocessor_config in repo). Audio resampled to 24kHz (processor does NOT resample ndarray input — feeding 16kHz as-is yields "[Unintelligible Speech]"). Greedy decoding; eos must be passed explicitly ([151645, 151643]) or generation runs to the token cap.
- **BitNet**: microsoft/VibeASR.cpp, VAE I8_S + LM I2_S (1.58GB), CPU 3 threads.
- **Groq**: whisper-large-v3-turbo API, language=ko, verbose_json segments.
- pyannote arm not run: gated models, no HF token found on mini/home server (production keeps it in Colab). Open item.

## Samples (386s total, ground truth available)
TTS dialogues (Yuna + pitch-shifted voice): meeting 42.8s/6 turns, long multi-topic 90.0s/14 turns, code-switching 44.2s/6, fast speech (rate 250) 18.9s/4, noisy (pink noise) 42.8s/6. Real speech: FLEURS ko_kr test first 12 utterances concatenated, 147.3s.

## CER % (whitespace/punct stripped, Arabic numerals converted to Korean readings on both sides, [Silence] tags stripped)
| sample | 7B | Groq turbo | BitNet |
|---|---|---|---|
| meeting 42.8s | 0.5 | 3.3 | 8.2 |
| long dialogue 90s | 2.7 | 3.5 | 37.5 |
| code-switch 44s | 5.1 | 6.1 | 19.4 |
| fast 19s | 0.9 | 0.9 | 13.6 |
| noisy 43s | 2.2 | 2.7 | 10.3 |
| FLEURS real 147s | 3.5 | 2.6 | 56.2 |
| **mean** | **2.5** | **3.2** | **24.2** |

## Diarization (7B built-in Who/When/What JSON)
- Turn-perfect on meeting (6/6), long (14/14), code-switch (6/6), noisy (6/6).
- **Unstable on fast dialogue**: repeated runs of the same file flip between 4 segments [0,1,0,1] and 2 merged segments [0,0] (MPS greedy nondeterminism). Text CER unaffected.
- FLEURS (12 different readers): 13 content segments, 3 speaker clusters — under-segmented.

## Speed
- 7B: load 25s once; generation RTF ~0.5 (decode ~15-19 tok/s MPS FP16). Some runs inflated by concurrent BitNet batch.
- Groq: 0.5-1.2s wall per file (API) — RTF ~0.01.
- BitNet: RTF 0.22-0.27 clean (3 threads); long files truncate (FLEURS: only first 6/12 utterances emitted; long dialogue: 10/14 turns).

## Verdict
- 7B quality ≈ Groq on Korean dialogue (slightly ahead), Groq ahead on clean read speech — same domain split as the official card. 7B adds diarization+timestamps in one pass, but must run on the mini (not the home server), is ~50x slower than the Groq API path, and its diarization can flip between runs on MPS.
- BitNet: rejected. Quality collapses with length, no speaker labels. Not viable even as an offline fallback beyond ~1 min clips.

## Addendum: Groq whisper-large-v3 (non-turbo), same samples
Mean CER 3.2% — identical to turbo (per-sample: 3.8 / 2.7 / 6.1 / 0.9 / 3.3 / 2.6). Same signature errors as turbo: 우도→"5도", 이유식 garbled ("아이유식"; turbo wrote "IEU식"), and the same hallucinated "감사합니다." appended after the final FLEURS utterance. v3 fixed 북발트해 (turbo: 북바이트해). API latency ~1.0-1.7s/file vs turbo 0.5-1.2s. Conclusion: on Korean, Groq turbo loses nothing against full v3; the 7B-vs-Groq comparison is unchanged either way.

## Addendum: pyannote diarization vs 7B built-in (2026-11-09, later session)
Question (user): is WatchNote's current pyannote diarization worse than the 7B's built-in Who? Method: pyannote speaker-diarization-3.1 pipeline run locally on the mini (pyannote.audio 4.0.7, torch 2.15.0, CPU; segmentation-3.0 + wespeaker-resnet34-LM + community-1 PLDA, all local files, 3.1 config/threshold), scored per GT turn by overlap-majority speaker with best label mapping. Groq+pyannote = Groq transcript segments labeled by pyannote majority speaker (the WatchNote production shape).

| sample | pyannote | 7B built-in | Groq+pyannote |
|---|---|---|---|
| meeting 6 turns (Eddy vs Flo) | 1.00 (2 spk) | 1.00 | 1.00 |
| long 14 turns (Yuna vs Yuna+25% pitch) | 0.50 (merged to 1 spk) | 1.00 | 0.50 |
| code-switch 6 turns (same pair) | 0.50 (merged) | 1.00 | 0.50 |
| fast 4 turns (same pair) | 1.00 (2 spk) | 0.50 (merged; run-unstable) | 1.00 |
| noisy 6 turns (Eddy/Flo + pink noise) | 0.50 (merged) | 1.00 | 0.50 |
| **total 36 turns** | **23/36 (0.64)** | **34/36 (0.94)** | **23/36 (0.64)** |
| FLEURS 12 readers | 4 clusters | 3 clusters | - |

- Speed (386s audio): pyannote CPU 126.1s total (RTF 0.33, load 0.3s) vs 7B generation 278.3s (RTF 0.72, load ~20s). Groq API transcription itself is 0.5-1.7s per file.
- pyannote's three merges have two distinct causes: voice-embedding clustering cannot separate the same TTS voice pitch-shifted +25% in the longer files (the short fast file did split), and pink noise collapsed the Eddy/Flo distinction entirely. Both are robustness warnings, but the same-voice pair is a synthetic edge case — real meetings have genuinely different voices, where the meeting/FLEURS pattern (pyannote at least on par) is the better guide.
- FLEURS cuts the other way: on real multi-reader speech both under-split badly (4 vs 3 of 12), pyannote marginally ahead.
- Verdict: on this dialogue set the 7B's built-in diarization clearly beats pyannote, and swapping WatchNote's diarizer to the 7B would also remove the separate diarization pass — at the cost of a 17GB model at RTF ~0.7 on the mini plus MPS run-to-run instability. A real WatchNote recording with known speakers is the deciding test that neither synthetic set can substitute for.
