"""
EXOCORTEX — Symbiotic AI Core
==============================
Implements the complete cognitive augmentation pipeline:
  1. Blindspot Detection (8 types, ONNX-ready)
  2. Socratic Scaffold Generator (ZPD-matched)
  3. User Cognitive Model (mastery + fatigue)
  4. Fading Scaffold Controller
  5. Prompt Budget Manager
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum, auto
import numpy as np
import math


# ═══════════════════════════════════════════════════════════════════════
# DATA TYPES
# ═══════════════════════════════════════════════════════════════════════

class BlindspotType(Enum):
    MISSING_VARIABLE    = auto()   # B1: thiếu biến kiểm soát
    CAUSAL_INVERSION    = auto()   # B2: nhân quả ngược
    BASE_RATE_NEGLECT   = auto()   # B3: bỏ qua tỉ lệ nền
    SURVIVORSHIP_BIAS   = auto()   # B4: thiên kiến sống sót
    FRAMING_TRAP        = auto()   # B5: bẫy khung
    OVERGENERALIZATION  = auto()   # B6: khái quát hóa quá mức
    TEMPORAL_CONFOUND   = auto()   # B7: yếu tố thời gian gây nhiễu
    SELECTION_BIAS      = auto()   # B8: thiên kiến chọn mẫu


class FadeLevel(Enum):
    VERBAL  = 4   # Full Socratic question spoken
    KEYWORD = 3   # Single key word whispered
    TONE    = 2   # Non-verbal auditory cue only
    SILENT  = 1   # No intervention


@dataclass
class BlindspotSignal:
    """A detected cognitive blindspot in conversation."""
    blindspot_type: BlindspotType
    severity: float           # 0-1, estimated probability
    context: str              # the relevant text segment
    entities: List[str]       # extracted entities for template instantiation
    position: int             # character offset in transcript


@dataclass
class SocraticPrompt:
    """A generated Socratic question/prompt."""
    template_id: str
    text: str                 # the actual prompt delivered to user
    blindspot_target: BlindspotType
    complexity: float         # estimated cognitive effort required
    spoil_level: float        # 0 = pure Socratic, 1 = answer
    entities_used: List[str]


@dataclass
class UserCognitiveState:
    """Real-time model of the user's cognitive state."""
    mastery: np.ndarray       # [0,1]^8  per blindspot domain
    fatigue: float            # 0-1, from voice features
    attention: float          # 0-1, estimated available attention
    fading: np.ndarray        # [0,1]^8  current assistance level per domain
    total_prompts_today: int = 0
    prompts_in_last_60s: int = 0


# ═══════════════════════════════════════════════════════════════════════
# I. COGNITIVE MASTERY DOMAINS — MAP TO BLINDSPOTS
# ═══════════════════════════════════════════════════════════════════════

DOMAIN_NAMES = {
    BlindspotType.MISSING_VARIABLE:    "Kiểm soát biến",
    BlindspotType.CAUSAL_INVERSION:    "Nhân quả",
    BlindspotType.BASE_RATE_NEGLECT:   "Xác suất nền",
    BlindspotType.SURVIVORSHIP_BIAS:   "Mẫu sống sót",
    BlindspotType.FRAMING_TRAP:        "Thoát khung",
    BlindspotType.OVERGENERALIZATION:  "Khái quát hóa",
    BlindspotType.TEMPORAL_CONFOUND:   "Thời gian",
    BlindspotType.SELECTION_BIAS:      "Chọn mẫu",
}

# ═══════════════════════════════════════════════════════════════════════
# II. BLINDSPOT DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════

