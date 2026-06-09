"""
EXOCORTEX Telegram Bot
=======================
Standalone bot: voice/text → exocortex pipeline → Socratic reply.
Plus: /quiz, /reflect, /status, scheduled proactive nudges.
"""

import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exocortex-bot")

TOKEN = "8100588732:AAGL_6da6IfBJ-hl1THRPw6Vled-CrI0kF0"
EXOCORTEX_URL = "http://127.0.0.1:8083"
NUDGE_CHAT_IDS = set()   # chat IDs that have interacted with the bot

# ═══════════════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NUDGE_CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text(
        "🧠 *EXOCORTEX — Symbiotic AI*\n\n"
        "AI không làm hộ bạn. AI làm bạn giỏi hơn.\n\n"
        "• 🎤 *Voice message* — tôi nghe và hỏi lại câu Socratic\n"
        "• 💬 *Text* — tôi phân tích blindspot trong lập luận\n"
        "• /quiz — bài kiểm tra nhận thức hôm nay\n"
        "• /reflect — tổng kết mastery của bạn\n"
        "• /status — trạng thái hiện tại\n\n"
        "Tôi *không bao giờ* đưa câu trả lời. Chỉ hỏi.",
        parse_mode="Markdown"
    )


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{EXOCORTEX_URL}/quiz?n=3")
            data = resp.json()
    except Exception:
        await update.message.reply_text("⚠️ Exocortex đang bận.")
        return

    qs = data.get("quiz", [])
    if not qs:
        await update.message.reply_text("📝 Chưa có câu hỏi quiz. Hãy đàm thoại trước để AI hiểu blindspot của bạn.")
        return

    lines = ["📝 *Bài Quiz Hôm Nay*\n"]
    for i, q in enumerate(qs):
        lines.append(f"*{i+1}.* {q['question']}")
        lines.append(f"   └ 💡 _{q['hint']}_ · Mastery: {int(q['mastery_current']*100)}%")
    lines.append("\n_Tự chấm điểm: /score <số> <điểm>_")
    lines.append("_VD: /score 1 80 — câu 1 bạn thấy mình đúng 80%_")

    context.user_data["last_quiz"] = qs
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    qs = context.user_data.get("last_quiz", [])
    if not qs:
        await update.message.reply_text("Gửi /quiz trước đã nhé.")
        return

    args = update.message.text.split()
    if len(args) < 3:
        await update.message.reply_text("Dùng: /score <số câu> <điểm 0-100>\nVD: /score 1 80")
        return

    try:
        idx = int(args[1]) - 1
        score = int(args[2]) / 100.0
        if idx < 0 or idx >= len(qs):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Số câu không hợp lệ. VD: /score 1 80")
        return

    q = qs[idx]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{EXOCORTEX_URL}/quiz/submit",
                json={"quiz_id": q["id"], "domain_idx": q["domain_idx"], "score": score}
            )
            data = resp.json()
    except Exception:
        await update.message.reply_text("⚠️ Lỗi gửi điểm.")
        return

    new_m = data.get("new_mastery", 0)
    await update.message.reply_text(
        f"✅ Đã ghi nhận câu {idx+1}: *{int(score*100)}%*\n"
        f"📈 Mastery [{q['domain']}]: {int(new_m*100)}%",
        parse_mode="Markdown"
    )


