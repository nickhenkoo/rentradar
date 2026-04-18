from telegram import InlineKeyboardButton, InlineKeyboardMarkup

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "choose_language":          "Choose your language:",
        "language_set":             "Language set to English.",
        "welcome": (
            "👋 Welcome to RentRadar | Latvia!\n\n"
            "I monitor ss.lv across all of Latvia and alert you instantly "
            "when a new apartment matches your filters.\n\n"
            "All filters are free. Use /addfilter to set up your first search."
        ),
        "city":                     "City",
        "district":                 "District",
        "price":                    "Price",
        "rooms":                    "Rooms",
        "area":                     "Area",
        "floor":                    "Floor",
        "series":                   "Series",
        "long_term_only":           "Long-term rentals only",

        "ask_city":                 "Which city are you looking in?",
        "ask_district":             "Which district?\nTap <b>Any</b> to match all districts.",
        "ask_price_range":          "Price range per month (€)?\nEnter as <code>min-max</code>, e.g. <code>300-700</code>.\nOr tap <b>Skip</b>.",
        "ask_rooms_range":          "How many rooms?\nEnter as <code>min-max</code>, e.g. <code>1-3</code>, or just <code>2</code> for exactly 2.\nOr tap <b>Skip</b>.",
        "ask_area_range":           "Area range (m²)?\nEnter as <code>min-max</code>, e.g. <code>40-80</code>.\nOr tap <b>Skip</b>.",
        "ask_floor_range":          "Floor range?\nEnter as <code>min-max</code>, e.g. <code>2-9</code>.\nOr tap <b>Skip</b>.",
        "ask_series":               "Building series? (optional)\nSelect one or tap <b>Any</b>.",
        "ask_long_term":            "Show only long-term rentals? (skip daily/short-term listings)",
        "ask_label":                "Give this filter a name? (optional)\nE.g. <i>Near work</i> — or tap <b>Skip</b>.",
        "filter_preview":           "📋 <b>Filter summary</b>\n\n{summary}\n\nSave this filter?",
        "filter_saved":             "✅ Filter saved. I'll alert you when something matches.",
        "filter_cancelled":         "Cancelled. No filter was saved.",
        "invalid_range":            "Please enter a valid range like <code>300-700</code> or a single number.",
        "invalid_number":           "Please enter a valid whole number.",

        "btn_any":                  "Any",
        "btn_skip":                 "Skip",
        "btn_yes":                  "Yes",
        "btn_no":                   "No",
        "btn_save":                 "Save filter",
        "btn_cancel":               "Cancel",
        "btn_delete":               "Delete",
        "btn_pause":                "Pause",
        "btn_resume":               "Resume",
        "btn_view":                 "👀 View",
        "btn_price_history":        "Price history",
        "btn_contact_seller":       "✉️ Contact seller",

        "no_filters":               "You have no active filters.\n\nUse /addfilter to create one.",
        "your_filters":             "📋 <b>Your filters</b>\n\nTap a filter to manage it.",
        "filter_deleted":           "🗑 Filter deleted.",
        "filter_paused":            "⏸ Filter paused.",
        "filter_resumed":           "▶️ Filter resumed.",

        "alert_hot_prefix":         "🔥 <b>HOT LISTING</b>\n\n",
        "alert_header":             "🏠 <b>New listing — {city}, {district}</b>",
        "alert_header_no_dist":     "🏠 <b>New listing — {city}</b>",
        "alert_price":              "💶 <b>{price} €/month</b>",
        "alert_no_price":           "💶 Price not listed",
        "alert_details":            "🚪 {rooms} rooms · 📐 {area} m²",
        "alert_floor":              "🏢 Floor {floor} of {floor_total}",
        "alert_series":             "🏗 {series}",
        "alert_contacts":           "📞 <b>Contacts:</b>\n{contacts}",
        "alert_no_contacts":        "📞 Contact info not listed",
        "alert_matched_filter":     "⚡ Matched filter: <i>{filter_name}</i>",
        "alert_filter_summary":     "🔍 <b>Your filter:</b>\n{filter_summary}",

        "subscribe_intro": (
            "⚡ <b>RentRadar Premium Features</b>\n\n"
            "All search filters are free. Premium adds speed + intelligence:\n\n"
            "⚡ <b>Priority speed</b> — alerts every 5 min instead of 30\n"
            "   2 €/month\n\n"
            "🔥 <b>Hot listing alerts</b> — instant push for below-market deals\n"
            "   1 €/month\n\n"
            "📈 <b>Price history</b> — track price changes on any listing\n"
            "   2 €/month\n\n"
            "📊 <b>Weekly analytics</b> — market digest every Monday\n"
            "   1 €/month\n\n"
            "🎯 <b>Pro bundle</b> — all 4 features\n"
            "   5 €/month (save 1 €)\n\n"
            "Choose what to unlock:"
        ),
        "payment_success":          "✅ <b>{feature}</b> activated until {date}.\n\nThank you!",
        "already_have_feature":     "You already have <b>{feature}</b> active until {date}.",
        "status_header":            "📊 <b>Your subscription status</b>",
        "status_plan_label":        "📋 Current plan: <b>{plan}</b>",
        "status_plan_pro":          "🎯 Pro bundle",
        "status_plan_free":         "🆓 Free",
        "status_free":              "You're on the free plan.",
        "status_feature_active":    "✅ {feature} — active until {date}",
        "status_feature_inactive":  "○ {feature} — not active",

        "history_header":           "📈 <b>Price history</b>\n\n",
        "history_no_data":          "No price changes recorded yet for this listing.",
        "history_entry":            "{date}: {price} €/month",
        "history_feature_required": "📈 Price history is a premium feature.\nUse /subscribe to unlock it.",

        "analytics_header":         "📊 <b>Weekly market report</b>\n\n",
        "analytics_no_data":        "No new listings recorded this week.",
        "analytics_feature_required": "📊 Weekly analytics is a premium feature.\nUse /subscribe to unlock it.",

        "error_generic":            "Something went wrong. Please try again.",
        "error_parse_failed":       "Could not reach ss.lv right now. Will retry shortly.",

        # filter list
        "any":                      "Any",
        "filter_item":              "#{n} <b>{label}</b>\n🏙 {city} · 📍 {district} · 💶 {price_max} · 🚪 {rooms_min}",

        # global pause
        "alerts_paused_msg":        "⏸ All alerts paused. Use /resume_all to enable.",
        "alerts_resumed_msg":       "▶️ Alerts enabled. You'll receive new matches.",
        "alerts_already_paused":    "Alerts are already paused.",
        "alerts_already_active":    "Alerts are already active.",

        # saved listings
        "btn_save_listing":         "💾 Save",
        "btn_unsave_listing":       "🗑 Remove from saved",
        "btn_add_note":             "📝 Add note",
        "btn_edit_note":            "✏️ Edit note",
        "note_prompt":              "Send your note (max 200 chars). Or /cancel_note to skip.",
        "note_saved":               "📝 Note saved.",
        "note_cancelled":           "Cancelled.",
        "note_too_long":            "Note must be under 200 characters.",
        "listing_saved":            "💾 Listing saved! View with /saved",
        "listing_unsaved":          "🗑 Removed from saved listings.",
        "listing_already_saved":    "Already in your saved listings.",
        "listing_save_error":       "Could not save this listing. It may no longer be in the database.",
        "saved_listings_header":    "💾 <b>Saved listings</b>\n\n",
        "no_saved_listings":        "You haven't saved any listings yet.\n\nTap 💾 Save in any alert to bookmark it.",

        # help with new commands
        "help": (
            "<b>Commands</b>\n\n"
            "/addfilter — create a new search filter\n"
            "/myfilters — view and manage your filters\n"
            "/saved — your saved listings\n"
            "/pause_all — pause all alerts\n"
            "/resume_all — resume alerts\n"
            "/subscribe — unlock premium features\n"
            "/status — your subscription status\n"
            "/language — change language\n"
            "/help — this message"
        ),

        # feedback
        "feedback_prompt":              "👋 Quick question — how are the alerts working for you?",
        "feedback_comment_prompt":      "Thanks! Want to add a comment? (optional)\nSend a message or tap Skip.",
        "feedback_thanks":              "Thanks for your feedback! 🙏",
        "feedback_comment_too_long":    "Comment must be under 500 characters.",

        # report
        "btn_report":               "⚠️ Report issue",
        "report_pick_reason":       "What's wrong with this listing?",
        "report_wrong_price":       "Wrong price",
        "report_already_rented":    "Already rented",
        "report_wrong_info":        "Wrong info (area, rooms, etc.)",
        "report_spam":              "Spam / duplicate",
        "report_submitted":         "✅ Thanks! Your report has been sent.",
    },

    "ru": {
        "choose_language":          "Выберите язык:",
        "language_set":             "Язык изменён на русский.",
        "welcome": (
            "👋 Добро пожаловать в RentRadar | Latvia!\n\n"
            "Я слежу за ss.lv по всей Латвии и уведомляю вас сразу, "
            "как только появляется квартира по вашим фильтрам.\n\n"
            "Все фильтры бесплатны. Используйте /addfilter чтобы начать поиск."
        ),
        "city":                     "Город",
        "district":                 "Район",
        "price":                    "Цена",
        "rooms":                    "Комнаты",
        "area":                     "Площадь",
        "floor":                    "Этаж",
        "series":                   "Серия",
        "long_term_only":           "Только долгосрочная аренда",

        "ask_city":                 "В каком городе ищете?",
        "ask_district":             "Выберите район.\nНажмите <b>Любой</b>, чтобы не ограничивать.",
        "ask_price_range":          "Диапазон цены в месяц (€)?\nВведите <code>мин-макс</code>, например <code>300-700</code>.\nИли нажмите <b>Пропустить</b>.",
        "ask_rooms_range":          "Количество комнат?\nВведите <code>мин-макс</code>, например <code>1-3</code>, или одно число.\nИли нажмите <b>Пропустить</b>.",
        "ask_area_range":           "Площадь (м²)?\nВведите <code>мин-макс</code>, например <code>40-80</code>.\nИли нажмите <b>Пропустить</b>.",
        "ask_floor_range":          "Этаж?\nВведите <code>мин-макс</code>, например <code>2-9</code>.\nИли нажмите <b>Пропустить</b>.",
        "ask_series":               "Серия дома? (необязательно)\nВыберите или нажмите <b>Любая</b>.",
        "ask_long_term":            "Показывать только долгосрочную аренду? (без посуточных)",
        "ask_label":                "Назовите этот фильтр? (необязательно)\nНапример: <i>Рядом с работой</i> — или нажмите <b>Пропустить</b>.",
        "filter_preview":           "📋 <b>Параметры фильтра</b>\n\n{summary}\n\nСохранить?",
        "filter_saved":             "✅ Фильтр сохранён. Пришлю уведомление, как только найдётся подходящий вариант.",
        "filter_cancelled":         "Отменено. Фильтр не сохранён.",
        "invalid_range":            "Введите диапазон вида <code>300-700</code> или одно число.",
        "invalid_number":           "Введите корректное целое число.",

        "btn_any":                  "Любой",
        "btn_skip":                 "Пропустить",
        "btn_yes":                  "Да",
        "btn_no":                   "Нет",
        "btn_save":                 "Сохранить фильтр",
        "btn_cancel":               "Отмена",
        "btn_delete":               "Удалить",
        "btn_pause":                "Пауза",
        "btn_resume":               "Возобновить",
        "btn_view":                 "👀 Смотреть",
        "btn_price_history":        "История цен",
        "btn_contact_seller":       "✉️ Написать продавцу",

        "no_filters":               "У вас нет активных фильтров.\n\nСоздайте первый через /addfilter.",
        "your_filters":             "📋 <b>Ваши фильтры</b>\n\nНажмите на фильтр для управления.",
        "filter_deleted":           "🗑 Фильтр удалён.",
        "filter_paused":            "⏸ Фильтр приостановлен.",
        "filter_resumed":           "▶️ Фильтр возобновлён.",

        "alert_hot_prefix":         "🔥 <b>ГОРЯЧЕЕ ОБЪЯВЛЕНИЕ</b>\n\n",
        "alert_header":             "🏠 <b>Новое объявление — {city}, {district}</b>",
        "alert_header_no_dist":     "🏠 <b>Новое объявление — {city}</b>",
        "alert_price":              "💶 <b>{price} €/мес</b>",
        "alert_no_price":           "💶 Цена не указана",
        "alert_details":            "🚪 {rooms} комн. · 📐 {area} м²",
        "alert_floor":              "🏢 Этаж {floor} из {floor_total}",
        "alert_series":             "🏗 {series}",
        "alert_contacts":           "📞 <b>Контакты:</b>\n{contacts}",
        "alert_no_contacts":        "📞 Контакты не указаны",
        "alert_matched_filter":     "⚡ Совпало с фильтром: <i>{filter_name}</i>",
        "alert_filter_summary":     "🔍 <b>Ваш фильтр:</b>\n{filter_summary}",

        "subscribe_intro": (
            "⚡ <b>RentRadar — Премиум функции</b>\n\n"
            "Все фильтры поиска бесплатны. Премиум добавляет скорость и аналитику:\n\n"
            "⚡ <b>Приоритетная скорость</b> — уведомления каждые 5 мин вместо 30\n"
            "   2 €/мес\n\n"
            "🔥 <b>Горячие объявления</b> — мгновенный алерт о выгодных предложениях\n"
            "   1 €/мес\n\n"
            "📈 <b>История цен</b> — отслеживание изменений цен\n"
            "   2 €/мес\n\n"
            "📊 <b>Еженедельная аналитика</b> — дайджест рынка каждый понедельник\n"
            "   1 €/мес\n\n"
            "🎯 <b>Pro пакет</b> — все 4 функции\n"
            "   5 €/мес (экономия 1 €)\n\n"
            "Выберите, что разблокировать:"
        ),
        "payment_success":          "✅ <b>{feature}</b> активировано до {date}.\n\nСпасибо!",
        "already_have_feature":     "<b>{feature}</b> уже активно до {date}.",
        "status_header":            "📊 <b>Ваш статус подписки</b>",
        "status_plan_label":        "📋 Текущий план: <b>{plan}</b>",
        "status_plan_pro":          "🎯 Pro пакет",
        "status_plan_free":         "🆓 Бесплатный",
        "status_free":              "Вы на бесплатном плане.",
        "status_feature_active":    "✅ {feature} — активно до {date}",
        "status_feature_inactive":  "○ {feature} — не активно",

        "history_header":           "📈 <b>История цен</b>\n\n",
        "history_no_data":          "Изменений цены ещё не зафиксировано.",
        "history_entry":            "{date}: {price} €/мес",
        "history_feature_required": "📈 История цен — премиум-функция.\nИспользуйте /subscribe для разблокировки.",

        "analytics_header":         "📊 <b>Еженедельный отчёт о рынке</b>\n\n",
        "analytics_no_data":        "За эту неделю новых объявлений не зафиксировано.",
        "analytics_feature_required": "📊 Еженедельная аналитика — премиум-функция.\nИспользуйте /subscribe для разблокировки.",

        "error_generic":            "Что-то пошло не так. Попробуйте ещё раз.",
        "error_parse_failed":       "Не удалось получить данные с ss.lv. Повторю попытку позже.",

        "any":                      "Любой",
        "filter_item":              "#{n} <b>{label}</b>\n🏙 {city} · 📍 {district} · 💶 {price_max} · 🚪 {rooms_min}",

        "alerts_paused_msg":        "⏸ Все уведомления приостановлены. Используйте /resume_all для возобновления.",
        "alerts_resumed_msg":       "▶️ Уведомления включены. Будете получать новые совпадения.",
        "alerts_already_paused":    "Уведомления уже приостановлены.",
        "alerts_already_active":    "Уведомления уже активны.",

        "btn_save_listing":         "💾 Сохранить",
        "btn_unsave_listing":       "🗑 Удалить из сохранённых",
        "btn_add_note":             "📝 Добавить заметку",
        "btn_edit_note":            "✏️ Изменить заметку",
        "note_prompt":              "Введите заметку (до 200 символов). Или /cancel_note для отмены.",
        "note_saved":               "📝 Заметка сохранена.",
        "note_cancelled":           "Отменено.",
        "note_too_long":            "Заметка должна быть до 200 символов.",
        "listing_saved":            "💾 Объявление сохранено! Посмотреть: /saved",
        "listing_unsaved":          "🗑 Удалено из сохранённых.",
        "listing_already_saved":    "Уже есть в сохранённых.",
        "listing_save_error":       "Не удалось сохранить. Объявление могло быть удалено из базы.",
        "saved_listings_header":    "💾 <b>Сохранённые объявления</b>\n\n",
        "no_saved_listings":        "Вы ещё не сохранили ни одного объявления.\n\nНажмите 💾 Сохранить в любом алерте.",

        "help": (
            "<b>Команды</b>\n\n"
            "/addfilter — создать фильтр\n"
            "/myfilters — мои фильтры\n"
            "/saved — сохранённые объявления\n"
            "/pause_all — приостановить все алерты\n"
            "/resume_all — возобновить алерты\n"
            "/subscribe — премиум-функции\n"
            "/status — статус подписки\n"
            "/language — изменить язык\n"
            "/help — это сообщение"
        ),

        # feedback
        "feedback_prompt":              "👋 Быстрый вопрос — как вам уведомления?",
        "feedback_comment_prompt":      "Спасибо! Хотите добавить комментарий? (необязательно)\nОтправьте сообщение или нажмите Пропустить.",
        "feedback_thanks":              "Спасибо за отзыв! 🙏",
        "feedback_comment_too_long":    "Комментарий должен быть до 500 символов.",

        # report
        "btn_report":               "⚠️ Сообщить об ошибке",
        "report_pick_reason":       "Что не так с этим объявлением?",
        "report_wrong_price":       "Неверная цена",
        "report_already_rented":    "Уже сдано",
        "report_wrong_info":        "Неверные данные (площадь, комнаты и т.д.)",
        "report_spam":              "Спам / дубликат",
        "report_submitted":         "✅ Спасибо! Мы получили ваш отчёт.",
    },

    "lv": {
        "choose_language":          "Izvēlieties valodu:",
        "language_set":             "Valoda mainīta uz latviešu.",
        "welcome": (
            "👋 Laipni lūdzam RentRadar | Latvia!\n\n"
            "Es uzraugu ss.lv visā Latvijā un nekavējoties brīdinu jūs, "
            "kad jauns dzīvoklis atbilst jūsu filtriem.\n\n"
            "Visi filtri ir bezmaksas. Izmantojiet /addfilter, lai sāktu meklēšanu."
        ),
        "city":                     "Pilsēta",
        "district":                 "Rajons",
        "price":                    "Cena",
        "rooms":                    "Istabas",
        "area":                     "Platība",
        "floor":                    "Stāvs",
        "series":                   "Sērija",
        "long_term_only":           "Tikai ilgtermiņa īre",

        "ask_city":                 "Kurā pilsētā meklējat?",
        "ask_district":             "Kurš rajons?\nNospiediet <b>Jebkurš</b>, lai neierobežotu.",
        "ask_price_range":          "Cenas diapazons mēnesī (€)?\nIevadiet <code>min-max</code>, piem. <code>300-700</code>.\nVai nospiediet <b>Izlaist</b>.",
        "ask_rooms_range":          "Istabu skaits?\nIevadiet <code>min-max</code>, piem. <code>1-3</code>, vai vienu skaitli.\nVai nospiediet <b>Izlaist</b>.",
        "ask_area_range":           "Platība (m²)?\nIevadiet <code>min-max</code>, piem. <code>40-80</code>.\nVai nospiediet <b>Izlaist</b>.",
        "ask_floor_range":          "Stāvs?\nIevadiet <code>min-max</code>, piem. <code>2-9</code>.\nVai nospiediet <b>Izlaist</b>.",
        "ask_series":               "Ēkas sērija? (neobligāti)\nIzvēlieties vai nospiediet <b>Jebkura</b>.",
        "ask_long_term":            "Rādīt tikai ilgtermiņa īri? (bez īslaicīgās)",
        "ask_label":                "Nosauciet šo filtru? (neobligāti)\nPiem. <i>Tuvu darbam</i> — vai nospiediet <b>Izlaist</b>.",
        "filter_preview":           "📋 <b>Filtra kopsavilkums</b>\n\n{summary}\n\nSaglabāt?",
        "filter_saved":             "✅ Filtrs saglabāts. Brīdināšu, tiklīdz kaut kas atbildīs.",
        "filter_cancelled":         "Atcelts. Filtrs netika saglabāts.",
        "invalid_range":            "Lūdzu ievadiet diapazonu formātā <code>300-700</code> vai vienu skaitli.",
        "invalid_number":           "Lūdzu ievadiet derīgu veselu skaitli.",

        "btn_any":                  "Jebkurš",
        "btn_skip":                 "Izlaist",
        "btn_yes":                  "Jā",
        "btn_no":                   "Nē",
        "btn_save":                 "Saglabāt filtru",
        "btn_cancel":               "Atcelt",
        "btn_delete":               "Dzēst",
        "btn_pause":                "Apturēt",
        "btn_resume":               "Atsākt",
        "btn_view":                 "👀 Skatīt",
        "btn_price_history":        "Cenu vēsture",
        "btn_contact_seller":       "✉️ Rakstīt pārdevējam",

        "no_filters":               "Jums nav aktīvu filtru.\n\nIzmantojiet /addfilter, lai izveidotu pirmo.",
        "your_filters":             "📋 <b>Jūsu filtri</b>\n\nNoklikšķiniet uz filtra, lai pārvaldītu.",
        "filter_deleted":           "🗑 Filtrs dzēsts.",
        "filter_paused":            "⏸ Filtrs apturēts.",
        "filter_resumed":           "▶️ Filtrs atsākts.",

        "alert_hot_prefix":         "🔥 <b>KARSTS SLUDINĀJUMS</b>\n\n",
        "alert_header":             "🏠 <b>Jauns sludinājums — {city}, {district}</b>",
        "alert_header_no_dist":     "🏠 <b>Jauns sludinājums — {city}</b>",
        "alert_price":              "💶 <b>{price} €/mēn</b>",
        "alert_no_price":           "💶 Cena nav norādīta",
        "alert_details":            "🚪 {rooms} ist. · 📐 {area} m²",
        "alert_floor":              "🏢 {floor}. stāvs no {floor_total}",
        "alert_series":             "🏗 {series}",
        "alert_contacts":           "📞 <b>Kontakti:</b>\n{contacts}",
        "alert_no_contacts":        "📞 Kontaktinformācija nav norādīta",
        "alert_matched_filter":     "⚡ Atbilst filtram: <i>{filter_name}</i>",
        "alert_filter_summary":     "🔍 <b>Jūsu filtrs:</b>\n{filter_summary}",

        "subscribe_intro": (
            "⚡ <b>RentRadar — Premium funkcijas</b>\n\n"
            "Visi meklēšanas filtri ir bezmaksas. Premium pievieno ātrumu un analītiku:\n\n"
            "⚡ <b>Prioritārais ātrums</b> — paziņojumi ik 5 min, nevis 30\n"
            "   2 €/mēn\n\n"
            "🔥 <b>Karstie sludinājumi</b> — tūlītējs signāls par izdevīgiem piedāvājumiem\n"
            "   1 €/mēn\n\n"
            "📈 <b>Cenu vēsture</b> — sekojiet cenu izmaiņām\n"
            "   2 €/mēn\n\n"
            "📊 <b>Iknedēļas analītika</b> — tirgus kopsavilkums katru pirmdienu\n"
            "   1 €/mēn\n\n"
            "🎯 <b>Pro pakete</b> — visas 4 funkcijas\n"
            "   5 €/mēn (ietaupiet 1 €)\n\n"
            "Izvēlieties, ko atbloķēt:"
        ),
        "payment_success":          "✅ <b>{feature}</b> aktivizēts līdz {date}.\n\nPaldies!",
        "already_have_feature":     "<b>{feature}</b> jau ir aktīvs līdz {date}.",
        "status_header":            "📊 <b>Jūsu abonēšanas statuss</b>",
        "status_plan_label":        "📋 Pašreizējais plāns: <b>{plan}</b>",
        "status_plan_pro":          "🎯 Pro pakete",
        "status_plan_free":         "🆓 Bezmaksas",
        "status_free":              "Jūs izmantojat bezmaksas plānu.",
        "status_feature_active":    "✅ {feature} — aktīvs līdz {date}",
        "status_feature_inactive":  "○ {feature} — nav aktīvs",

        "history_header":           "📈 <b>Cenu vēsture</b>\n\n",
        "history_no_data":          "Cenu izmaiņas vēl nav reģistrētas.",
        "history_entry":            "{date}: {price} €/mēn",
        "history_feature_required": "📈 Cenu vēsture ir premium funkcija.\nIzmantojiet /subscribe, lai atbloķētu.",

        "analytics_header":         "📊 <b>Iknedēļas tirgus pārskats</b>\n\n",
        "analytics_no_data":        "Šajā nedēļā nav reģistrēts neviens jauns sludinājums.",
        "analytics_feature_required": "📊 Iknedēļas analītika ir premium funkcija.\nIzmantojiet /subscribe, lai atbloķētu.",

        "error_generic":            "Kaut kas nogāja greizi. Lūdzu, mēģiniet vēlreiz.",
        "error_parse_failed":       "Nevarēja sasniegt ss.lv. Mēģināšu vēlreiz drīzumā.",

        "any":                      "Jebkurš",
        "filter_item":              "#{n} <b>{label}</b>\n🏙 {city} · 📍 {district} · 💶 {price_max} · 🚪 {rooms_min}",

        "alerts_paused_msg":        "⏸ Visi paziņojumi apturēti. Izmantojiet /resume_all, lai atsāktu.",
        "alerts_resumed_msg":       "▶️ Paziņojumi ieslēgti. Saņemsiet jaunas atbilstības.",
        "alerts_already_paused":    "Paziņojumi jau ir apturēti.",
        "alerts_already_active":    "Paziņojumi jau ir aktīvi.",

        "btn_save_listing":         "💾 Saglabāt",
        "btn_unsave_listing":       "🗑 Noņemt no saglabātajiem",
        "btn_add_note":             "📝 Pievienot piezīmi",
        "btn_edit_note":            "✏️ Rediģēt piezīmi",
        "note_prompt":              "Ievadiet piezīmi (līdz 200 rakstzīmēm). Vai /cancel_note, lai atceltu.",
        "note_saved":               "📝 Piezīme saglabāta.",
        "note_cancelled":           "Atcelts.",
        "note_too_long":            "Piezīmei jābūt līdz 200 rakstzīmēm.",
        "listing_saved":            "💾 Sludinājums saglabāts! Skatīt: /saved",
        "listing_unsaved":          "🗑 Noņemts no saglabātajiem.",
        "listing_already_saved":    "Jau saglabāts.",
        "listing_save_error":       "Nevarēja saglabāt. Sludinājums, iespējams, vairs nav datubāzē.",
        "saved_listings_header":    "💾 <b>Saglabātie sludinājumi</b>\n\n",
        "no_saved_listings":        "Jūs vēl neesat saglabājis nevienu sludinājumu.\n\nNospiediet 💾 Saglabāt jebkurā paziņojumā.",

        "help": (
            "<b>Komandas</b>\n\n"
            "/addfilter — izveidot filtru\n"
            "/myfilters — mani filtri\n"
            "/saved — saglabātie sludinājumi\n"
            "/pause_all — apturēt visus paziņojumus\n"
            "/resume_all — atsākt paziņojumus\n"
            "/subscribe — premium funkcijas\n"
            "/status — abonēšanas statuss\n"
            "/language — mainīt valodu\n"
            "/help — šī ziņa"
        ),

        # feedback
        "feedback_prompt":              "👋 Īss jautājums — kā darbojas paziņojumi?",
        "feedback_comment_prompt":      "Paldies! Vēlaties pievienot komentāru? (neobligāti)\nNosūtiet ziņu vai nospiediet Izlaist.",
        "feedback_thanks":              "Paldies par atsauksmi! 🙏",
        "feedback_comment_too_long":    "Komentāram jābūt līdz 500 rakstzīmēm.",

        # report
        "btn_report":               "⚠️ Ziņot par kļūdu",
        "report_pick_reason":       "Kas ir nepareizi šajā sludinājumā?",
        "report_wrong_price":       "Nepareiza cena",
        "report_already_rented":    "Jau izīrēts",
        "report_wrong_info":        "Nepareiza informācija (platība, istabas u.c.)",
        "report_spam":              "Surogātpasts / dublikāts",
        "report_submitted":         "✅ Paldies! Jūsu ziņojums ir nosūtīts.",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    text = STRINGS.get(lang, {}).get(key) or STRINGS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇱🇻 Latviski", callback_data="lang_lv"),
    ]])
