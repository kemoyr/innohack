# ──────────────────────────────────
#  All bot text constants (Russian)
# ──────────────────────────────────

# ── Welcome & Role ────────────────
WELCOME = (
    "<b>Добро пожаловать в Волонтёр+!</b>\n\n"
    "Это бот для учёта волонтёрской деятельности.\n"
    "Выберите свою роль:"
)
BTN_ROLE_VOLUNTEER = "Волонтёр"
BTN_ROLE_COORDINATOR = "Координатор"

# ── Registration ──────────────────
REG_ASK_NAME = "Введите ваше <b>ФИО</b>:"
REG_ASK_CITY = "Введите ваш <b>город</b>:"
REG_ASK_PHONE = "Введите ваш <b>номер телефона</b> (или нажмите «Пропустить»):"
REG_SUCCESS_VOLUNTEER = (
    "Регистрация завершена!\n"
    "Добро пожаловать, <b>{name}</b>! Вы зарегистрированы как волонтёр."
)
REG_SUCCESS_COORDINATOR = (
    "Регистрация завершена!\n"
    "Добро пожаловать, <b>{name}</b>! Вы зарегистрированы как координатор."
)
REG_ASK_PASSWORD = "Введите <b>пароль координатора</b>:"
REG_WRONG_PASSWORD = "Неверный пароль. Попробуйте ещё раз или нажмите /start."

# ── Volunteer Menu ────────────────
MENU_VOLUNTEER_HEADER = "<b>Главное меню волонтёра</b>"
BTN_SUBMIT_REPORT = "📝 Подать отчёт"
BTN_MY_STATS = "📊 Моя статистика"
BTN_MY_ACHIEVEMENTS = "🏅 Мои достижения"

# ── Submission Flow ───────────────
SUB_ASK_LOCATION = (
    "Отправьте вашу <b>геолокацию</b> (нажмите на скрепку → Геопозиция).\n"
    "Или нажмите «Пропустить», если не можете отправить."
)
SUB_ASK_PHOTOS = (
    "Отправьте <b>2-3 фотографии</b> с мероприятия.\n"
    "Хотя бы одна должна быть <b>селфи</b> (с вашим лицом).\n"
    "После загрузки нажмите «Далее»."
)
SUB_PHOTO_RECEIVED = "Фото #{num} получено."
SUB_PHOTO_STATUS = (
    "Фото #{num}: EXIF {exif} | Гео {geo} | Лицо {face}"
)
SUB_BTN_NEXT = "Далее ➡️"
SUB_BTN_SKIP = "Пропустить"
SUB_ASK_QR = (
    "Отправьте <b>QR-код</b> мероприятия.\n"
    "Можно отправить фото QR-кода или текст кода."
)
SUB_MIN_PHOTOS = "Нужно отправить минимум <b>2 фотографии</b>."

# ── Verification Results ──────────
VERIFY_EXIF_FAIL = "⚠️ Не удалось извлечь EXIF-данные из фотографий."
VERIFY_GEO_FAIL = "⚠️ Геолокация не совпадает с местом мероприятия."
VERIFY_SELFIE_FAIL = "⚠️ Не обнаружено лицо ни на одной фотографии. Нужно хотя бы одно селфи."
VERIFY_QR_FAIL = "⚠️ QR-код не распознан или недействителен."
VERIFY_QR_ALREADY_USED = "⚠️ Этот QR-код уже был использован вами."
VERIFY_QR_INVALID = "⚠️ QR-код не найден в базе мероприятий. Попробуйте ещё раз."
VERIFY_ALL_PASSED = "✅ Все проверки пройдены!"
VERIFY_POINTS_AWARDED = "🎉 Вам начислено <b>{points}</b> баллов!"
VERIFY_SUBMISSION_SAVED = (
    "✅ Отчёт сохранён!\n"
    "Мероприятие: <b>{event_title}</b>\n"
    "Баллы: <b>+{points}</b>\n"
    "Всего баллов: <b>{total_points}</b>"
)
VERIFY_SUBMISSION_REJECTED = (
    "❌ Отчёт отклонён.\n"
    "Причина: {reason}\n\n"
    "Попробуйте отправить отчёт заново."
)

# ── Demo mode warnings ────────────
DEMO_EXIF_WARNING = "ℹ️ DEMO: EXIF-данные отсутствуют (сжатие Telegram). Пропускаем проверку."

# ── Coordinator Menu ──────────────
MENU_COORDINATOR_HEADER = "<b>Главное меню координатора</b>"
BTN_TEAM = "👥 Команда"
BTN_STATS = "📊 Статистика"
BTN_CALENDAR = "📅 Календарь"
BTN_RATINGS = "🏆 Рейтинг"
BTN_GENERATE_QR = "🔲 Создать QR"
BTN_DASHBOARD = "🌐 Открыть дашборд"
BTN_BACK = "◀️ Назад"

# ── Team ──────────────────────────
TEAM_HEADER = "<b>👥 Команда волонтёров</b>\n\nВсего: {count}"
TEAM_VOLUNTEER_ROW = "{i}. {name} — {points} баллов"
TEAM_VOLUNTEER_DETAIL = (
    "<b>{name}</b>\n"
    "Город: {city}\n"
    "Телефон: {phone}\n"
    "Роль: {role}\n"
    "Баллов: {points}\n"
    "Отчётов: {submissions}\n"
    "Статус: {status}\n"
    "Зарегистрирован: {created_at}"
)

