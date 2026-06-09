# EXOCORTEX — Patent Architecture
## Symbiotic AI Wearable System for Real-Time Cognitive Enhancement
### Invention Disclosure Document — June 2026

---

## CLAIM 1: METHOD FOR REAL-TIME SOCRATIC PROMPT GENERATION FROM CONVERSATIONAL AUDIO

### Technical Field
Human-computer interaction, natural language processing, cognitive augmentation, wearable computing.

### Abstract
A method for generating Socratic prompts — questions that trigger analytical reasoning without providing answers — in real-time from conversational audio. The system captures audio via a wearable microphone, performs streaming automatic speech recognition (ASR), detects cognitive blindspots in the recognized text using a fine-tuned argumentation mining model, and generates a single Socratic question matched to the user's Zone of Proximal Development (ZPD). The question is delivered via bone conduction speaker or micro-display within 300ms of the conversation partner completing their utterance.

### Claim Elements

**E1 — Audio Capture Subsystem**
- Wearable MEMS microphone array (I2S interface)
- On-device Voice Activity Detection (VAD) and noise suppression
- Continuous audio streaming via BLE 5.3 to companion phone
- Ring buffer architecture for rewind-to-utterance-boundary

**E2 — Streaming ASR Engine**
- ONNX-runtime Whisper (tiny or base) running on phone/edge
- Streaming decoder producing partial transcripts with <100ms latency per token
- Speaker diarization via embedding clustering (ECAPA-TDNN embeddings)

**E3 — Cognitive Blindspot Detector**
- 8-class blindspot classifier: missing variable, causal inversion, base rate neglect, survivorship bias, framing trap, overgeneralization, temporal confound, selection bias
- Fine-tuned SLM (10-50M parameters) specialized in argumentation mining
- Input: last N utterances (sliding window, ~500 tokens)
- Output: blindspot activation vector b ∈ [0,1]^8
- Inference latency: <50ms on device (ONNX Runtime on phone GPU/NPU)

**E4 — Socratic Scaffold Generator**
- Template library: 200+ Socratic question templates organized by blindspot type
- Template selection: argmax over utility function U(p,u,s) combining ZPD-fit, blindspot severity, and overload penalty
- Template instantiation: fill variables using named entity recognition output from ASR
- Spoil level constraint: σ(p) < σ_max (system prohibited from answer-giving)
- Output: single, concrete, context-specific question

**E5 — Prompt Delivery Subsystem**
- Bone conduction speaker: discrete audio delivery
- Micro-OLED display: optional text delivery
- Delivery timing: synchronized with turn boundary prediction (<300ms after speaker transition)
- Volume/visibility adaptive to ambient noise and user preference

### Novelty
No existing system generates real-time Socratic questions from conversational audio. Current AI assistants (Siri, Google Assistant, Alexa, ChatGPT) are answer-giving systems. This method is the first to operate as a pure process catalyst — understanding the conversation, detecting reasoning gaps, but forcing the user to complete the reasoning independently.

### Priority Date
June 9, 2026

---

## CLAIM 2: FADING SCAFFOLD SYSTEM WITH COGNITIVE MASTERY TRACKING

### Abstract
A system that automatically reduces AI assistance as the user demonstrates competence in a cognitive domain. The system maintains a per-domain mastery vector m(t) ∈ [0,1]^n updated via spaced repetition performance and blindspot detection rate. A fading function Φ(m) maps mastery to assistance level, transitioning through VERBAL → KEYWORD → TONE → SILENT levels. The system includes a fatigue override that temporarily increases assistance when voice-based fatigue detection exceeds threshold.

### Claim Elements

**E1 — Cognitive Mastery Tracker**
- n-dimensional mastery vector m(t) covering: causal reasoning, statistical thinking, logical fallacy detection, probabilistic judgment, framing awareness, generalization control, temporal analysis, sampling awareness
- Update mechanism: mastery_d += η · (performance_d - mastery_d) where performance_d is measured via spaced repetition quiz accuracy AND naturalistic blindspot detection rate
- Decay mechanism: mastery_d *= (1 - δ) for each day without domain exercise

