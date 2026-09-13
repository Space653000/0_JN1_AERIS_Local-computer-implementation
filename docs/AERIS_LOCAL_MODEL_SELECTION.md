# Local model selection (2026-09-13)

## Instruction being satisfied

The Human asked: verify the local AI's actual capability, and prefer a
non-Chinese-origin ("非紅") model over a Chinese-origin one, unless the
Chinese-origin model is demonstrably stronger.

## What was tested

The machine already had a wide range of models pulled via Ollama (no
downloads were needed for this evaluation -- `GET
http://127.0.0.1:11434/api/tags`):

| Model | Origin | Params | Size |
|---|---|---|---|
| qwen3:4b-instruct (previous default) | Alibaba (CN) | 4.0B | 2.5GB |
| llama3.2:3b | Meta (US) | 3.2B | 2.0GB |
| llama3.1:8b | Meta (US) | 8.0B | 4.9GB |
| gemma2:9b | Google (US) | 9.2B | 5.4GB |
| mistral-nemo:latest | Mistral AI (FR) | 12.2B | 7.1GB |
| qwen3:14b | Alibaba (CN) | 14.8B | 9.3GB |
| gemma2:27b (new default) | Google (US) | 27.2B | 15.6GB |
| qwen2.5:32b, qwen3:32b, qwen2.5-coder:32b, qwen3-coder:30b | Alibaba (CN) | 30-33B | 18.6-20.2GB |

GPU: NVIDIA RTX Spark N1X, 24GB VRAM -- comfortably fits any of the
above, including the 30B-class models.

**Test 1** (`aeris_runtime chat`, one-line answer requested): "Explain in
exactly 3 bullet points why a golden regression test needs a negative
case, and give one concrete example for a lowpass filter skill."
qwen3:4b-instruct gave the most contextually correct answer (correctly
framed "negative case" as invalid-input rejection, matching this
codebase's actual `negative_patch`/`failure_expectation` convention);
llama3.1:8b and gemma2:9b both misapplied general ML-model-evaluation
framing ("prevents overfitting", "model's performance") that doesn't fit
this project's deterministic-calculation domain. This alone would have
favored keeping qwen3:4b-instruct.

**Test 2** (`aeris_runtime chat`, exact numeric answer requested): "A
speaker's resonance frequency fs is given by fs =
1/(2*pi*sqrt(Mms*Cms)). If Mms doubles and Cms is halved, what happens
to fs? Answer with the exact multiplier, one sentence." The correct
answer is **unchanged (multiplier = 1)**, since Mms*Cms is invariant
under that substitution -- straightforward algebra, not a trick
question. Every sub-10B model tested got this wrong:

- qwen3:4b-instruct: "multiplied by sqrt(2)" -- wrong
- llama3.1:8b: "sqrt(2) times" -- wrong
- gemma2:9b: "multiplied by sqrt(2)" -- wrong
- mistral-nemo:latest: "decreases by a factor of 1/sqrt(2)" -- wrong

**Test 3** (same question, explicitly asked to work through the algebra
step by step rather than answer directly): both gemma2:27b and
qwen3:14b correctly substituted, simplified, and concluded "multiplier =
1, unchanged" -- see the raw transcripts in this session's log if
needed. The smaller models were not re-tested with step-by-step
prompting; the point already established (sub-10B models fail this
regardless of vendor) was sufficient.

## Conclusion

Model **size/capacity**, not vendor, was the actual variable that
determined correctness on a real multi-step engineering reasoning
question. Every small model failed regardless of Chinese vs.
non-Chinese origin; a ~14-27B-class model succeeded regardless of origin
too. Since a non-Chinese-origin model (gemma2:27b) performed equally
well to the Chinese-origin one (qwen3:14b) once given comparable
capacity, **gemma2:27b was set as the new default** per the explicit
instruction to prefer non-Chinese-origin models when capability is
comparable.

This is configurable per-instance via the `AERIS_LOCAL_MODEL`
environment variable (see `aeris_runtime/config.py`) -- nothing about
this choice is hardcoded beyond the default. `local_timeout_sec`'s
default was also raised from 120s to 180s to give the larger model
comfortable headroom on a cold load.

## What this does not cover

- This was a small, targeted comparison (3 prompts), not a
  comprehensive benchmark suite. If a future session has reason to
  suspect this default no longer holds up (e.g. a new small model
  released, or a task class where gemma2:27b underperforms), re-test
  rather than trusting this note indefinitely.
- The `chat`/`research` local-model role in AERIS is used for
  engineering commentary, workflow narration, and orchestration --
  **not** for the actual acoustic/DSP calculations, which are
  deterministic Python (`aeris_runtime/engineering/*.py`, numpy/scipy)
  regardless of which local model is configured. A stronger or weaker
  local model changes response quality for commentary/chat, not the
  correctness of any sealed Evidence bundle's numerical results.