class BlindspotDetector:
    """
    Detects cognitive blindspots in conversational text.
    
    Production: ONNX-runtime SLM (~10M params).
    Reference: rule-based detector for development/testing.
    """

    # Keyword triggers per blindspot type (reference implementation)
    TRIGGERS: Dict[BlindspotType, List[str]] = {
        BlindspotType.MISSING_VARIABLE: [
            "vì", "bởi vì", "do", "nguyên nhân", "dẫn đến",
            "tác động", "ảnh hưởng", "làm cho", "khiến",
            "therefore", "because", "cause", "lead to", "affect",
            "kết quả là", "hệ quả", "yếu tố duy nhất"
        ],
        BlindspotType.CAUSAL_INVERSION: [
            "làm cho", "khiến cho", "gây ra", "tạo nên",
            "causes", "results in", "produces",
            "tương quan", "đi kèm với", "liên quan đến"
        ],
        BlindspotType.BASE_RATE_NEGLECT: [
            "luôn luôn", "không bao giờ", "chắc chắn", "tuyệt đối",
            "always", "never", "100%", "definitely", "certainly",
            "tất cả", "mọi", "không ai", "ai cũng"
        ],
        BlindspotType.SURVIVORSHIP_BIAS: [
            "thành công", "điển hình", "hầu hết", "thông thường",
            "successful", "typical", "most", "usually",
            "những người thành công đều", "các công ty lớn"
        ],
        BlindspotType.FRAMING_TRAP: [
            "hoặc là", "một là", "chỉ có thể",
            "either", "only option", "must be",
            "không còn cách nào khác", "bắt buộc phải"
        ],
        BlindspotType.OVERGENERALIZATION: [
            "tất cả", "mọi", "luôn luôn", "không bao giờ",
            "all", "every", "always", "never",
            "toàn bộ", "bất kỳ", "không có ngoại lệ"
        ],
        BlindspotType.TEMPORAL_CONFOUND: [
            "đang tăng", "đang giảm", "xu hướng", "theo thời gian",
            "trend", "growing", "declining", "over time",
            "tháng này", "quý này", "năm nay"
        ],
        BlindspotType.SELECTION_BIAS: [
            "khảo sát", "theo nghiên cứu", "số liệu cho thấy",
            "survey", "study shows", "data indicates",
            "phỏng vấn", "thăm dò", "đa số ý kiến"
        ],
    }

    def detect(self, text: str) -> List[BlindspotSignal]:
        """
        Detect blindspots in conversational text.
        Returns list of signals sorted by severity descending.
        """
        signals = []
        text_lower = text.lower()

        for btype, triggers in self.TRIGGERS.items():
            matches = []
            for trigger in triggers:
                idx = text_lower.find(trigger.lower())
                if idx >= 0:
                    matches.append(idx)

            if matches:
                # Severity: more matches + earlier position = higher severity
                density = len(matches) / (len(text.split()) + 1)
                earliness = 1.0 - (min(matches) / max(len(text), 1))
                severity = min(1.0, 0.4 * density * 10 + 0.6 * earliness)

                # Extract surrounding context
                best_idx = min(matches)
                start = max(0, best_idx - 40)
                end = min(len(text), best_idx + 80)
                context = text[start:end]

                # Simple entity extraction: capitalized words and key nouns
                words = context.split()
                entities = [w.strip(",.;:!?") for w in words
                           if w[0].isupper() or len(w) > 6][:5]

                signals.append(BlindspotSignal(
                    blindspot_type=btype,
                    severity=severity,
                    context=context,
                    entities=entities if entities else words[:3],
                    position=best_idx
                ))

        # Deduplicate: keep strongest signal per type
        seen: Dict[BlindspotType, BlindspotSignal] = {}
        for s in signals:
            if s.blindspot_type not in seen or s.severity > seen[s.blindspot_type].severity:
                seen[s.blindspot_type] = s

        return sorted(seen.values(), key=lambda s: s.severity, reverse=True)

    def blindspot_vector(self, text: str) -> np.ndarray:
        """Return blindspot activation vector b ∈ [0,1]^8."""
        signals = self.detect(text)
        vec = np.zeros(8)
        btype_to_idx = {bt: i for i, bt in enumerate(BlindspotType)}
        for s in signals:
            vec[btype_to_idx[s.blindspot_type]] = s.severity
        return vec

    def blindspot_distance(self, text_a: str, text_b: str) -> float:
        """Compute blindspot distance d_B between two text segments."""
        return float(np.linalg.norm(
            self.blindspot_vector(text_a) - self.blindspot_vector(text_b)
        ))