**E2 — Fading Function**
- Φ_d(m_d) = max(0, 1 - (m_d - θ_low)/(θ_high - θ_low))
- Maps to 4 discrete levels: VERBAL (>0.75), KEYWORD (0.50-0.75), TONE (0.25-0.50), SILENT (<0.25)
- Domain-independent fading: each domain fades independently based on its own mastery

**E3 — Fatigue Detection and Override**
- Voice feature extraction: jitter, shimmer, HNR, speech rate, pause duration
- Fatigue classifier F(t) ∈ [0,1] updated every 30s
- Override: Φ_eff(t) = min(1, Φ(m) + λ_F · max(0, F(t) - F_crit))
- Re-engagement: when novel blindspot type detected, temporarily reset fading for that domain

**E4 — Prompt Budget Controller**
- N_prompts(t, Δ) ≤ N_max · sigmoid(k(Φ - Φ_0))
- Monotonically decreasing prompt frequency as fading progresses
- Prevents over-prompting and user fatigue

### Novelty
No existing AI system deliberately reduces its own assistance as the user improves. All current systems (spell-check, code completion, navigation, AI assistants) maintain or increase assistance over time, creating dependency. The fading scaffold is the first AI control system designed to make itself obsolete per domain.

---

## CLAIM 3: COGNITIVE BLINDSPOT DETECTION VIA ARGUMENTATION MINING ON EDGE DEVICE

### Abstract
A lightweight neural network (~10M parameters) running on-device (phone GPU/NPU or wearable MCU) that analyzes conversational text in real-time to detect 8 categories of cognitive blindspots. The model is trained on a corpus of annotated arguments and logical fallacies, distilled from a larger teacher model (LLM), and optimized for <50ms inference latency.

### Claim Elements

**E1 — Model Architecture**
- Base: distilled transformer (BERT-tiny scale, ~10M params)
- Input: tokenized utterance window (max 512 tokens), speaker-labeled
- Output: 8-dimensional vector b ∈ [0,1]^8
- Training: teacher-student distillation from LLM (70B+) with chain-of-thought reasoning traces
- Quantization: INT8 post-training quantization for edge deployment

**E2 — Blindspot Taxonomy**
- B1: Missing Variable — causal claim without covariate control
- B2: Causal Inversion — potential reversal of causal direction
- B3: Base Rate Neglect — probabilistic claim ignoring P(A)
- B4: Survivorship Bias — only successful cases considered
- B5: Framing Trap — linguistic framing constraining solution space
- B6: Overgeneralization — pattern extended beyond valid domain
- B7: Temporal Confound — time as unacknowledged confound
- B8: Selection Bias — unrepresentative sample

**E3 — Training Data Generation Pipeline**
- Source: online debate corpora, academic argumentation datasets, LLM-generated synthetic arguments
- Annotation: LLM identifies blindspots with reasoning trace → human verification on subset → train student
- Augmentation: paraphrasing, negation, entity substitution

**E4 — Edge Deployment**
- ONNX Runtime on mobile GPU/NPU
- Optional: TensorFlow Lite Micro for MCU deployment (further quantized to INT4)
- Target inference: <50ms on smartphone, <200ms on wearable MCU

---

## CLAIM 4: KNOWLEDGE GRAPH EXTRACTION FROM NATURAL DIALOGUE WITH SPACED REPETITION INTEGRATION

### Abstract
A batch processing pipeline that extracts a personal knowledge graph from daily conversational transcripts, merges it with existing knowledge, and generates spaced repetition quiz questions scheduled at optimal intervals. The system uses a local LLM for extraction (privacy-preserving) and a modified SM-2 algorithm for scheduling voice-interactive review sessions.

### Claim Elements

**E1 — Transcript-to-Graph Extraction**
- Daily transcript (full day) → chunked → LLM extracts (entity, relation, entity) triples
- Entity resolution: merge co-referring entities across chunks using embedding similarity
- Graph storage: PostgreSQL + pgvector for hybrid (structured + embedding) queries
- Privacy: all processing on-device or on user-owned server; no cloud upload

