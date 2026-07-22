import os
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

countdowns = {}


# وب سرور کوچک برای Render
class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(
        ("0.0.0.0", port),
        HealthCheck
    )
    server.serve_forever()


def jalali_to_timestamp(date_text, time_text):

    y, m, d = map(
        int,
        date_text.split("/")
    )

    hour, minute = map(
        int,
        time_text.split(":")
    )

    j_date = jdatetime.datetime(
        y, m, d,
        hour, minute
    )

    g_date = j_date.togregorian()

    return g_date.replace(
        tzinfo=timezone.utc
    ).timestamp()


def remaining_text(seconds):

    if seconds <= 0:
        return "✅ رویداد تمام شد"

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    text = "⏳ زمان باقی‌مانده:\n"

    if days:
        text += f"📅 {days} روز\n"

    if hours:
        text += f"🕐 {hours} ساعت\n"

    text += f"⏱ {minutes} دقیقه"

    return text


async def is_admin(update):

    admins = await update.effective_chat.get_administrators()

    return any(
        a.user.id == update.effective_user.id
        for a in admins
    )


async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_admin(update):
        await update.message.reply_text(
            "❌ فقط ادمین‌ها اجازه دارند."
        )
        return

    try:
        date = context.args[0]
        time = context.args[1]
        title = " ".join(context.args[2:])

        end = jalali_to_timestamp(
            date,
            time
        )

        msg = await update.message.reply_text(
            "🎯 " + title
        )

        countdowns[msg.message_id] = {
            "chat": update.effective_chat.id,
            "message": msg.message_id,
            "title": title,
            "end": end
        }

        await update.message.delete()

    except Exception:

        await update.message.reply_text(
            "فرمت:\n"
            "/countdown 1405/05/01 20:00 نام رویداد"
        )


async def update_timers(context):

    now = datetime.now(
        timezone.utc
    ).timestamp()

    for timer in countdowns.values():

        left = timer["end"] - now

        try:
            await context.bot.edit_message_text(
                chat_id=timer["chat"],
                message_id=timer["message"],
                text=(
                    f"🎯 {timer['title']}\n\n"
                    f"{remaining_text(left)}"
                )
            )

        except Exception:
            pass


def main():

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler(
            "countdown",
            countdown
        )
    )


    app.job_queue.run_repeating(
        update_timers,
        interval=60,
        first=5
    )


    print("Bot started successfully")

    app.run_polling()


if __name__ == "__main__":
    main()