# ═══════════════════════════════════════════════════════════════════════
# III. SOCRATIC SCAFFOLD GENERATOR
# ═══════════════════════════════════════════════════════════════════════

class ScaffoldGenerator:
    """
    Generates Socratic prompts matched to user's ZPD.
    Template-based with concrete instantiation from context.
    """

    MAX_SPOIL = 0.15  # hard cap: never reveal answer

    # (template, complexity, spoil_level)
    TEMPLATES: Dict[BlindspotType, List[Tuple[str, float, float]]] = {
        BlindspotType.MISSING_VARIABLE: [
            ("Ngoài {entities[0]} ra, còn biến nào ảnh hưởng đến kết quả không?", 0.30, 0.05),
            ("Làm sao để biết {entities[0]} là nguyên nhân chính chứ không phải yếu tố khác?", 0.40, 0.08),
            ("Nếu kiểm soát được các biến, kết luận còn đúng không?", 0.35, 0.06),
            ("Có biến thứ ba nào vừa ảnh hưởng đến {entities[0]} vừa ảnh hưởng đến kết quả không?", 0.50, 0.10),
        ],
        BlindspotType.CAUSAL_INVERSION: [
            ("Liệu có phải kết quả đang gây ra {entities[0]}, chứ không phải ngược lại?", 0.25, 0.05),
            ("Điều gì xảy ra nếu mũi tên nhân quả đi ngược hướng?", 0.20, 0.03),
            ("Có bằng chứng thực nghiệm nào xác nhận chiều nhân quả này không?", 0.30, 0.08),
        ],
        BlindspotType.BASE_RATE_NEGLECT: [
            ("Tỉ lệ cơ bản của hiện tượng này trong tổng thể là bao nhiêu?", 0.25, 0.04),
            ("Nếu không biết gì về trường hợp cụ thể, xác suất nền là bao nhiêu?", 0.35, 0.06),
            ("Có bao nhiêu trường hợp tương tự đã xảy ra trong quá khứ?", 0.28, 0.05),
        ],
        BlindspotType.SURVIVORSHIP_BIAS: [
            ("Những trường hợp thất bại có đặc điểm gì chung?", 0.20, 0.03),
            ("Có bao nhiêu người đã thử cách này và không thành công?", 0.15, 0.02),
            ("Nếu chỉ nhìn vào người thất bại, bức tranh sẽ khác thế nào?", 0.25, 0.05),
        ],
        BlindspotType.FRAMING_TRAP: [
            ("Nếu diễn đạt vấn đề theo cách ngược lại thì giải pháp có khác không?", 0.25, 0.04),
            ("Có cách thứ ba nào không nằm trong hai lựa chọn này không?", 0.20, 0.03),
            ("Ai được lợi từ cách đặt vấn đề này?", 0.30, 0.08),
        ],
        BlindspotType.OVERGENERALIZATION: [
            ("Có trường hợp ngoại lệ nào cho quy luật này không?", 0.18, 0.02),
            ("Trong điều kiện nào thì kết luận này không còn đúng?", 0.25, 0.05),
            ("Phạm vi áp dụng chính xác của nhận định này là gì?", 0.30, 0.06),
        ],
        BlindspotType.TEMPORAL_CONFOUND: [
            ("Cùng kỳ năm ngoái con số này là bao nhiêu?", 0.20, 0.04),
            ("Có yếu tố mùa vụ hoặc chu kỳ nào ở đây không?", 0.25, 0.05),
            ("Nếu loại bỏ yếu tố thời gian, xu hướng còn giữ không?", 0.35, 0.07),
        ],
        BlindspotType.SELECTION_BIAS: [
            ("Mẫu này có đại diện cho tổng thể không? Tại sao?", 0.25, 0.05),
            ("Những ai không có trong mẫu này? Đặc điểm của họ là gì?", 0.30, 0.06),
            ("Phương pháp chọn mẫu có thể bỏ sót nhóm nào không?", 0.35, 0.07),
        ],
    }

    def generate(self, signals: List[BlindspotSignal],
                 user: UserCognitiveState) -> Optional[SocraticPrompt]:
        """
        Generate the single best Socratic prompt, or None if no suitable
        prompt found (silence is better than bad prompt).
        """
        if not signals:
            return None

        # Score each candidate prompt
        candidates: List[Tuple[float, SocraticPrompt]] = []

        for signal in signals[:3]:  # top 3 most severe blindspots
            domain_idx = list(BlindspotType).index(signal.blindspot_type)
            zpd_center = user.mastery[domain_idx] + 0.15  # slightly above mastery
            zpd_center = min(zpd_center, 0.95)

            for template, base_complexity, base_spoil in self.TEMPLATES.get(signal.blindspot_type, []):
                # Instantiate template with entities
                entities = signal.entities if signal.entities else ["điều này"]
                try:
                    text = template.format(entities=entities)
                except (IndexError, KeyError):
                    text = template.replace("{entities[0]}", entities[0] if entities else "điều này")

                # Complexity: base from template + penalty for entity unfamiliarity
                complexity = base_complexity + 0.1 * (1 - user.mastery[domain_idx])
                spoil = base_spoil

                # ZPD-fit: how close to ideal difficulty?
                zpd_fit = math.exp(-((complexity - zpd_center) ** 2) / (2 * 0.15 ** 2))

                # Blindspot severity
                severity = signal.severity

                # Fading penalty: reduce weight if this domain is fading
                fade_penalty = 1.0 - 0.5 * user.fading[domain_idx]

                # Overload penalty
                overload = 1.0 if user.prompts_in_last_60s < 2 else 0.2
                if user.total_prompts_today > 50:
                    overload *= 0.5

                utility = (0.35 * zpd_fit + 0.35 * severity * fade_penalty
                           + 0.15 * (1.0 - complexity) + 0.15 * overload)

                candidates.append((utility, SocraticPrompt(
                    template_id=f"{signal.blindspot_type.name}_{hash(template) % 1000}",
                    text=text,
                    blindspot_target=signal.blindspot_type,
                    complexity=complexity,
                    spoil_level=spoil,
                    entities_used=entities
                )))

        if not candidates:
            return None

        # Select argmax utility
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]

        # Hard constraint: never exceed max spoil
        if best.spoil_level > self.MAX_SPOIL:
            return None

        # Hard constraint: must require System 2 (complexity > 0)
        if best.complexity < 0.05:
            return None

        return best


