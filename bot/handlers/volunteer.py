import logging
import os
import tempfile

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from bot.config import settings
from bot.database import (
    get_volunteer,
    get_event_by_qr,
    mark_qr_used,
    create_submission,
    add_points,
    add_achievement,
    get_achievements,
    get_volunteer_submissions,
    get_leaderboard,
    get_planned_events,
)
from bot.utils.exif import extract_exif, is_recent
from bot.utils.geo import is_location_match
from bot.utils.face import detect_face
from bot.utils.qr import read_qr_from_image
from bot.handlers.start import show_volunteer_menu
from bot import strings

logger = logging.getLogger(__name__)

router = Router(name="volunteer")

DEMO_MODE = settings.DEMO_MODE


# ── FSM States ────────────────────

class SubmissionFlow(StatesGroup):
    waiting_location = State()
    waiting_photos = State()
    waiting_qr = State()


# ── Keyboards ─────────────────────

def photos_keyboard(photo_count: int):
    buttons = []
    if photo_count >= 2:
        buttons.append([KeyboardButton(text=strings.SUB_BTN_NEXT)])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True) if buttons else ReplyKeyboardRemove()


def skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=strings.SUB_BTN_SKIP)]],
        resize_keyboard=True,
    )


# ── Help ─────────────────────────

