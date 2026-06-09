# EXOCORTEX — Symbiotic AI Wearable
## Master Development Plan v1.0

```
          ┌─────────────────────────────────────────────┐
          │  EXOCORTEX: Vỏ Não Ngoại Vi                   │
          │  "AI không làm hộ bạn. AI làm bạn giỏi hơn."  │
          └─────────────────────────────────────────────┘
```

---

## PHASE 0 — FOUNDATION (Đang thực hiện)

### 0.1 Formal Mathematical Model
**File:** `paper/exocortex_formalism.tex` + `.pdf`
**Nội dung:**
- Định nghĩa toán học Cognitive Scaffold Space S
- Blindspot Distance Metric d_B(s, t) giữa hai cognitive state
- Optimal Prompt Complexity Function C*(u, d) cho user u ở difficulty d
- Fading Function Φ(m, t): mastery m → prompt frequency theo thời gian t
- Chứng minh: dC_H/dt > 0 dưới tác động của Exocortex (không brainrot)
- Chứng minh: tồn tại fixed point Φ(m→∞) = 0 (fading hoàn toàn)
- Định lý: Cognitive Load Balance — AI gánh Hệ thống 1, user bắt buộc vận hành Hệ thống 2

### 0.2 Patent Architecture
**File:** `patent/exocortex_architecture.md`
**Claims:**
1. Method for real-time Socratic prompt generation from conversational audio
2. Fading scaffold system with cognitive mastery tracking
3. Blindspot detection via argumentation mining on edge device
4. Knowledge graph extraction from natural dialogue with spaced repetition integration
5. Predictive turn-boundary inference for sub-200ms prompt delivery

### 0.3 Reference Implementation (Proof-of-Concept)
**File:** `src/core/exocortex_core.py`
**Chạy được ngay trên server hiện tại**, dùng Ollama + Python.

---

## PHASE 1 — CORE INTELLIGENCE (Tuần 1-4)

### 1.1 Blindspot Detection Engine (BDE)
**File:** `src/core/blindspot_detector.py`
**Input:** transcript segment (text)
**Output:** [(type, severity, context, prompt_template)]
**Các loại blindspot:**
| ID | Loại | Mô tả | Prompt template |
|----|------|-------|-----------------|
| B1 | Missing Variable | Thiếu biến kiểm soát | "Có biến nào ngoài {mentioned_vars} ảnh hưởng đến {outcome} không?" |
| B2 | Causal Inversion | Nhân quả ngược | "Liệu {effect} có thể là nguyên nhân của {cause} thay vì ngược lại?" |
| B3 | Base Rate Neglect | Bỏ qua tỉ lệ nền | "Tỉ lệ cơ bản của {event} trong tổng thể là bao nhiêu?" |
| B4 | Survivorship Bias | Thiên kiến sống sót | "Những trường hợp thất bại của {strategy} có đặc điểm gì?" |
| B5 | Framing Trap | Bẫy khung | "Nếu diễn đạt {statement} theo cách ngược lại thì sao?" |
| B6 | Overgeneralization | Khái quát hóa quá mức | "Có counter-example nào cho {generalization} không?" |
| B7 | Temporal Confound | Yếu tố thời gian gây nhiễu | "Có yếu tố mùa vụ hoặc chu kỳ nào ở đây không?" |
| B8 | Selection Bias | Thiên kiến chọn mẫu | "Mẫu {sample} có đại diện cho {population} không?" |

### 1.2 Cognitive Scaffold Generator (CSG)
**File:** `src/core/scaffold_generator.py`
**Pipeline:**
1. Nhận transcript + detected blindspots
2. Xếp hạng blindspots theo severity × user_need (tránh overload)
3. Chọn prompt template phù hợp với ZPD của user
4. Instantiate template với concrete variables từ context
5. Output: single Socratic question (không phải answer)

### 1.3 Turn Boundary Predictor
**File:** `src/core/turn_predictor.py`
**Model:** lightweight (10-50M params), ONNX format
**Input:** audio features (pitch, energy, pause duration, speech rate trend)
**Output:** P(turn_ends_in_N_ms)
**Training:** trên conversational corpus (Switchboard, Fisher, AMI)

