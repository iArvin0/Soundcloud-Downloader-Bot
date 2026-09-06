from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .config import Settings
from .handlers import BotHandlers
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show usage help"),
        ]
    )
    bot = await application.bot.get_me()
    logger.info("Bot started as @%s (id=%s)", bot.username, bot.id)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled Telegram update error", exc_info=context.error)



def main() -> None:
    settings = Settings.from_env()
    settings.download_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(settings.log_dir)

    handlers = BotHandlers(settings)

    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(post_init)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text))
    application.add_error_handler(error_handler)

    logger.info("Starting polling…")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