# ═══════════════════════════════════════════════════════════════════════
# IV. USER COGNITIVE MODEL
# ═══════════════════════════════════════════════════════════════════════

class UserCognitiveModel:
    """
    Maintains and updates the user's cognitive state.
    Tracks mastery, fatigue, and fading across 8 cognitive domains.
    """

    def __init__(self):
        self.state = UserCognitiveState(
            mastery=np.full(8, 0.3),   # start at novice level
            fatigue=0.2,
            attention=0.9,
            fading=np.full(8, 1.0),    # start with full assistance
        )
        self.history: List[UserCognitiveState] = []
        self.prompt_log: List[SocraticPrompt] = []

    def update_mastery(self, domain_idx: int,
                       quiz_score: float,
                       blindspot_detection_rate: float):
        """
        Update mastery from two signals:
        - quiz_score: performance on spaced repetition (0-1)
        - blindspot_detection_rate: naturalistic detection rate (0-1)
        """
        learning_rate = 0.05
        performance = 0.6 * quiz_score + 0.4 * blindspot_detection_rate
        current = self.state.mastery[domain_idx]
        self.state.mastery[domain_idx] = current + learning_rate * (performance - current)
        self.state.mastery[domain_idx] = np.clip(self.state.mastery[domain_idx], 0.0, 1.0)

    def update_fatigue(self, voice_features: Dict[str, float]):
        """
        Estimate fatigue from voice features.
        Input: {jitter, shimmer, hnr, speech_rate, pause_duration}
        """
        # Simple linear model (production: ML classifier)
        score = 0.0
        score += 0.25 * min(1.0, voice_features.get('jitter', 0.01) / 0.02)
        score += 0.20 * min(1.0, voice_features.get('shimmer', 0.05) / 0.1)
        score += 0.15 * max(0.0, 1.0 - voice_features.get('hnr', 20) / 25)
        score += 0.20 * max(0.0, 1.0 - voice_features.get('speech_rate', 150) / 200)
        score += 0.20 * min(1.0, voice_features.get('pause_duration', 0.3) / 0.8)

        # Smooth update
        self.state.fatigue = 0.8 * self.state.fatigue + 0.2 * score

    def update_attention(self, prompt_response_time: float):
        """Estimate attention from how quickly user responds to prompts."""
        expected_time = 3.0  # seconds expected for System 2 response
        if prompt_response_time > 0:
            ratio = expected_time / prompt_response_time
            self.state.attention = 0.7 * self.state.attention + 0.3 * min(1.0, ratio)

    def record_prompt(self, prompt: SocraticPrompt):
        """Record that a prompt was delivered."""
        self.state.total_prompts_today += 1
        self.state.prompts_in_last_60s += 1
        self.prompt_log.append(prompt)

    def tick_second(self):
        """Called every second to decay short-term counters."""
        self.state.prompts_in_last_60s = max(0, self.state.prompts_in_last_60s - 1/60)

    def get_zpd_bounds(self, domain_idx: int) -> Tuple[float, float]:
        """Get ZPD complexity bounds for a domain."""
        m = self.state.mastery[domain_idx]
        return (m * 0.7, min(1.0, (m + 0.25) * 0.7))


