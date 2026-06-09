# EXOCORTEX — Symbiotic AI Wearable

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20602851.svg)](https://doi.org/10.5281/zenodo.20602851)

> *"AI không làm hộ bạn. AI làm bạn giỏi hơn."*

## What is Exocortex?

**Exocortex** is the first Symbiotic AI wearable — an AI that strengthens human cognition through **Socratic questioning** rather than answer-giving. It listens to your conversations in real-time, detects cognitive blindspots, and whispers the right question at the right moment — then deliberately fades as you improve.

### The Problem: Brainrot

Current AI systems (ChatGPT, Siri, Alexa) make us **dumber** by:
- Answering questions → we stop thinking
- Summarizing content → we stop reading
- Generating ideas → we stop creating

This is **cognitive offloading** — use it or lose it.

### The Solution: Symbiotic AI

Exocortex acts as a **process catalyst**, not a database:
- ❌ Never gives answers
- ✅ Asks Socratic questions that trigger YOUR System 2 thinking
- ✅ Detects 8 types of cognitive blindspots in real-time
- ✅ Fades assistance as you master each domain
- ✅ Builds personal knowledge graph from daily conversations
- ✅ Runs spaced repetition to consolidate learning

### Anti-Brainrot Theorem

We prove mathematically: under the Symbiotic protocol, human cognitive capacity is **monotonically non-decreasing** over time.

```
dC_H/dt ≥ 0  ∀t
```

## Repository

| File | Description |
|------|-------------|
| `paper/exocortex_formalism.pdf` | 7-page formal mathematical paper |
| `src/core/exocortex_core.py` | 640-line Python reference implementation |
| `patent/exocortex_patent_architecture.md` | 5 patent claims |
| `PLAN.md` | Complete 5-phase development plan |

## Quick Start

```bash
pip install numpy
python src/core/exocortex_core.py
# EXOCORTEX — All tests passed. System operational.
```

## Architecture

```
Conversation → Blindspot Detector → Scaffold Generator → Socratic Prompt
                    ↑                       ↑
              User Model ←── Fading Controller ←── Spaced Repetition
```

8 blindspot types detected in real-time:
B1 Missing Variable · B2 Causal Inversion · B3 Base Rate Neglect · 
B4 Survivorship Bias · B5 Framing Trap · B6 Overgeneralization · 
B7 Temporal Confound · B8 Selection Bias

## Citation

```bibtex
@article{exocortex-2026,
  title   = {EXOCORTEX: A Formal Model of Symbiotic AI for Real-Time Cognitive Enhancement},
  author  = {DeepSeek Research System},
  year    = {2026},
  doi     = {10.5281/zenodo.20602851},
  url     = {https://github.com/qosu/exocortex}
}
```

## License

MIT — Symbiotic AI should be free.
