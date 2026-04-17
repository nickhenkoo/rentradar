import os
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, PreCheckoutQueryHandler, filters,
)

from bot.handlers.start import start, language_callback, help_command
from bot.handlers.language import language_command
from bot.handlers.filters import build_addfilter_handler
from bot.handlers.listings import (
    myfilters, filter_delete_callback,
    filter_pause_callback, filter_resume_callback,
    pause_all, resume_all, saved_listings, save_listing_callback,
    unsave_listing_callback, note_listing_callback, note_message_handler,
    cancel_note,
)
from bot.handlers.subscription import (
    subscribe, buy_feature_callback, precheckout_callback, successful_payment, status,
)
from bot.handlers.premium import price_history_callback
from bot.handlers.admin import (
    admin_panel, admin_stats, admin_grant, admin_user,
    admin_broadcast, admin_test_alerts, admin_refresh, admin_setplan,
    admin_test_analytics, admin_test_hot,
)


async def _post_init(application: Application) -> None:
    from telegram import BotCommand
    from core.scheduler import start_scheduler

    # Register commands so Telegram shows hints when user types /
    commands = {
        "en": [
            BotCommand("addfilter",  "Add a search filter"),
            BotCommand("myfilters",  "View and manage filters"),
            BotCommand("saved",      "Saved listings"),
            BotCommand("pause_all",  "Pause all alerts"),
            BotCommand("resume_all", "Resume alerts"),
            BotCommand("subscribe",  "Unlock premium features"),
            BotCommand("status",     "Your subscription status"),
            BotCommand("language",   "Change language"),
            BotCommand("help",       "Show help"),
        ],
        "ru": [
            BotCommand("addfilter",  "Добавить фильтр поиска"),
            BotCommand("myfilters",  "Мои фильтры"),
            BotCommand("saved",      "Сохранённые объявления"),
            BotCommand("pause_all",  "Приостановить все алерты"),
            BotCommand("resume_all", "Возобновить алерты"),
            BotCommand("subscribe",  "Премиум-функции"),
            BotCommand("status",     "Статус подписки"),
            BotCommand("language",   "Изменить язык"),
            BotCommand("help",       "Помощь"),
        ],
        "lv": [
            BotCommand("addfilter",  "Pievienot filtru"),
            BotCommand("myfilters",  "Mani filtri"),
            BotCommand("saved",      "Saglabātie sludinājumi"),
            BotCommand("pause_all",  "Apturēt visus paziņojumus"),
            BotCommand("resume_all", "Atsākt paziņojumus"),
            BotCommand("subscribe",  "Premium funkcijas"),
            BotCommand("status",     "Abonēšanas statuss"),
            BotCommand("language",   "Mainīt valodu"),
            BotCommand("help",       "Palīdzība"),
        ],
    }

    from telegram import BotCommandScopeDefault, BotCommandScopeChat
    for lang_code, cmds in commands.items():
        await application.bot.set_my_commands(cmds, language_code=lang_code)
    # Fallback for users without language set
    await application.bot.set_my_commands(commands["en"])

    # Admin commands — shown in admin's chat on top of regular commands
    admin_id = int(os.environ.get("ADMIN_ID", "0"))
    if admin_id:
        admin_commands = commands["en"] + [
            BotCommand("admin",             "Admin panel"),
            BotCommand("admin_stats",       "Analytics"),
            BotCommand("admin_grant",       "Grant premium"),
            BotCommand("admin_setplan",     "Set/change user plan"),
            BotCommand("admin_user",        "View user info"),
            BotCommand("admin_broadcast",   "Broadcast message"),
            BotCommand("admin_test_alerts",    "Send 5 test alerts + seed history"),
            BotCommand("admin_test_hot",       "Test hot listing alert"),
            BotCommand("admin_test_analytics", "Trigger analytics report now"),
            BotCommand("admin_refresh",        "Clear my sent_alerts"),
        ]
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception:
            pass  # admin hasn't started the bot yet — will register on next restart

    scheduler = start_scheduler(application.bot)
    scheduler.start()
    application.bot_data["scheduler"] = scheduler


async def _post_shutdown(application: Application) -> None:
    scheduler = application.bot_data.get("scheduler")
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)


def build_application() -> Application:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = (
        Application.builder()
        .token(token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))

    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_(en|ru|lv)$"))

    app.add_handler(build_addfilter_handler())

    app.add_handler(CommandHandler("myfilters", myfilters))
    app.add_handler(CallbackQueryHandler(filter_delete_callback, pattern="^filter_delete_"))
    app.add_handler(CallbackQueryHandler(filter_pause_callback, pattern="^filter_pause_"))
    app.add_handler(CallbackQueryHandler(filter_resume_callback, pattern="^filter_resume_"))
    app.add_handler(CommandHandler("pause_all", pause_all))
    app.add_handler(CommandHandler("resume_all", resume_all))
    app.add_handler(CommandHandler("saved", saved_listings))
    app.add_handler(CallbackQueryHandler(save_listing_callback, pattern="^save_listing_"))
    app.add_handler(CallbackQueryHandler(unsave_listing_callback, pattern="^unsave_listing_"))
    app.add_handler(CallbackQueryHandler(note_listing_callback, pattern="^note_listing_"))
    app.add_handler(CommandHandler("cancel_note", cancel_note))

    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(buy_feature_callback, pattern="^buy_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    app.add_handler(CallbackQueryHandler(price_history_callback, pattern="^history_"))

    # Note message handler — must be last (lowest priority)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, note_message_handler))

    # Admin commands
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("admin_stats", admin_stats))
    app.add_handler(CommandHandler("admin_grant", admin_grant))
    app.add_handler(CommandHandler("admin_user", admin_user))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    app.add_handler(CommandHandler("admin_test_alerts", admin_test_alerts))
    app.add_handler(CommandHandler("admin_refresh", admin_refresh))
    app.add_handler(CommandHandler("admin_setplan", admin_setplan))
    app.add_handler(CommandHandler("admin_test_analytics", admin_test_analytics))
    app.add_handler(CommandHandler("admin_test_hot", admin_test_hot))

    return app