**E2 — Question Generation**
- From graph triples, generate fact-recall AND conceptual questions
- Conceptual: "You learned about {concept} today. How does it relate to {other_concept}?"
- Factual: "What is the key principle behind {entity}?"
- Application: "How would you apply {concept} to {novel_scenario}?"

**E3 — Spaced Repetition Scheduling**
- Modified SM-2 algorithm with voice response scoring
- Intervals: 1, 3, 7, 21, 60, 180 days (adjusted by response quality)
- Voice interaction: TTS asks question → user speaks answer → ASR → embedding similarity to reference answer → score (0-5)
- Score 0-2: reset interval; Score 3: repeat; Score 4-5: advance interval

**E4 — Mastery Update Loop**
- Quiz performance → updates m(t) per domain
- m(t) → updates fading Φ(t)
- Closes the cognitive enhancement feedback loop

---

## CLAIM 5: PREDICTIVE TURN-BOUNDARY INFERENCE FOR SUB-300MS PROMPT DELIVERY

### Abstract
A lightweight model that predicts conversation turn boundaries from streaming audio features, enabling the scaffold generator to begin inference BEFORE the current speaker finishes their utterance. This reduces end-to-end prompt delivery latency below the 300ms threshold required for natural conversation flow.

### Claim Elements

**E1 — Audio Feature Extraction**
- Real-time features: pitch (F0), energy (RMS), zero-crossing rate, spectral centroid
- Sliding window: 200ms frames, 50ms stride
- Derived features: speech rate trend, pause duration, pitch declination slope

**E2 — Turn Boundary Predictor Architecture**
- Model: lightweight LSTM or TCN (~1M parameters)
- Input: feature sequence (last 2s = 40 frames)
- Output: P(turn_ends_in_next_N_ms) for N ∈ {0, 100, 200, 300, 500, 1000}
- Training: Switchboard + Fisher + AMI meeting corpora (turn-annotated)
- Inference: <5ms on CPU

**E3 — Speculative Execution Pipeline**
- When P(turn_ends_in_200ms) > 0.7: trigger blindspot detection on current partial transcript
- When turn actually ends: scaffold generator already has blindspot vector ready
- Expected latency reduction: 50-100ms (blindspot detection overlaps with speaker's final syllables)

**E4 — Fallback Protocol**
- If turn prediction false-positive (speaker continues): discard generated prompt, reset
- If turn prediction false-negative (speaker stops unexpectedly): run full pipeline, accept 500ms latency
- Adaptive threshold: adjust P_threshold based on speaker's turn-taking style (learned per speaker)

---

## PRIOR ART DISTINCTION

| Existing System | Type | Why Different |
|----------------|------|---------------|
| Siri/Alexa/Google | Answer-giving assistant | Opposite paradigm |
| ChatGPT/Claude | Answer generation | Provides answers, not questions |
| Grammarly | Writing correction | Passive, not real-time conversational |
| Oura/Whoop | Health monitoring | Physiological, not cognitive |
| Friend/Tab AI | Conversation recording | Summarizes, doesn't enhance thinking |
| Humane AI Pin | AI wearable | Answer-giving, failed product |
| Omi | Open-source wearable | General purpose, no cognitive focus |

**Exocortex is the first system that:**
1. Operates in real-time conversation
2. Detects cognitive blindspots
3. Generates Socratic questions (not answers)
4. Fades assistance as user improves
5. Integrates with spaced repetition for long-term learning

---

## IMPLEMENTATION NOTES

- All claims are implementable with current technology (2026)
- Core AI: fine-tuned SLM for blindspot detection + LLM for batch knowledge extraction
- Hardware: nRF5340 or similar BLE MCU + MEMS mic + bone conduction
- Software: Python backend + React Native mobile + Zephyr RTOS firmware
- Patent strategy: file provisional first, then PCT within 12 months

---

*Document prepared by DeepSeek AI Research System — June 9, 2026*