# ── Stats ─────────────────────────
STATS_HEADER = "<b>📊 Статистика</b>"
STATS_FORMAT = (
    "Всего мероприятий: <b>{total_events}</b>\n"
    "Завершённых: <b>{completed_events}</b>\n"
    "На этой неделе: <b>{this_week_events}</b>\n"
    "В этом месяце: <b>{this_month_events}</b>\n"
    "Всего волонтёров: <b>{total_volunteers}</b>\n"
    "Активных: <b>{active_volunteers}</b>"
)

MY_STATS_FORMAT = (
    "<b>📊 Ваша статистика</b>\n\n"
    "Баллов: <b>{points}</b>\n"
    "Отчётов: <b>{submissions_count}</b>\n"
    "Достижений: <b>{achievements_count}</b>"
)

# ── Calendar ──────────────────────
CALENDAR_HEADER = "<b>📅 Календарь мероприятий</b>"
CALENDAR_PLANNED = "🔵 {title} — {date}"
CALENDAR_COMPLETED = "✅ {title} — {date} (участников: {attendance})"
CALENDAR_EMPTY = "Нет запланированных мероприятий."
CALENDAR_ASK_ATTENDANCE = "Введите количество участников:"
CALENDAR_EVENT_COMPLETED = "✅ Мероприятие «{title}» отмечено как завершённое."

# ── QR Generation ─────────────────
QR_ASK_TITLE = "Введите <b>название мероприятия</b>:"
QR_ASK_DATE = "Введите <b>дату</b> мероприятия (ДД.ММ.ГГГГ):"
QR_ASK_LOCATION = "Введите <b>место проведения</b>:"
QR_GENERATED = (
    "✅ QR-код создан!\n\n"
    "Мероприятие: <b>{title}</b>\n"
    "Дата: <b>{date}</b>\n"
    "Место: <b>{location}</b>\n"
    "Код: <code>{code}</code>"
)

# ── Ratings ───────────────────────
RATINGS_HEADER = "<b>🏆 Рейтинг волонтёров</b>\n"
RATINGS_PODIUM = "{medal} <b>{name}</b> — {points} баллов"
RATINGS_ROW = "{i}. {name} — {points} баллов"
RATINGS_EMPTY = "Пока нет данных для рейтинга."

MEDAL_FIRST = "🥇"
MEDAL_SECOND = "🥈"
MEDAL_THIRD = "🥉"

# ── Achievements ──────────────────
ACHIEVEMENT_EARNED = "🏅 <b>Новое достижение!</b>\n\n{title}\n{description}"
ACHIEVEMENTS_HEADER = "<b>🏅 Ваши достижения</b>\n"
ACHIEVEMENTS_ROW = "• <b>{title}</b> — {description}"
ACHIEVEMENTS_EMPTY = "У вас пока нет достижений. Подавайте отчёты, чтобы получать награды!"

# Achievement definitions
ACH_FIRST_REPORT_TITLE = "Первый шаг"
ACH_FIRST_REPORT_DESC = "Подан первый отчёт"
ACH_FIVE_REPORTS_TITLE = "Активист"
ACH_FIVE_REPORTS_DESC = "Подано 5 отчётов"
ACH_TEN_REPORTS_TITLE = "Ветеран"
ACH_TEN_REPORTS_DESC = "Подано 10 отчётов"
ACH_100_POINTS_TITLE = "Сотня"
ACH_100_POINTS_DESC = "Набрано 100 баллов"
ACH_500_POINTS_TITLE = "Полтысячи"
ACH_500_POINTS_DESC = "Набрано 500 баллов"

# ── Errors ────────────────────────
ERROR_GENERAL = "Произошла ошибка. Попробуйте позже."
ERROR_NOT_REGISTERED = "Вы не зарегистрированы. Нажмите /start для начала."
ERROR_NO_PERMISSION = "У вас нет прав для этого действия."

# ── New Buttons ──────────────────
BTN_HELP = "Помощь"
BTN_MY_PROFILE = "Мой профиль"
BTN_EVENTS = "Мероприятия"
BTN_OPEN_APP = "Открыть приложение"

# ── Help ─────────────────────────
HELP_TEXT = (
    "<b>Команды бота:</b>\n\n"
    "/start — Главное меню\n"
    "/profile — Мой профиль\n"
    "/events — Предстоящие мероприятия\n"
    "/help — Справка\n\n"
    "<b>Как подать отчёт:</b>\n"
    "1. Нажмите «Подать отчёт»\n"
    "2. Отправьте геолокацию места\n"
    "3. Загрузите 2-3 фото (одно — селфи)\n"
    "4. Отсканируйте QR-код организатора\n"
    "5. Получите баллы!\n\n"
    "<b>Проверки фотографий:</b>\n"
    "• Метаданные (EXIF): дата и время съёмки\n"
    "• Геолокация: совпадение с местом\n"
    "• Распознавание лица: минимум одно селфи"
)

# ── Profile ──────────────────────
PROFILE_FORMAT = (
    "<b>Профиль</b>\n\n"
    "Имя: <b>{name}</b>\n"
    "Город: {city}\n"
    "Статус: {status}\n\n"
    "Баллы: <b>{points}</b>\n"
    "Место в рейтинге: <b>{rank}</b>\n"
    "Отчётов: <b>{submissions}</b>\n"
    "Достижений: <b>{achievements}</b>"
)

# ── Events (volunteer view) ─────
UPCOMING_EVENTS_HEADER = "<b>Предстоящие мероприятия:</b>\n"
UPCOMING_EVENT_ROW = "• <b>{title}</b>\n  {date} | {location}"
NO_UPCOMING_EVENTS = "Нет предстоящих мероприятий."

# ── Misc ──────────────────────────
BTN_SKIP = "Пропустить"
DASHBOARD_LINK = '🌐 <a href="http://localhost:8000">Открыть дашборд</a>'
