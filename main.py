from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
import plugins

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", plugins.start))
    app.add_handler(CommandHandler("waymenu", plugins.waymenu))
    app.add_handler(CommandHandler("ping", plugins.ping))

    app.add_handler(CommandHandler("setconfess", plugins.set_confess))
    app.add_handler(CommandHandler("confess", plugins.confess))
    app.add_handler(CommandHandler("setcooldown", plugins.set_cooldown))

    app.add_handler(CommandHandler("ship", plugins.ship))

    app.add_handler(CommandHandler("filter", plugins.add_filter))
    app.add_handler(CommandHandler("stop", plugins.stop_filter))
    app.add_handler(CommandHandler("filterlist", plugins.filter_list))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plugins.check_message))

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()