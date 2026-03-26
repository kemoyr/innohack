import io
import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BufferedInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from bot.database import (
    get_volunteer,
    get_all_volunteers,
    get_volunteer_submissions,
    get_achievements,
    get_stats,
    get_planned_events,
    get_completed_events,
    get_leaderboard,
    create_event,
    update_event_status,
)
from bot.utils.qr import generate_qr_image, generate_event_code
from bot.handlers.start import show_coordinator_menu, coordinator_menu_keyboard
from bot import strings

logger = logging.getLogger(__name__)

router = Router(name="coordinator")


# ── FSM States ────────────────────

class QRGeneration(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_location = State()


class EventCompletion(StatesGroup):
    waiting_attendance = State()


# ── Team ──────────────────────────

@router.message(F.text == strings.BTN_TEAM)
async def team_list(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer or volunteer["role"] != "coordinator":
            await message.answer(strings.ERROR_NO_PERMISSION)
            return

        volunteers = await get_all_volunteers()
        if not volunteers:
            await message.answer(strings.TEAM_HEADER.format(count=0))
            return

        text = strings.TEAM_HEADER.format(count=len(volunteers)) + "\n\n"

        buttons = []
        for i, v in enumerate(volunteers, 1):
            text += strings.TEAM_VOLUNTEER_ROW.format(
                i=i, name=v["full_name"], points=v["points"]
            ) + "\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{v['full_name']}", callback_data=f"vol_detail:{v['id']}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        await message.answer(text, reply_markup=keyboard)
    except Exception as e:
        logger.error("Error showing team: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.callback_query(F.data.startswith("vol_detail:"))
async def volunteer_detail(callback: CallbackQuery):
    try:
        await callback.answer()
        vol_id = int(callback.data.split(":")[1])

        # Get volunteer by id
        volunteers = await get_all_volunteers()
        vol = None
        for v in volunteers:
            if v["id"] == vol_id:
                vol = v
                break

        if not vol:
            await callback.message.answer("Волонтёр не найден.")
            return

        submissions = await get_volunteer_submissions(vol_id)
        role_text = "Координатор" if vol["role"] == "coordinator" else "Волонтёр"
        status_text = "Активен" if vol["status"] == "active" else "Неактивен"

        text = strings.TEAM_VOLUNTEER_DETAIL.format(
            name=vol["full_name"],
            city=vol["city"] or "—",
            phone=vol["phone"] or "—",
            role=role_text,
            points=vol["points"],
            submissions=len(submissions),
            status=status_text,
            created_at=vol["created_at"] or "—",
        )
        await callback.message.answer(text)
    except Exception as e:
        logger.error("Error showing volunteer detail: %s", e)


# ── Stats ─────────────────────────

@router.message(F.text == strings.BTN_STATS)
async def show_stats(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer or volunteer["role"] != "coordinator":
            await message.answer(strings.ERROR_NO_PERMISSION)
            return

        stats = await get_stats()
        text = strings.STATS_HEADER + "\n\n" + strings.STATS_FORMAT.format(**stats)
        await message.answer(text)
    except Exception as e:
        logger.error("Error showing stats: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Calendar ──────────────────────

@router.message(F.text == strings.BTN_CALENDAR)
async def show_calendar(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer or volunteer["role"] != "coordinator":
            await message.answer(strings.ERROR_NO_PERMISSION)
            return

        planned = await get_planned_events()
        completed = await get_completed_events()

        if not planned and not completed:
            await message.answer(strings.CALENDAR_HEADER + "\n\n" + strings.CALENDAR_EMPTY)
            return

        text = strings.CALENDAR_HEADER + "\n\n"

        buttons = []
        if planned:
            text += "<b>Запланированные:</b>\n"
            for ev in planned:
                date_str = ev["scheduled_date"] or "—"
                text += strings.CALENDAR_PLANNED.format(title=ev["title"], date=date_str) + "\n"
                buttons.append([
                    InlineKeyboardButton(
                        text=f"✅ Завершить: {ev['title']}",
                        callback_data=f"complete_event:{ev['id']}",
                    )
                ])
            text += "\n"

        if completed:
            text += "<b>Завершённые:</b>\n"
            for ev in completed:
                date_str = ev["scheduled_date"] or "—"
                text += strings.CALENDAR_COMPLETED.format(
                    title=ev["title"], date=date_str, attendance=ev["attendance_count"]
                ) + "\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        await message.answer(text, reply_markup=keyboard)
    except Exception as e:
        logger.error("Error showing calendar: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.callback_query(F.data.startswith("complete_event:"))
async def complete_event_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        event_id = int(callback.data.split(":")[1])
        await state.update_data(completing_event_id=event_id)
        await state.set_state(EventCompletion.waiting_attendance)
        await callback.message.answer(strings.CALENDAR_ASK_ATTENDANCE)
    except Exception as e:
        logger.error("Error starting event completion: %s", e)


@router.message(EventCompletion.waiting_attendance)
async def process_attendance(message: Message, state: FSMContext):
    try:
        text = message.text.strip()
        if not text.isdigit():
            await message.answer(strings.CALENDAR_ASK_ATTENDANCE)
            return

        attendance = int(text)
        data = await state.get_data()
        event_id = data["completing_event_id"]

        await update_event_status(event_id, "completed", attendance)

        # Get event title for the message
        from bot.database import get_all_events
        events = await get_all_events()
        title = "Мероприятие"
        for ev in events:
            if ev["id"] == event_id:
                title = ev["title"]
                break

        await state.clear()
        await message.answer(
            strings.CALENDAR_EVENT_COMPLETED.format(title=title),
            reply_markup=coordinator_menu_keyboard(),
        )
    except Exception as e:
        logger.error("Error completing event: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Ratings ───────────────────────

@router.message(F.text == strings.BTN_RATINGS)
async def show_ratings(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer or volunteer["role"] != "coordinator":
            await message.answer(strings.ERROR_NO_PERMISSION)
            return

        leaders = await get_leaderboard(10)
        if not leaders:
            await message.answer(strings.RATINGS_HEADER + "\n" + strings.RATINGS_EMPTY)
            return

        medals = [strings.MEDAL_FIRST, strings.MEDAL_SECOND, strings.MEDAL_THIRD]
        lines = [strings.RATINGS_HEADER]

        for i, v in enumerate(leaders):
            if i < 3:
                lines.append(strings.RATINGS_PODIUM.format(
                    medal=medals[i], name=v["full_name"], points=v["points"]
                ))
            else:
                lines.append(strings.RATINGS_ROW.format(
                    i=i + 1, name=v["full_name"], points=v["points"]
                ))

        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error("Error showing ratings: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── QR Generation ─────────────────

@router.message(F.text == strings.BTN_GENERATE_QR)
async def start_qr_generation(message: Message, state: FSMContext):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer or volunteer["role"] != "coordinator":
            await message.answer(strings.ERROR_NO_PERMISSION)
            return

        await state.update_data(coordinator_id=volunteer["id"])
        await message.answer(strings.QR_ASK_TITLE)
        await state.set_state(QRGeneration.waiting_title)
    except Exception as e:
        logger.error("Error starting QR generation: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(QRGeneration.waiting_title)
async def qr_process_title(message: Message, state: FSMContext):
    try:
        await state.update_data(event_title=message.text.strip())
        await message.answer(strings.QR_ASK_DATE)
        await state.set_state(QRGeneration.waiting_date)
    except Exception as e:
        logger.error("Error processing QR title: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(QRGeneration.waiting_date)
async def qr_process_date(message: Message, state: FSMContext):
    try:
        date_text = message.text.strip()
        # Try to parse DD.MM.YYYY
        try:
            from datetime import datetime
            parsed = datetime.strptime(date_text, "%d.%m.%Y")
            scheduled_date = parsed.strftime("%Y-%m-%d")
        except ValueError:
            scheduled_date = date_text  # store as-is if parsing fails

        await state.update_data(event_date=date_text, scheduled_date=scheduled_date)
        await message.answer(strings.QR_ASK_LOCATION)
        await state.set_state(QRGeneration.waiting_location)
    except Exception as e:
        logger.error("Error processing QR date: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(QRGeneration.waiting_location)
async def qr_process_location(message: Message, state: FSMContext):
    try:
        location_name = message.text.strip()
        data = await state.get_data()

        event_title = data["event_title"]
        event_date = data["event_date"]
        scheduled_date = data.get("scheduled_date", "")
        coordinator_id = data["coordinator_id"]

        # Generate unique QR code
        code = generate_event_code()

        # Create event in DB
        await create_event(
            title=event_title,
            description="",
            location_name=location_name,
            lat=None,
            lon=None,
            scheduled_date=scheduled_date,
            qr_code=code,
            coordinator_id=coordinator_id,
        )

        # Generate QR image
        qr_bytes = generate_qr_image(code)

        await state.clear()

        text = strings.QR_GENERATED.format(
            title=event_title,
            date=event_date,
            location=location_name,
            code=code,
        )

        await message.answer_photo(
            photo=BufferedInputFile(qr_bytes, filename="qr_code.png"),
            caption=text,
            reply_markup=coordinator_menu_keyboard(),
        )
    except Exception as e:
        logger.error("Error generating QR: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Dashboard Link ────────────────

@router.message(F.text == strings.BTN_DASHBOARD)
async def send_dashboard_link(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer or volunteer["role"] != "coordinator":
            await message.answer(strings.ERROR_NO_PERMISSION)
            return
        await message.answer(strings.DASHBOARD_LINK)
    except Exception as e:
        logger.error("Error sending dashboard link: %s", e)
        await message.answer(strings.ERROR_GENERAL)
