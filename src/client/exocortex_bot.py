"""
EXOCORTEX Telegram Bot
=======================
Standalone bot: receives voice/text → exocortex pipeline → Socratic reply.

Usage: send voice message or text to @LEO_AGII_bot on Telegram.
"""

import logging
import httpx
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("exocortex-bot")

TOKEN = "8100588732:AAGL_6da6IfBJ-hl1THRPw6Vled-CrI0kF0"
EXOCORTEX_URL = "http://127.0.0.1:8083"

EXO_SYSTEM = """Bạn là EXOCORTEX — Symbiotic AI.

Bạn không bao giờ đưa câu trả lời. Bạn chỉ hỏi câu hỏi Socratic để kích hoạt tư duy phản biện.

Nguyên tắc:
- Luôn dùng tiếng Việt
- 1 câu hỏi ngắn gọn, dưới 25 từ
- Không giải thích, không bình luận
- Không bao giờ cho biết câu trả lời"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *EXOCORTEX — Symbiotic AI*\n\n"
        "AI không làm hộ bạn. AI làm bạn giỏi hơn.\n\n"
        "• Gửi *voice message* — tôi nghe và hỏi lại câu hỏi Socratic\n"
        "• Gửi *text* — tôi phân tích blindspot trong lập luận của bạn\n\n"
        "Tôi *không bao giờ* đưa câu trả lời. Chỉ hỏi để bạn tự nghĩ.",
        parse_mode="Markdown"
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download voice from Telegram → exocortex → reply Socratic prompt."""
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
    except Exception as e:
        logger.error(f"Exocortex API error: {e}")
        await update.message.reply_text("⚠️ Exocortex đang bận, thử lại sau nhé!")
        return

    transcript = data.get("transcript", "")
    prompt = data.get("prompt")
    blindspots = data.get("blindspots", [])

    if not prompt:
        if transcript:
            await update.message.reply_text(
                f'👂 *Nghe được:* "{transcript}"\n\n'
                f"✅ Không phát hiện blindspot — lập luận ổn.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("👂 Không nghe rõ, bạn nói lại được không?")
        return

    bs_tags = ""
    if blindspots:
        bs_names = [b["type"] for b in blindspots[:2]]
        bs_tags = "`" + "` · `".join(bs_names) + "`\n"

    await update.message.reply_text(
        f"🤔 *{prompt}*\n\n"
        f"{bs_tags}"
        f"_{'Độ phức tạp: ' + str(data.get('prompt_complexity', '?'))}_",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Text → exocortex /detect → reply Socratic prompt."""
    text = update.message.text.strip()
    if len(text) < 10:
        await update.message.reply_text("Gửi câu dài hơn chút để tôi phân tích nhé.")
        return

    await update.message.chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{EXOCORTEX_URL}/detect",
                json={"text": text}
            )
            data = resp.json()
    except Exception as e:
        logger.error(f"Exocortex API error: {e}")
        await update.message.reply_text("⚠️ Exocortex đang bận, thử lại sau nhé!")
        return

    prompt = data.get("prompt")
    blindspots = data.get("blindspots", [])

    if not prompt:
        await update.message.reply_text(
            "✅ Không phát hiện blindspot trong lập luận này."
        )
        return

    bs_tags = "`" + "` · `".join([b["type"] for b in blindspots[:3]]) + "`"

    await update.message.reply_text(
        f"🔍 Phát hiện: {bs_tags}\n\n"
        f"🤔 *{prompt}*\n\n"
        f"_{'Độ phức tạp: ' + str(data.get('prompt_complexity', '?'))}_",
        parse_mode="Markdown"
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🧠 EXOCORTEX Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