@router.message(Command("help"))
@router.message(F.text == strings.BTN_HELP)
async def show_help(message: Message):
    try:
        await message.answer(strings.HELP_TEXT)
    except Exception as e:
        logger.error("Error showing help: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Profile ──────────────────────

@router.message(Command("profile"))
@router.message(F.text == strings.BTN_MY_PROFILE)
async def show_profile(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer:
            await message.answer(strings.ERROR_NOT_REGISTERED)
            return
        submissions = await get_volunteer_submissions(volunteer["id"])
        achievements = await get_achievements(volunteer["id"])
        leaderboard = await get_leaderboard(100)
        rank = next(
            (i + 1 for i, v in enumerate(leaderboard) if v["id"] == volunteer["id"]),
            "—",
        )

        await message.answer(strings.PROFILE_FORMAT.format(
            name=volunteer["full_name"],
            city=volunteer["city"] or "—",
            points=volunteer["points"],
            rank=rank,
            submissions=len(submissions),
            achievements=len(achievements),
            status="Активен" if volunteer["status"] == "active" else "Неактивен",
        ))
    except Exception as e:
        logger.error("Error showing profile: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Events ───────────────────────

@router.message(Command("events"))
@router.message(F.text == strings.BTN_EVENTS)
async def show_events(message: Message):
    try:
        events = await get_planned_events()
        if not events:
            await message.answer(strings.NO_UPCOMING_EVENTS)
            return
        lines = [strings.UPCOMING_EVENTS_HEADER]
        for ev in events[:5]:
            lines.append(strings.UPCOMING_EVENT_ROW.format(
                title=ev["title"],
                date=ev["scheduled_date"] or "—",
                location=ev["location_name"] or "—",
            ))
        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error("Error showing events: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Submit Report ─────────────────

@router.message(F.text == strings.BTN_SUBMIT_REPORT)
async def start_submission(message: Message, state: FSMContext):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer:
            await message.answer(strings.ERROR_NOT_REGISTERED)
            return
        await state.update_data(
            volunteer_id=volunteer["id"],
            lat=None,
            lon=None,
            photo_results=[],
        )
        await message.answer(strings.SUB_ASK_LOCATION, reply_markup=skip_keyboard())
        await state.set_state(SubmissionFlow.waiting_location)
    except Exception as e:
        logger.error("Error starting submission: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Location ──────────────────────

@router.message(SubmissionFlow.waiting_location, F.location)
async def process_location(message: Message, state: FSMContext):
    try:
        await state.update_data(
            lat=message.location.latitude,
            lon=message.location.longitude,
        )
        await message.answer(strings.SUB_ASK_PHOTOS, reply_markup=ReplyKeyboardRemove())
        await state.set_state(SubmissionFlow.waiting_photos)
    except Exception as e:
        logger.error("Error processing location: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(SubmissionFlow.waiting_location, F.text == strings.SUB_BTN_SKIP)
async def skip_location(message: Message, state: FSMContext):
    try:
        await message.answer(strings.SUB_ASK_PHOTOS, reply_markup=ReplyKeyboardRemove())
        await state.set_state(SubmissionFlow.waiting_photos)
    except Exception as e:
        logger.error("Error skipping location: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Photos ────────────────────────

@router.message(SubmissionFlow.waiting_photos, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    tmp_path = None
    try:
        data = await state.get_data()
        photo_results = data.get("photo_results", [])
        user_lat = data.get("lat")
        user_lon = data.get("lon")

        # Download photo to temp file
        photo = message.photo[-1]  # highest resolution
        file_info = await bot.get_file(photo.file_id)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(tmp_fd)

        await bot.download_file(file_info.file_path, tmp_path)

        # Analyse photo
        exif_data = extract_exif(tmp_path)
        exif_ok = False
        geo_ok = False
        has_face = False

        # EXIF check
        if exif_data["datetime"] and is_recent(exif_data["datetime"]):
            exif_ok = True
        elif DEMO_MODE:
            logger.warning("DEMO: EXIF missing or not recent, skipping strict check")
            exif_ok = True  # lenient in demo mode

        # Geo check
        if exif_data["lat"] and exif_data["lon"] and user_lat and user_lon:
            geo_ok = is_location_match(exif_data["lat"], exif_data["lon"], user_lat, user_lon)
        elif user_lat and user_lon:
            # No EXIF GPS, but user sent location — accept in demo mode
            if DEMO_MODE:
                geo_ok = True
        elif DEMO_MODE:
            geo_ok = True  # no location at all, lenient in demo

        # Face detection (always run)
        has_face = detect_face(tmp_path)

        photo_results.append({
            "exif_ok": exif_ok,
            "geo_ok": geo_ok,
            "has_face": has_face,
        })
        await state.update_data(photo_results=photo_results)

        num = len(photo_results)

        # Status icons
        exif_icon = "✅" if exif_ok else "❌"
        geo_icon = "✅" if geo_ok else "❌"
        face_icon = "✅" if has_face else "❌"

        status_text = strings.SUB_PHOTO_STATUS.format(
            num=num, exif=exif_icon, geo=geo_icon, face=face_icon
        )

        if not exif_data["datetime"] and DEMO_MODE:
            status_text += "\n" + strings.DEMO_EXIF_WARNING

        if num >= 3:
            await message.answer(status_text)
            await _finalize_photos(message, state)
        else:
            await message.answer(status_text, reply_markup=photos_keyboard(num))

    except Exception as e:
        logger.error("Error processing photo: %s", e)
        await message.answer(strings.ERROR_GENERAL)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.message(SubmissionFlow.waiting_photos, F.text == strings.SUB_BTN_NEXT)
async def next_after_photos(message: Message, state: FSMContext):
    try:
        await _finalize_photos(message, state)
    except Exception as e:
        logger.error("Error finalizing photos: %s", e)
        await message.answer(strings.ERROR_GENERAL)


async def _finalize_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_results = data.get("photo_results", [])

    # Validate
    if len(photo_results) < 2:
        await message.answer(strings.SUB_MIN_PHOTOS, reply_markup=photos_keyboard(len(photo_results)))
        return

    has_any_exif = any(p["exif_ok"] for p in photo_results)
    has_any_face = any(p["has_face"] for p in photo_results)

    rejection_reasons = []

    if not has_any_exif and not DEMO_MODE:
        rejection_reasons.append(strings.VERIFY_EXIF_FAIL)

    if not has_any_face:
        rejection_reasons.append(strings.VERIFY_SELFIE_FAIL)

    if rejection_reasons:
        reason_text = "\n".join(rejection_reasons)
        await message.answer(
            strings.VERIFY_SUBMISSION_REJECTED.format(reason=reason_text),
            reply_markup=ReplyKeyboardRemove(),
        )
        volunteer = await get_volunteer(message.from_user.id)
        if volunteer:
            await show_volunteer_menu(message, volunteer)
        await state.clear()
        return

    # Proceed to QR step
    await message.answer(strings.SUB_ASK_QR, reply_markup=skip_keyboard())
    await state.set_state(SubmissionFlow.waiting_qr)


# ── QR Code ───────────────────────

@router.message(SubmissionFlow.waiting_qr, F.text == strings.SUB_BTN_SKIP)
async def skip_qr(message: Message, state: FSMContext):
    """Allow skipping QR in demo mode — award reduced points."""
    try:
        await _complete_submission(message, state, qr_code=None, event=None)
    except Exception as e:
        logger.error("Error skipping QR: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(SubmissionFlow.waiting_qr, F.photo)
async def process_qr_photo(message: Message, state: FSMContext, bot: Bot):
    tmp_path = None
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(tmp_fd)
        await bot.download_file(file_info.file_path, tmp_path)

        qr_text = read_qr_from_image(tmp_path)

        if not qr_text:
            await message.answer(strings.VERIFY_QR_FAIL)
            return

        await _validate_and_complete_qr(message, state, qr_text)
    except Exception as e:
        logger.error("Error processing QR photo: %s", e)
        await message.answer(strings.ERROR_GENERAL)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.message(SubmissionFlow.waiting_qr, F.text)
async def process_qr_text(message: Message, state: FSMContext):
    try:
        qr_text = message.text.strip()
        await _validate_and_complete_qr(message, state, qr_text)
    except Exception as e:
        logger.error("Error processing QR text: %s", e)
        await message.answer(strings.ERROR_GENERAL)


async def _validate_and_complete_qr(message: Message, state: FSMContext, qr_text: str):
    data = await state.get_data()
    volunteer_id = data["volunteer_id"]

    event = await get_event_by_qr(qr_text)
    if not event:
        await message.answer(strings.VERIFY_QR_INVALID)
        return

    already_used = await mark_qr_used(qr_text, volunteer_id)
    if already_used:
        await message.answer(strings.VERIFY_QR_ALREADY_USED)
        return

    await _complete_submission(message, state, qr_code=qr_text, event=event)


async def _complete_submission(message: Message, state: FSMContext, qr_code, event):
    data = await state.get_data()
    volunteer_id = data["volunteer_id"]
    photo_results = data.get("photo_results", [])
    user_lat = data.get("lat")
    user_lon = data.get("lon")

    has_any_exif = any(p["exif_ok"] for p in photo_results)
    has_any_face = any(p["has_face"] for p in photo_results)
    has_any_geo = any(p["geo_ok"] for p in photo_results)

    # Calculate points
    base_points = 50
    bonus = 0
    if has_any_exif:
        bonus += 10
    if has_any_geo:
        bonus += 10
    if has_any_face:
        bonus += 10
    if qr_code:
        bonus += 20
    total_points = base_points + bonus

    event_id = event["id"] if event else None
    event_title = event["title"] if event else "Без QR-кода"

    sub_id = await create_submission(
        volunteer_id=volunteer_id,
        event_id=event_id,
        lat=user_lat,
        lon=user_lon,
        photo_count=len(photo_results),
        selfie_verified=int(has_any_face),
        geo_verified=int(has_any_geo),
        exif_verified=int(has_any_exif),
        qr_verified=int(bool(qr_code)),
        qr_code=qr_code or "",
        points_awarded=total_points,
        status="verified",
        rejection_reason="",
    )

    await add_points(
        volunteer_id=volunteer_id,
        amount=total_points,
        reason=f"Отчёт: {event_title}",
        submission_id=sub_id,
    )

    # Get updated volunteer
    volunteer = await get_volunteer(message.from_user.id)
    total_volunteer_points = volunteer["points"] if volunteer else total_points

    await message.answer(strings.VERIFY_ALL_PASSED, reply_markup=ReplyKeyboardRemove())
    await message.answer(
        strings.VERIFY_SUBMISSION_SAVED.format(
            event_title=event_title,
            points=total_points,
            total_points=total_volunteer_points,
        )
    )

    # Check achievements
    await _check_achievements(message, volunteer_id)

    await state.clear()
    if volunteer:
        await show_volunteer_menu(message, volunteer)


async def _check_achievements(message: Message, volunteer_id: int):
    try:
        existing = await get_achievements(volunteer_id)
        existing_types = {a["badge_type"] for a in existing}

        submissions = await get_volunteer_submissions(volunteer_id)
        volunteer = None

        # Fetch volunteer for points
        from bot.database import get_all_volunteers
        all_vols = await get_all_volunteers()
        for v in all_vols:
            if v["id"] == volunteer_id:
                volunteer = v
                break

        new_achievements = []

        # First report
        if len(submissions) >= 1 and "first_report" not in existing_types:
            new_achievements.append(("first_report", strings.ACH_FIRST_REPORT_TITLE, strings.ACH_FIRST_REPORT_DESC))

        # 5 reports
        if len(submissions) >= 5 and "five_reports" not in existing_types:
            new_achievements.append(("five_reports", strings.ACH_FIVE_REPORTS_TITLE, strings.ACH_FIVE_REPORTS_DESC))

        # 10 reports
        if len(submissions) >= 10 and "ten_reports" not in existing_types:
            new_achievements.append(("ten_reports", strings.ACH_TEN_REPORTS_TITLE, strings.ACH_TEN_REPORTS_DESC))

        if volunteer:
            # 100 points
            if volunteer["points"] >= 100 and "100_points" not in existing_types:
                new_achievements.append(("100_points", strings.ACH_100_POINTS_TITLE, strings.ACH_100_POINTS_DESC))

            # 500 points
            if volunteer["points"] >= 500 and "500_points" not in existing_types:
                new_achievements.append(("500_points", strings.ACH_500_POINTS_TITLE, strings.ACH_500_POINTS_DESC))

        for badge_type, title, description in new_achievements:
            await add_achievement(volunteer_id, badge_type, title, description)
            try:
                await message.answer(
                    strings.ACHIEVEMENT_EARNED.format(title=title, description=description)
                )
            except Exception as e:
                logger.error("Error sending achievement notification: %s", e)

    except Exception as e:
        logger.error("Error checking achievements: %s", e)


# ── My Stats ──────────────────────

@router.message(F.text == strings.BTN_MY_STATS)
async def my_stats(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer:
            await message.answer(strings.ERROR_NOT_REGISTERED)
            return

        submissions = await get_volunteer_submissions(volunteer["id"])
        achievements = await get_achievements(volunteer["id"])

        await message.answer(
            strings.MY_STATS_FORMAT.format(
                points=volunteer["points"],
                submissions_count=len(submissions),
                achievements_count=len(achievements),
            )
        )
    except Exception as e:
        logger.error("Error showing stats: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── My Achievements ───────────────

@router.message(F.text == strings.BTN_MY_ACHIEVEMENTS)
async def my_achievements(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer:
            await message.answer(strings.ERROR_NOT_REGISTERED)
            return

        achievements = await get_achievements(volunteer["id"])
        if not achievements:
            await message.answer(strings.ACHIEVEMENTS_EMPTY)
            return

        lines = [strings.ACHIEVEMENTS_HEADER]
        for a in achievements:
            lines.append(strings.ACHIEVEMENTS_ROW.format(title=a["title"], description=a["description"]))
        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error("Error showing achievements: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Back ──────────────────────────

@router.message(F.text == strings.BTN_BACK)
async def go_back(message: Message, state: FSMContext):
    try:
        await state.clear()
        volunteer = await get_volunteer(message.from_user.id)
        if volunteer:
            if volunteer["role"] == "coordinator":
                from bot.handlers.start import show_coordinator_menu
                await show_coordinator_menu(message)
            else:
                await show_volunteer_menu(message, volunteer)
        else:
            await message.answer(strings.ERROR_NOT_REGISTERED)
    except Exception as e:
        logger.error("Error going back: %s", e)
        await message.answer(strings.ERROR_GENERAL)
