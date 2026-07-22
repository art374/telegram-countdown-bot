import os
import asyncio
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

# ذخیره تایمرها در حافظه
countdowns = {}


def convert_jalali_to_timestamp(date_str, time_str):
    """
    تبدیل تاریخ شمسی به timestamp
    ورودی:
    1405/05/01
    20:00
    """

    y, m, d = map(int, date_str.split("/"))
    hour, minute = map(int, time_str.split(":"))

    jalali_date = jdatetime.datetime(
        y, m, d, hour, minute
    )

    gregorian = jalali_date.togregorian()

    return gregorian.replace(
        tzinfo=timezone.utc
    ).timestamp()


def format_remaining(seconds):
    if seconds <= 0:
        return "✅ رویداد به پایان رسید"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    text = "⏳ زمان باقی‌مانده:\n"

    if days:
        text += f"📅 {days} روز\n"

    if hours:
        text += f"🕐 {hours} ساعت\n"

    text += f"⏱ {minutes} دقیقه"

    return text


async def is_admin(update):
    user = update.effective_user
    chat = update.effective_chat

    admins = await chat.get_administrators()

    return any(
        admin.user.id == user.id
        for admin in admins
    )


async def countdown_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_chat.type not in [
        "group",
        "supergroup"
    ]:
        return

    if not await is_admin(update):
        await update.message.reply_text(
            "❌ فقط ادمین‌ها می‌توانند تایمر بسازند."
        )
        return


    try:
        # مثال:
        # /countdown 1405/05/01 20:00 جشن تابستانی

        args = context.args

        date = args[0]
        time = args[1]

        title = " ".join(args[2:])

        end_time = convert_jalali_to_timestamp(
            date,
            time
        )

        msg = await update.message.reply_text(
            f"🎯 {title}\n\n"
            f"⏳ در حال محاسبه..."
        )


        countdowns[msg.message_id] = {
            "chat_id": update.effective_chat.id,
            "message_id": msg.message_id,
            "end_time": end_time,
            "title": title
        }


        await update.message.delete()


    except Exception:

        await update.message.reply_text(
            "فرمت درست:\n\n"
            "/countdown 1405/05/01 20:00 نام رویداد"
        )


async def update_countdowns(
    context: ContextTypes.DEFAULT_TYPE
):

    now = datetime.now(
        timezone.utc
    ).timestamp()


    for key, item in list(countdowns.items()):

        remaining = int(
            item["end_time"] - now
        )

        text = (
            f"🎯 {item['title']}\n\n"
            f"{format_remaining(remaining)}"
        )

        try:

            await context.bot.edit_message_text(
                chat_id=item["chat_id"],
                message_id=item["message_id"],
                text=text
            )

        except Exception:
            pass



async def stop(update, context):

    if not await is_admin(update):
        return

    countdowns.clear()

    await update.message.reply_text(
        "🛑 همه تایمرها متوقف شدند."
    )



def main():

    app = Application.builder()\
        .token(TOKEN)\
        .build()


    app.add_handler(
        CommandHandler(
            "countdown",
            countdown_command
        )
    )


    app.add_handler(
        CommandHandler(
            "stopcountdown",
            stop
        )
    )


    # اجرای آپدیت هر دقیقه
    app.job_queue.run_repeating(
        update_countdowns,
        interval=60,
        first=10
    )


    print("Bot started...")

    app.run_polling()



if __name__ == "__main__":
    main()