### 1.4 User Cognitive Model
**File:** `src/core/user_model.py`
**Theo dõi per user:**
- Cognitive domain mastery scores (vector M ∈ [0,1]^n)
- Fatigue level F(t) từ voice features
- ZPD boundaries per domain
- Prompt response history (đã dùng prompt → đã cải thiện?)
- Fading level Φ per domain

---

## PHASE 2 — KNOWLEDGE PIPELINE (Tuần 5-8)

### 2.1 Real-time Audio Pipeline
**File:** `src/pipeline/audio_stream.py`
**Stack:** WebSocket server ← audio chunks từ client
- Streaming ASR (Whisper tiny/base via ONNX)
- Voice activity detection (silero-vad)
- Speaker diarization (pyannote hoặc simple embedding-based)
- Audio buffer management (ring buffer, 30s window)

### 2.2 Daily Knowledge Graph Extractor
**File:** `src/pipeline/knowledge_graph.py`
**Pipeline (batch, cuối ngày):**
1. Lấy transcript đầy đủ của ngày
2. Chunk → LLM extract entities + relations (Ollama, async)
3. Entity resolution (merge duplicates, link to existing KG)
4. Store vào PostgreSQL + pgvector (embeddings)
5. Output: cập nhật knowledge graph cá nhân

### 2.3 Spaced Repetition Engine
**File:** `src/pipeline/spaced_repetition.py`
**Algorithm:** Modified SM-2 với voice interaction
- Từ knowledge graph, generate câu hỏi kiểm tra
- Schedule theo spaced repetition optimal intervals
- Voice-based quiz session (5-10 phút cuối ngày)
- Cập nhật mastery scores dựa trên response quality

### 2.4 Fading Scaffold Controller
**File:** `src/pipeline/fading_controller.py`
**Logic:**
- Per cognitive domain, track user response accuracy and latency
- Khi accuracy > θ_high và latency < τ_low → tăng fading
- Fading levels: VERBAL_PROMPT → KEYWORD → TONE_CUE → SILENT
- Khi novel concept hoặc fatigue > threshold → reset fading tạm thời

---

## PHASE 3 — CLIENT (Tuần 9-12)

### 3.1 Mobile App (PWA)
**File:** `src/client/` — React + TypeScript
- Audio streaming client (WebSocket)
- User dashboard (mastery scores, KG visualization)
- Reflection session UI (spaced repetition quiz)
- Settings (fading aggressiveness, domain focus)
- Offline mode (cache prompts, sync later)

### 3.2 Wearable Bridge
**File:** `src/client/wearable_bridge.py`
- BLE communication với wearable
- Audio relay: wearable mic → phone → server
- Prompt delivery: server → phone → wearable speaker/display

### 3.3 Notification System
**File:** `src/client/notifications.py`
- End-of-day reflection reminder
- Knowledge graph "weekly review" summary
- Mastery milestone celebrations (gamification nhẹ)

---

## PHASE 4 — HARDWARE (Tuần 13-20)

### 4.1 Hardware Architecture
**File:** `src/hardware/architecture.md`
**Base design:**
- MCU: nRF5340 (dual-core: network + application)
- Mic: ICS-43434 I2S MEMS (low power, high SNR)
- Speaker: bone conduction transducer (discrete, không block tai)
- Battery: 50mAh LiPo (target 8h continuous)
- Connectivity: BLE 5.3 → phone; Wi-Fi optional
- Optional display: 0.26" micro-OLED (text prompts)

### 4.2 Edge Inference
**File:** `src/hardware/edge_inference.md`
- Model quantization cho MCU (TensorFlow Lite Micro)
- SLM cho argumentation mining: distilled model ~10M params
- Turn boundary predictor: ~1M params (DSP-optimized)
- Inference time target: <50ms on Cortex-M33
- Audio preprocessing: on-device VAD, noise suppression

### 4.3 Firmware
**File:** `src/hardware/firmware/`
- Zephyr RTOS
- Audio capture + BLE streaming
- VAD + local inference trigger
- Power management (ultra-low power when silent)
- OTA update capability

---