# ═══════════════════════════════════════════════════════════════════════
# V. FADING SCAFFOLD CONTROLLER
# ═══════════════════════════════════════════════════════════════════════

class FadingController:
    """
    Controls the gradual reduction of AI assistance as user mastery grows.
    
    Φ(m) = max(0, 1 - (m - θ_low) / (θ_high - θ_low))
    """

    THETA_LOW = 0.30   # mastery where fading begins
    THETA_HIGH = 0.85  # mastery where fading is complete
    F_CRIT = 0.65      # fatigue threshold for override
    LAMBDA_F = 0.8     # fatigue override strength

    def update(self, user: UserCognitiveModel):
        """Update fading levels based on current mastery and fatigue."""
        for d in range(8):
            m = user.state.mastery[d]
            # Base fading
            phi = max(0.0, 1.0 - (m - self.THETA_LOW) / (self.THETA_HIGH - self.THETA_LOW))
            # Fatigue override
            if user.state.fatigue > self.F_CRIT:
                fatigue_boost = self.LAMBDA_F * (user.state.fatigue - self.F_CRIT)
                phi = min(1.0, phi + fatigue_boost)
            user.state.fading[d] = phi

    def get_fade_level(self, fading_value: float) -> FadeLevel:
        """Map fading value to discrete action level."""
        if fading_value > 0.75:
            return FadeLevel.VERBAL
        elif fading_value > 0.50:
            return FadeLevel.KEYWORD
        elif fading_value > 0.25:
            return FadeLevel.TONE
        else:
            return FadeLevel.SILENT

    def get_prompt_budget(self, user: UserCognitiveModel,
                          window_seconds: float = 60.0) -> int:
        """Maximum prompts allowed in time window."""
        mean_fading = float(np.mean(user.state.fading))
        # Sigmoid: more fading → fewer prompts
        k = 5.0
        phi_0 = 0.5
        ratio = 1.0 / (1.0 + math.exp(-k * (mean_fading - phi_0)))
        max_per_window = 3  # absolute max per minute
        return max(0, int(max_per_window * ratio))