async def cmd_reflect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{EXOCORTEX_URL}/reflect")
            d = await resp.json()
    except Exception:
        await update.message.reply_text("⚠️ Exocortex đang bận.")
        return

    weakest = ", ".join(f"{w['domain']} ({int(w['mastery']*100)}%)" for w in d["weakest"])
    strongest = ", ".join(f"{s['domain']} ({int(s['mastery']*100)}%)" for s in d["strongest"])

    await update.message.reply_text(
        f"📊 *Phản Tư Hôm Nay*\n\n"
        f"🔢 Truy vấn: *{d['prompts_today']}*\n"
        f"🧠 Mastery TB: *{int(d['average_mastery']*100)}%*\n"
        f"😴 Fatigue: *{int(d['fatigue']*100)}%*\n\n"
        f"⚠️ Yếu nhất: {weakest}\n"
        f"💪 Mạnh nhất: {strongest}\n\n"
        f"_{d['message']}_",
        parse_mode="Markdown"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{EXOCORTEX_URL}/status")
            d = await resp.json()
    except Exception:
        await update.message.reply_text("⚠️ Exocortex đang bận.")
        return

    cog = d.get("cognitive", {})
    await update.message.reply_text(
        f"🧠 *Trạng Thái*\n\n"
        f"📋 Prompts hôm nay: *{cog.get('prompts_today', 0)}*\n"
        f"⏱ Budget/phút: *{cog.get('budget_per_minute', 0)}*\n"
        f"😴 Fatigue: *{int(cog.get('fatigue', 0)*100)}%*\n"
        f"⚠️ Yếu nhất: *{cog.get('weakest_domain', '?')}*\n"
        f"💪 Mạnh nhất: *{cog.get('strongest_domain', '?')}*",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════════════
# VOICE / TEXT HANDLERS
# ═══════════════════════════════════════════════════════════════════════

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NUDGE_CHAT_IDS.add(update.effective_chat.id)
    await update.message.chat.send_action("typing")

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    audio_bytes = await file.download_as_bytearray()

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{EXOCORTEX_URL}/process-voice",
                files={"file": ("voice.ogg", bytes(audio_bytes), "audio/ogg")}
            )
            data = resp.json()
    except Exception:
        await update.message.reply_text("⚠️ Exocortex đang bận, thử lại sau nhé!")
        return

    transcript = data.get("transcript", "")
    prompt = data.get("prompt")
    blindspots = data.get("blindspots", [])

    if not prompt:
        if transcript:
            await update.message.reply_text(
                f'👂 *Nghe được:* "{transcript}"\n\n✅ Không phát hiện blindspot.',
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("👂 Không nghe rõ, bạn nói lại được không?")
        return

    bs_tags = "`" + "` · `".join([b["type"] for b in blindspots[:2]]) + "`" if blindspots else ""
    await update.message.reply_text(
        f"🤔 *{prompt}*\n\n{bs_tags}",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NUDGE_CHAT_IDS.add(update.effective_chat.id)
    text = update.message.text.strip()
    if len(text) < 10:
        await update.message.reply_text("Gửi câu dài hơn chút để tôi phân tích nhé.")
        return

    await update.message.chat.send_action("typing")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{EXOCORTEX_URL}/detect", json={"text": text})
            data = resp.json()
    except Exception:
        await update.message.reply_text("⚠️ Exocortex đang bận.")
        return

    prompt = data.get("prompt")
    blindspots = data.get("blindspots", [])

    if not prompt:
        await update.message.reply_text("✅ Không phát hiện blindspot trong lập luận này.")
        return

    bs_tags = "`" + "` · `".join([b["type"] for b in blindspots[:3]]) + "`"
    await update.message.reply_text(
        f"🔍 {bs_tags}\n\n🤔 *{prompt}*",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════════════
# PROACTIVE NUDGES (scheduled job)
# ═══════════════════════════════════════════════════════════════════════

async def proactive_nudge(context: ContextTypes.DEFAULT_TYPE):
    """Periodic job: check for nudges and send to active users."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{EXOCORTEX_URL}/nudge")
            data = resp.json()
    except Exception:
        return

    if not data.get("has_nudge"):
        return

    nudge = data["nudge"]
    msg = (
        f"🔄 *Nhắc bài*\n\n"
        f"{nudge['nudge']}\n\n"
        f"_{nudge['domain']} · Mastery: {int(nudge['mastery']*100)}%_\n"
        f"Gửi /quiz để luyện tập."
    )

    for chat_id in list(NUDGE_CHAT_IDS):
        try:
            await context.bot.send_message(chat_id, msg, parse_mode="Markdown")
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("score", cmd_score))
    app.add_handler(CommandHandler("reflect", cmd_reflect))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Proactive nudge every 2 hours (7200s)
    app.job_queue.run_repeating(proactive_nudge, interval=7200, first=600)

    logger.info("🧠 EXOCORTEX Bot starting with proactive nudges...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
