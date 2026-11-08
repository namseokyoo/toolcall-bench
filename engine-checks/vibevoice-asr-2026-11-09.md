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