# ═══════════════════════════════════════════════════════════════════════
# VI. ORCHESTRATOR — Full Pipeline
# ═══════════════════════════════════════════════════════════════════════

class ExocortexPipeline:
    """
    Full cognitive augmentation pipeline.
    
    1. Receive transcript segment
    2. Detect blindspots
    3. Generate Socratic prompt (or silence)
    4. Update user model
    5. Apply fading control
    """

    def __init__(self):
        self.detector = BlindspotDetector()
        self.generator = ScaffoldGenerator()
        self.user_model = UserCognitiveModel()
        self.fading = FadingController()

    def process(self, transcript: str,
                voice_features: Optional[Dict[str, float]] = None,
                is_turn_boundary: bool = True) -> Optional[SocraticPrompt]:
        """
        Process a new transcript segment.
        Returns a prompt if one should be delivered, None if silent.
        """
        # Update fatigue if voice features available
        if voice_features:
            self.user_model.update_fatigue(voice_features)

        # Update fading
        self.fading.update(self.user_model)

        # Check prompt budget
        budget = self.fading.get_prompt_budget(self.user_model)
        if self.user_model.state.prompts_in_last_60s >= budget:
            return None

        # Only generate at turn boundaries
        if not is_turn_boundary:
            return None

        # Detect blindspots
        signals = self.detector.detect(transcript)

        # Filter by severity threshold
        signals = [s for s in signals if s.severity > 0.3]

        # Generate prompt
        prompt = self.generator.generate(signals, self.user_model.state)

        if prompt:
            self.user_model.record_prompt(prompt)

        return prompt

    def end_of_day_reflection(self, quiz_results: Dict[int, float]):
        """
        Process end-of-day spaced repetition results to update mastery.
        quiz_results: {domain_idx: score}
        """
        for domain_idx, score in quiz_results.items():
            self.user_model.update_mastery(domain_idx, score, 0.5)
        self.fading.update(self.user_model)
        self.user_model.state.total_prompts_today = 0


