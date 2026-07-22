import os
from datetime import datetime, timezone

import jdatetime
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


def jalali_to_timestamp(date_text, time_text):
    year, month, day = map(int, date_text.split("/"))
    hour, minute = map(int, time_text.split(":"))

    jalali = jdatetime.datetime(
        year,
        month,
        day,
        hour,
        minute
    )

    gregorian = jalali.togregorian()

    return gregorian.replace(
        tzinfo=timezone.utc
    ).timestamp()


def remaining_text(seconds):
    if seconds <= 0:
        return "✅ رویداد به پایان رسید"

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    result = "⏳ زمان باقی‌مانده:\n"

    if days:
        result += f"📅 {days} روز\n"

    if hours:
        result += f"🕐 {hours} ساعت\n"

    result += f"⏱ {minutes} دقیقه"

    return result


async def is_admin(update):
    admins = await update.effective_chat.get_administrators()

    return any(
        admin.user.id == update.effective_user.id
        for admin in admins
    )


async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_admin(update):
        await update.message.reply_text(
            "❌ فقط ادمین‌ها اجازه ساخت تایمر دارند."
        )
        return

    try:
        date = context.args[0]
        time = context.args[1]
        title = " ".join(context.args[2:])

        end_time = jalali_to_timestamp(
            date,
            time
        )

        message = await update.message.reply_text(
            f"🎯 {title}\n\n"
            f"⏳ در حال ساخت تایمر..."
        )

        countdowns[message.message_id] = {
            "chat_id": update.effective_chat.id,
            "message_id": message.message_id,
            "title": title,
            "end": end_time
        }

        await update.message.delete()

    except Exception:

        await update.message.reply_text(
            "فرمت صحیح:\n\n"
            "/countdown 1405/05/01 20:00 نام رویداد"
        )


async def update_timers(context: ContextTypes.DEFAULT_TYPE):

    now = datetime.now(
        timezone.utc
    ).timestamp()

    for timer in list(countdowns.values()):

        seconds = timer["end"] - now

        text = (
            f"🎯 {timer['title']}\n\n"
            f"{remaining_text(seconds)}"
        )

        try:
            await context.bot.edit_message_text(
                chat_id=timer["chat_id"],
                message_id=timer["message_id"],
                text=text
            )

        except Exception:
            pass


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await is_admin(update):

        countdowns.clear()

        await update.message.reply_text(
            "🛑 همه تایمرها حذف شدند."
        )


def main():

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


    app.add_handler(
        CommandHandler(
            "stopcountdown",
            stop
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
