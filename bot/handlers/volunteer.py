import logging
import os
import tempfile

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from bot.config import settings
from bot.database import (
    get_volunteer,
    get_volunteer_by_id,
    get_event_by_qr,
    get_event_by_id,
    mark_qr_used,
    create_submission,
    add_points,
    add_achievement,
    get_achievements,
    get_volunteer_submissions,
    get_leaderboard,
    get_planned_events,
    get_all_volunteers,
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

class SubmissionFlow(StatesGroup):
    waiting_location = State()
    waiting_photos = State()
    waiting_qr = State()

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


@router.message(Command("help"))
@router.message(F.text == strings.BTN_HELP)
async def show_help(message: Message):
    try:
        await message.answer(strings.HELP_TEXT)
    except Exception as e:
        logger.error("Error showing help: %s", e)
        await message.answer(strings.ERROR_GENERAL)


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


@router.message(SubmissionFlow.waiting_photos, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    tmp_path = None
    try:
        data = await state.get_data()
        photo_results = data.get("photo_results", [])
        user_lat = data.get("lat")
        user_lon = data.get("lon")

        photo = message.photo[-1]  # highest resolution
        file_info = await bot.get_file(photo.file_id)

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(tmp_fd)

        await bot.download_file(file_info.file_path, tmp_path)

        exif_data = extract_exif(tmp_path)
        exif_ok = False
        geo_ok = False
        has_face = False

        if exif_data["datetime"] and is_recent(exif_data["datetime"]):
            exif_ok = True
        elif DEMO_MODE:
            logger.warning("DEMO: EXIF missing or not recent, skipping strict check")
            exif_ok = True  # lenient in demo mode

        if exif_data["lat"] and exif_data["lon"] and user_lat and user_lon:
            geo_ok = is_location_match(exif_data["lat"], exif_data["lon"], user_lat, user_lon)
        elif user_lat and user_lon:
            # DEMO: если у фото нет GPS в EXIF, принимаем координаты, отправленные пользователем.
            if DEMO_MODE:
                geo_ok = True
        elif DEMO_MODE:
            geo_ok = True  # no location at all, lenient in demo

        has_face = detect_face(tmp_path)

        photo_results.append({
            "exif_ok": exif_ok,
            "geo_ok": geo_ok,
            "has_face": has_face,
        })
        await state.update_data(photo_results=photo_results)

        num = len(photo_results)

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

    await message.answer(strings.SUB_ASK_QR, reply_markup=skip_keyboard())
    await state.set_state(SubmissionFlow.waiting_qr)

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

    await _check_achievements(message, volunteer_id)

    await state.clear()
    if volunteer:
        await show_volunteer_menu(message, volunteer)


async def _check_achievements(message: Message, volunteer_id: int):
    try:
        existing = await get_achievements(volunteer_id)
        existing_types = {a["badge_type"] for a in existing}

        submissions = await get_volunteer_submissions(volunteer_id)
        volunteer = await get_volunteer_by_id(volunteer_id)

        new_achievements = []

        if len(submissions) >= 1 and "first_report" not in existing_types:
            new_achievements.append(("first_report", strings.ACH_FIRST_REPORT_TITLE, strings.ACH_FIRST_REPORT_DESC))

        if len(submissions) >= 5 and "five_reports" not in existing_types:
            new_achievements.append(("five_reports", strings.ACH_FIVE_REPORTS_TITLE, strings.ACH_FIVE_REPORTS_DESC))

        if len(submissions) >= 10 and "ten_reports" not in existing_types:
            new_achievements.append(("ten_reports", strings.ACH_TEN_REPORTS_TITLE, strings.ACH_TEN_REPORTS_DESC))

        if volunteer:
            if volunteer["points"] >= 100 and "100_points" not in existing_types:
                new_achievements.append(("100_points", strings.ACH_100_POINTS_TITLE, strings.ACH_100_POINTS_DESC))

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

@router.message(F.text == strings.BTN_MY_STATS)
async def my_stats(message: Message):
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

        exif_count = sum(1 for s in submissions if s.get("exif_verified"))
        geo_count = sum(1 for s in submissions if s.get("geo_verified"))
        selfie_count = sum(1 for s in submissions if s.get("selfie_verified"))
        qr_count = sum(1 for s in submissions if s.get("qr_verified"))

        await message.answer(
            strings.MY_STATS_FORMAT.format(
                points=volunteer["points"],
                rank=rank,
                submissions_count=len(submissions),
                achievements_count=len(achievements),
                exif_count=exif_count,
                geo_count=geo_count,
                selfie_count=selfie_count,
                qr_count=qr_count,
            )
        )
    except Exception as e:
        logger.error("Error showing stats: %s", e)
        await message.answer(strings.ERROR_GENERAL)

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
            date_str = a["created_at"][:10] if a.get("created_at") else "—"
            lines.append(strings.ACHIEVEMENTS_ROW.format(
                title=a["title"], description=a["description"], date=date_str
            ))
        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error("Error showing achievements: %s", e)
        await message.answer(strings.ERROR_GENERAL)

@router.message(F.text == strings.BTN_MY_REPORTS)
async def my_reports(message: Message):
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if not volunteer:
            await message.answer(strings.ERROR_NOT_REGISTERED)
            return

        submissions = await get_volunteer_submissions(volunteer["id"])
        if not submissions:
            await message.answer(strings.MY_REPORTS_EMPTY)
            return

        lines = [strings.MY_REPORTS_HEADER]
        for i, sub in enumerate(submissions[:10], 1):
            event_title = "Без QR-кода"
            if sub.get("event_id"):
                event = await get_event_by_id(sub["event_id"])
                if event:
                    event_title = event["title"]

            status_map = {
                "verified": "✅ Подтверждён",
                "pending": "⏳ На проверке",
                "rejected": "❌ Отклонён",
            }
            status_text = status_map.get(sub["status"], sub["status"])

            exif_icon = "✅" if sub["exif_verified"] else "❌"
            geo_icon = "✅" if sub["geo_verified"] else "❌"
            selfie_icon = "✅" if sub["selfie_verified"] else "❌"
            qr_icon = "✅" if sub["qr_verified"] else "❌"

            date_str = sub["created_at"][:10] if sub.get("created_at") else "—"

            lines.append(strings.MY_REPORTS_ROW.format(
                i=i,
                event_title=event_title,
                date=date_str,
                points=sub["points_awarded"],
                status=status_text,
                exif=exif_icon,
                geo=geo_icon,
                selfie=selfie_icon,
                qr=qr_icon,
            ))

        lines.append(strings.MY_REPORTS_TOTAL.format(
            count=len(submissions),
            points=volunteer["points"],
        ))

        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error("Error showing reports: %s", e)
        await message.answer(strings.ERROR_GENERAL)

@router.message(F.text == strings.BTN_VOLUNTEERS)
async def public_volunteer_list(message: Message):
    """Show list of all volunteers — available to everyone."""
    try:
        volunteers = await get_all_volunteers()
        vols = [v for v in volunteers if v["role"] == "volunteer"]
        if not vols:
            await message.answer(strings.VOLUNTEERS_HEADER.format(count=0))
            return

        text = strings.VOLUNTEERS_HEADER.format(count=len(vols)) + "\n\n"

        buttons = []
        for i, v in enumerate(vols, 1):
            text += strings.VOLUNTEERS_ROW.format(
                i=i, name=v["full_name"], points=v["points"]
            ) + "\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{v['full_name']}",
                    callback_data=f"pub_vol:{v['id']}",
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
        await message.answer(text, reply_markup=keyboard)
    except Exception as e:
        logger.error("Error showing public volunteer list: %s", e)
        await message.answer(strings.ERROR_GENERAL)

@router.callback_query(F.data.startswith("pub_vol:"))
async def public_volunteer_detail(callback: CallbackQuery):
    """Show public profile of a volunteer — available to everyone."""
    try:
        await callback.answer()
        vol_id = int(callback.data.split(":")[1])

        vol = await get_volunteer_by_id(vol_id)
        if not vol:
            await callback.message.answer(strings.VOLUNTEER_NOT_FOUND)
            return

        submissions = await get_volunteer_submissions(vol_id)
        achievements = await get_achievements(vol_id)
        leaderboard = await get_leaderboard(100)
        rank = next(
            (i + 1 for i, v in enumerate(leaderboard) if v["id"] == vol_id),
            "—",
        )
        status_text = "Активен" if vol["status"] == "active" else "Неактивен"

        text = strings.VOLUNTEER_PUBLIC_PROFILE.format(
            name=vol["full_name"],
            city=vol["city"] or "—",
            points=vol["points"],
            rank=rank,
            submissions=len(submissions),
            achievements=len(achievements),
            status=status_text,
        )

        if achievements:
            text += "\n\n<b>Достижения:</b>"
            for a in achievements:
                text += f"\n  🏅 {a['title']}"

        await callback.message.answer(text)
    except Exception as e:
        logger.error("Error showing public volunteer detail: %s", e)

@router.message(F.text == strings.BTN_LEADERBOARD)
async def public_leaderboard(message: Message):
    """Show leaderboard — available to everyone."""
    try:
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

        volunteer = await get_volunteer(message.from_user.id)
        if volunteer and volunteer["role"] == "volunteer":
            all_leaders = await get_leaderboard(100)
            my_rank = next(
                (i + 1 for i, v in enumerate(all_leaders) if v["id"] == volunteer["id"]),
                None,
            )
            if my_rank and my_rank > 10:
                lines.append(f"\n---\nВы: <b>{my_rank}</b> место — {volunteer['points']} баллов")

        await message.answer("\n".join(lines))
    except Exception as e:
        logger.error("Error showing public leaderboard: %s", e)
        await message.answer(strings.ERROR_GENERAL)

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