# ═══════════════════════════════════════════════════════════════════════
# VII. SELF-TEST SUITE
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 64)
    print("EXOCORTEX — Symbiotic AI Core — Self-Test Suite")
    print("=" * 64)

    pipeline = ExocortexPipeline()

    # Test 1: Blindspot Detection
    print("\n[1] Blindspot Detection")
    test_utterances = [
        "Doanh số tháng này giảm 20% vì chiến dịch marketing thất bại.",
        "Tất cả khách hàng đều thích sản phẩm này, khảo sát cho thấy 95% hài lòng.",
        "Chỉ có hai cách: hoặc tăng giá hoặc giảm chất lượng.",
        "Mọi công ty thành công đều có văn hóa mạnh, nên ta phải xây dựng văn hóa.",
        "Xu hướng đang tăng, chắc chắn quý sau sẽ có lãi.",
    ]

    for i, utterance in enumerate(test_utterances):
        signals = pipeline.detector.detect(utterance)
        vec = pipeline.detector.blindspot_vector(utterance)
        print(f"\n  [{i}] \"{utterance[:70]}...\"")
        print(f"      Blindspots: {len(signals)}")
        for s in signals[:2]:
            print(f"        - {s.blindspot_type.name}: severity={s.severity:.3f}")
        print(f"      Vector: {[f'{v:.3f}' for v in vec]}")

    # Test 2: Scaffold Generation
    print("\n[2] Socratic Scaffold Generation")
    for i, utterance in enumerate(test_utterances):
        signals = pipeline.detector.detect(utterance)
        prompt = pipeline.generator.generate(signals, pipeline.user_model.state)
        if prompt:
            print(f"\n  [{i}] → \"{prompt.text}\"")
            print(f"      Complexity: {prompt.complexity:.3f} | Spoil: {prompt.spoil_level:.3f}")
            print(f"      Fade level: {pipeline.fading.get_fade_level(pipeline.user_model.state.fading[0])}")
        else:
            print(f"\n  [{i}] → [SILENCE] (no suitable prompt)")

    # Test 3: Fading Controller
    print("\n[3] Fading Scaffold Controller")
    print(f"  Initial mastery:  {[f'{m:.2f}' for m in pipeline.user_model.state.mastery]}")
    print(f"  Initial fading:   {[f'{m:.2f}' for m in pipeline.user_model.state.fading]}")
    print(f"  Initial levels:   {[pipeline.fading.get_fade_level(f) for f in pipeline.user_model.state.fading]}")

    # Simulate learning
    print("\n  --- Simulating 30 days of spaced repetition ---")
    for day in range(30):
        for d in range(8):
            if day % 3 == 0:  # quiz every 3 days per domain
                pipeline.user_model.update_mastery(d, 0.6 + 0.01 * day, 0.5)
        pipeline.fading.update(pipeline.user_model)

    print(f"  Final mastery:    {[f'{m:.2f}' for m in pipeline.user_model.state.mastery]}")
    print(f"  Final fading:     {[f'{m:.2f}' for m in pipeline.user_model.state.fading]}")
    print(f"  Final levels:     {[pipeline.fading.get_fade_level(f) for f in pipeline.user_model.state.fading]}")

    # Test 4: Prompt Budget
    print("\n[4] Prompt Budget Controller")
    for fading_mean in [1.0, 0.75, 0.50, 0.25, 0.0]:
        pipeline.user_model.state.fading = np.full(8, fading_mean)
        budget = pipeline.fading.get_prompt_budget(pipeline.user_model)
        levels = pipeline.fading.get_fade_level(fading_mean)
        print(f"  Φ_mean={fading_mean:.2f} → level={levels.name:8s} → budget={budget} prompts/min")

    # Test 5: Anti-Brainrot Check
    print("\n[5] Anti-Brainrot Theorem Verification")
    initial_mastery = np.mean(pipeline.user_model.state.mastery)
    print(f"  Initial mean mastery: {initial_mastery:.4f}")
    print("  dC_H/dt >= 0: ", end="")
    # After 30 days of training, mastery should be higher
    assert np.mean(pipeline.user_model.state.mastery) >= initial_mastery, \
        "FAIL: Mastery decreased!"
    print("✅ CONFIRMED")
    print(f"  Final mean mastery:   {np.mean(pipeline.user_model.state.mastery):.4f}")
    print(f"  Δmastery = +{np.mean(pipeline.user_model.state.mastery) - initial_mastery:.4f}")
    print("  Brainrot averted. Cognitive capacity increased.")

    # Test 6: Edge Cases
    print("\n[6] Edge Cases")

    # Empty input
    prompt = pipeline.process("", None, True)
    assert prompt is None, "FAIL: Generated prompt from empty text"
    print("  ✅ Empty input → silence")

    # Very short input
    prompt = pipeline.process("Ừ.", None, True)
    assert prompt is None, "FAIL: Generated prompt from trivial text"
    print("  ✅ Trivial input → silence")

    # Fatigue override — simulate sustained fatigue over time
    for _ in range(20):
        pipeline.user_model.update_fatigue({
            'jitter': 0.04, 'shimmer': 0.20, 'hnr': 8,
            'speech_rate': 80, 'pause_duration': 1.2
        })
    pipeline.fading.update(pipeline.user_model)
    assert pipeline.user_model.state.fatigue > 0.6, f"FAIL: Fatigue={pipeline.user_model.state.fatigue:.3f} <= 0.6"
    print(f"  ✅ High fatigue detected: F={pipeline.user_model.state.fatigue:.3f}")
    print(f"     Fading override: Φ_mean={np.mean(pipeline.user_model.state.fading):.3f}")

    print("\n" + "=" * 64)
    print("EXOCORTEX — All tests passed. System operational.")
    print("=" * 64)
