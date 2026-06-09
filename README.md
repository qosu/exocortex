# EXOCORTEX — Symbiotic AI Wearable

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20602851.svg)](https://doi.org/10.5281/zenodo.20602851)

> *"AI không làm hộ bạn. AI làm bạn giỏi hơn."*

## What is Exocortex?

**Exocortex** is the first Symbiotic AI wearable — an AI that strengthens human cognition through **Socratic questioning** rather than answer-giving. It listens to your conversations in real-time, detects cognitive blindspots, and whispers the right question at the right moment — then deliberately fades as you improve.

### Live Demo
Try it now: **[https://assignee.net/exocortex/client](https://assignee.net/exocortex/client)** (open on Android Chrome)

### The Problem: Brainrot
Current AI systems make us **dumber** by answering questions → we stop thinking.

### The Solution: Symbiotic AI
Exocortex acts as a **process catalyst**, not a database:
- ❌ Never gives answers
- ✅ Asks Socratic questions that trigger YOUR System 2 thinking
- ✅ Detects 8 types of cognitive blindspots in real-time
- ✅ Fades assistance as you master each domain
- ✅ Works on Android phone mic → prompt in <300ms

### Anti-Brainrot Theorem
We prove mathematically: under the Symbiotic protocol, human cognitive capacity is **monotonically non-decreasing**: dC_H/dt ≥ 0

## Quick Start

```bash
# REST API
curl -X POST https://assignee.net/exocortex/detect \
  -H 'Content-Type: application/json' \
  -d '{"text":"Doanh số giảm vì chiến dịch marketing thất bại"}'

# Client
open https://assignee.net/exocortex/client
```

## Repository

| File | Description |
|------|-------------|
| `paper/exocortex_formalism.pdf` | 7-page formal mathematical paper |
| `src/core/exocortex_core.py` | 640-line Python reference implementation |
| `src/pipeline/server.py` | FastAPI server with WebSocket + ASR |
| `src/client/index.html` | Android PWA client with mic capture |
| `patent/exocortex_patent_architecture.md` | 5 patent claims |
| `PLAN.md` | Complete 5-phase development plan |

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