## PHASE 5 — LAUNCH (Tuần 21-24)

### 5.1 Pilot Program
- 50 beta testers (chọn từ waitlist)
- Domain: business negotiation (focus ban đầu)
- Metrics: user-reported cognitive improvement, prompt usefulness, retention

### 5.2 Manufacturing
- PCB design finalization
- Enclosure design (industrial design)
- CE/FCC certification
- Initial production: 500 units

### 5.3 Go-to-Market
- Product Hunt launch
- Pricing: $299 device + $19.99/month subscription
- Target: professionals, executives, debaters, therapists in training

---

## KIẾN TRÚC KỸ THUẬT TỔNG THỂ

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXOCORTEX SYSTEM                          │
├───────────────┬──────────────────┬──────────────────────────────┤
│   WEARABLE    │   MOBILE (PWA)   │        SERVER                │
│   (nRF5340)   │   (React/TS)     │    (FastAPI/Python)          │
├───────────────┼──────────────────┼──────────────────────────────┤
│               │                  │                               │
│ [Mic I2S]     │                  │  ┌───────────────────────┐   │
│    ↓          │                  │  │  Audio Pipeline       │   │
│ [VAD + NS]    │                  │  │  - ASR (Whisper ONNX) │   │
│    ↓          │  [WebSocket]     │  │  - Diarization        │   │
│ [BLE TX] ──────→ [Audio Relay] ──→  │  - VAD               │   │
│               │                  │  └─────────┬─────────────┘   │
│               │                  │            ↓                 │
│               │                  │  ┌───────────────────────┐   │
│               │                  │  │  Blindspot Detector   │   │
│               │                  │  │  (SLM ONNX, <200ms)   │   │
│  [BLE RX] ←── [Prompt Bridge] ←───  └─────────┬─────────────┘   │
│    ↓          │                  │            ↓                 │
│ [Bone Cond]   │                  │  ┌───────────────────────┐   │
│ [micro-OLED]  │                  │  │  Scaffold Generator   │   │
│               │                  │  │  (LLM select template)│   │
│               │                  │  └─────────┬─────────────┘   │
│               │                  │            ↓                 │
│               │                  │  ┌───────────────────────┐   │
│               │  [Dashboard]     │  │  Fading Controller    │   │
│               │  [Reflection]    │  │  (per user, per domain)│  │
│               │  [Settings]      │  └─────────┬─────────────┘   │
│               │                  │            ↓                 │
│               │                  │  ┌───────────────────────┐   │
│               │                  │  │  Knowledge Graph      │   │
│               │                  │  │  (PostgreSQL+pgvector)│   │
│               │                  │  └─────────┬─────────────┘   │
│               │                  │            ↓                 │
│               │                  │  ┌───────────────────────┐   │
│               │  [Quiz UI] ←───────│  Spaced Repetition     │   │
│               │                  │  │  (nightly batch)      │   │
│               │                  │  └───────────────────────┘   │
└───────────────┴──────────────────┴──────────────────────────────┘
```

## THỨ TỰ XÂY DỰNG (ưu tiên)

1. **RIGHT NOW:** Formal paper + patent doc + core Python module
2. **NEXT:** Blindspot detector + scaffold generator
3. **THEN:** Audio pipeline + turn predictor
4. **AFTER:** Knowledge graph + spaced repetition
5. **CLIENT:** PWA mobile app
6. **LAST:** Hardware spec → prototype

---

## METRICS THÀNH CÔNG

| Metric | Target | Đo bằng |
|--------|--------|---------|
| Prompt usefulness | >70% user rating ≥4/5 | In-app feedback |
| Cognitive improvement | +15% blindspot detection tự nhiên sau 30 ngày | A/B test transcripts |
| Retention | >60% sau 3 tháng | Subscription data |
| Latency (end-to-end) | <300ms từ đối phương dứt lời → prompt đến tai | System logs |
| False prompt rate | <20% prompts bị user bỏ qua | Usage analytics |
| Fading success | >50% domain đạt Φ=max trong 60 ngày | Mastery tracker |

---

*"Symbiotic AI không phải là AI thông minh nhất. 
Là AI khiến con người thông minh nhất."*
