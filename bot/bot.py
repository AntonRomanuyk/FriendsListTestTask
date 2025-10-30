import logging

import api_client
from config import settings
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import Update
from telegram.ext import Application
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import filters
from telegram.helpers import escape_markdown

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PHOTO, NAME, PROFESSION, DESCRIPTION = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm your bot for managing your friend list.\n\n"
        "Available commands:\n"
        "/addfriend - add a new friend\n"
        "/list - show all friends\n"
        "/friend <id> - show a friend by ID"
    )


async def list_friends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Getting friend list from the backend...")

    friends = await api_client.get_all_friends()

    if not friends:
        await update.message.reply_text("Failed to get friend list, or it is empty.")
        return

    message_parts = ["Here are your friends:\n"]
    for friend in friends:
        part = f"👤 *{friend['name']}*\n"
        part += f"💼 **Profession:** {friend['profession']}\n"

        if friend.get('photo_url'):
            photo_url = f"{friend['photo_url']}"
            part += f"🖼️ *Photo URL:* `({escape_markdown(photo_url, version=2)})`\n"

        message_parts.append(part)

    await update.message.reply_text(
        "\n".join(message_parts),
        parse_mode='MarkdownV2',
        disable_web_page_preview=True
    )


async def get_friend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        friend_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please specify an ID. For example: /friend 123")
        return

    friend = await api_client.get_friend_by_id(friend_id)

    if not friend:
        await update.message.reply_text("Error: could not contact the server.")
        return
    if friend.get("error") == "not_found":
        await update.message.reply_text(f"Friend with ID {friend_id} not found.")
        return

    caption = f"👤 *{friend['name']}*\n\n"
    caption += f"💼 **Profession:** {friend['profession']}\n"

    if friend.get('profession_description'):
        caption += f"📝 **Description:** _{friend['profession_description']}_"

    photo_bytes = None
    if friend.get('photo_url'):
        photo_bytes = await api_client.get_photo_bytes(friend['photo_url'])

    try:
        if photo_bytes:

            await update.message.reply_photo(
                photo=photo_bytes,
                caption=caption,
                parse_mode='Markdown'
            )
        else:

            await update.message.reply_text(
                f"Here is the data (photo not found):\n{caption}",
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Failed to send photo to Telegram: {e}")

        await update.message.reply_text(f"Failed to send photo, but here is the data:\n{caption}")


async def add_friend_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Let's start creating a friend. Please send me their photo.\n\n"
        "Send /cancel to stop at any time."
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("This is not a photo. Please send a photo.")
        return PHOTO

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    context.user_data['friend_photo'] = bytes(photo_bytes)

    logger.info(f"Photo received from {update.effective_user.first_name}")
    await update.message.reply_text("Great photo! Now, enter the friend's name:")

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['friend_name'] = update.message.text
    logger.info(f"Name: {update.message.text}")

    await update.message.reply_text("Got it. Now, enter their profession:")

    return PROFESSION


async def get_profession(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['friend_profession'] = update.message.text
    logger.info(f"Profession: {update.message.text}")

    reply_keyboard = [["/skip"]]
    await update.message.reply_text(
        "Almost done. Add a short description of their profession.\n"
        "(Or press /skip to skip this step)",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )

    return DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['friend_description'] = update.message.text
    logger.info(f"Description: {update.message.text}")

    await update.message.reply_text(
        "Thank you! Creating your friend on the server...",
        reply_markup=ReplyKeyboardRemove()
    )

    await submit_friend_to_api(update, context)
    return ConversationHandler.END


async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['friend_description'] = None  # or ""
    logger.info("Description skipped.")

    await update.message.reply_text(
        "Okay, skipping description. Creating friend...",
        reply_markup=ReplyKeyboardRemove()
    )

    await submit_friend_to_api(update, context)
    return ConversationHandler.END


async def submit_friend_to_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = {
            'name': context.user_data['friend_name'],
            'profession': context.user_data['friend_profession'],
            'profession_description': context.user_data.get('friend_description')
        }
        photo = context.user_data['friend_photo']

        new_friend = await api_client.add_friend(data, photo)

        if new_friend:
            await update.message.reply_text(
                f"🎉 Successfully created friend!\n\n"
                f"ID: {new_friend['id']}\n"
                f"Name: {new_friend['name']}\n"
                f"Profession: {new_friend['profession']}"
            )
        else:
            await update.message.reply_text("Error! Failed to create friend. Check the backend or console logs.")

    except Exception as e:
        logger.error(f"Error while sending data: {e}")
        await update.message.reply_text("An unknown error occurred while creating the friend.")
    finally:
        context.user_data.clear()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.effective_user.first_name} canceled the conversation.")
    context.user_data.clear()
    await update.message.reply_text(
        "Friend creation canceled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(settings.BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addfriend", add_friend_start)],
        states={
            PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               lambda u, c: u.message.reply_text("Please send a photo."))
            ],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_profession)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description),
                CommandHandler("skip", skip_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Adding handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_friends))
    application.add_handler(CommandHandler("friend", get_friend))

    logger.info("Bot is starting...")

    application.run_polling()


if __name__ == "__main__":
    main()
