import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from bot.config import settings
from bot.database import get_volunteer, create_volunteer
from bot import strings

logger = logging.getLogger(__name__)

router = Router(name="start")


# ── FSM States ────────────────────

class Registration(StatesGroup):
    waiting_name = State()
    waiting_city = State()
    waiting_password = State()
    waiting_password_name = State()
    waiting_password_city = State()


# ── Keyboard builders ────────────

def volunteer_menu_keyboard():
    keyboard = [
        [KeyboardButton(text=strings.BTN_SUBMIT_REPORT)],
        [KeyboardButton(text=strings.BTN_MY_PROFILE), KeyboardButton(text=strings.BTN_MY_STATS)],
        [KeyboardButton(text=strings.BTN_MY_REPORTS), KeyboardButton(text=strings.BTN_MY_ACHIEVEMENTS)],
        [KeyboardButton(text=strings.BTN_VOLUNTEERS), KeyboardButton(text=strings.BTN_LEADERBOARD)],
        [KeyboardButton(text=strings.BTN_EVENTS), KeyboardButton(text=strings.BTN_HELP)],
    ]
    # Add webapp button if configured
    if settings.WEBAPP_URL:
        keyboard.insert(-1, [KeyboardButton(
            text=strings.BTN_OPEN_APP,
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def coordinator_menu_keyboard():
    keyboard = [
        [KeyboardButton(text=strings.BTN_TEAM), KeyboardButton(text=strings.BTN_STATS)],
        [KeyboardButton(text=strings.BTN_CALENDAR), KeyboardButton(text=strings.BTN_RATINGS)],
        [KeyboardButton(text=strings.BTN_GENERATE_QR)],
    ]
    if settings.WEBAPP_URL:
        keyboard.append([KeyboardButton(
            text=strings.BTN_DASHBOARD,
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )])
    else:
        keyboard.append([KeyboardButton(text=strings.BTN_DASHBOARD)])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def role_selection_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=strings.BTN_ROLE_VOLUNTEER, callback_data="role_volunteer"),
                InlineKeyboardButton(text=strings.BTN_ROLE_COORDINATOR, callback_data="role_coordinator"),
            ]
        ]
    )


# ── Helpers ───────────────────────

async def show_volunteer_menu(message: Message, volunteer: dict):
    try:
        text = strings.MENU_VOLUNTEER_HEADER
        await message.answer(text, reply_markup=volunteer_menu_keyboard())
    except Exception as e:
        logger.error("Error showing volunteer menu: %s", e)


async def show_coordinator_menu(message: Message):
    try:
        text = strings.MENU_COORDINATOR_HEADER
        await message.answer(text, reply_markup=coordinator_menu_keyboard())
    except Exception as e:
        logger.error("Error showing coordinator menu: %s", e)


# ── /start ────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    try:
        volunteer = await get_volunteer(message.from_user.id)
        if volunteer:
            if volunteer["role"] == "coordinator":
                await show_coordinator_menu(message)
            else:
                await show_volunteer_menu(message, volunteer)
        else:
            await message.answer(
                strings.WELCOME,
                reply_markup=role_selection_keyboard(),
            )
    except Exception as e:
        logger.error("Error in /start: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Role Selection ────────────────

@router.callback_query(F.data == "role_volunteer")
async def role_volunteer_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(strings.REG_ASK_NAME, reply_markup=ReplyKeyboardRemove())
        await state.set_state(Registration.waiting_name)
        await state.update_data(role="volunteer")
    except Exception as e:
        logger.error("Error in role_volunteer callback: %s", e)


@router.callback_query(F.data == "role_coordinator")
async def role_coordinator_cb(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(strings.REG_ASK_PASSWORD, reply_markup=ReplyKeyboardRemove())
        await state.set_state(Registration.waiting_password)
    except Exception as e:
        logger.error("Error in role_coordinator callback: %s", e)


# ── Coordinator Password ──────────

@router.message(Registration.waiting_password)
async def process_password(message: Message, state: FSMContext):
    try:
        if message.text == settings.ADMIN_PASSWORD:
            await state.update_data(role="coordinator")
            await message.answer(strings.REG_ASK_NAME)
            await state.set_state(Registration.waiting_password_name)
        else:
            await message.answer(strings.REG_WRONG_PASSWORD)
    except Exception as e:
        logger.error("Error checking coordinator password: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(Registration.waiting_password_name)
async def process_password_name(message: Message, state: FSMContext):
    try:
        await state.update_data(full_name=message.text.strip())
        await message.answer(strings.REG_ASK_CITY)
        await state.set_state(Registration.waiting_password_city)
    except Exception as e:
        logger.error("Error processing coordinator name: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(Registration.waiting_password_city)
async def process_password_city(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        city = message.text.strip()
        username = message.from_user.username or ""
        full_name = data["full_name"]

        # Check if already exists and update role
        existing = await get_volunteer(message.from_user.id)
        if existing:
            import aiosqlite
            from bot.config import settings as cfg
            async with aiosqlite.connect(cfg.DB_PATH) as db:
                await db.execute(
                    "UPDATE volunteers SET role = 'coordinator', city = ? WHERE telegram_id = ?",
                    (city, message.from_user.id),
                )
                await db.commit()
        else:
            await create_volunteer(
                telegram_id=message.from_user.id,
                username=username,
                full_name=full_name,
                city=city,
                phone="",
                role="coordinator",
            )

        await state.clear()
        await message.answer(strings.REG_SUCCESS_COORDINATOR.format(name=full_name))
        await show_coordinator_menu(message)
    except Exception as e:
        logger.error("Error completing coordinator registration: %s", e)
        await message.answer(strings.ERROR_GENERAL)


# ── Volunteer Registration ────────

@router.message(Registration.waiting_name)
async def process_name(message: Message, state: FSMContext):
    try:
        await state.update_data(full_name=message.text.strip())
        await message.answer(strings.REG_ASK_CITY)
        await state.set_state(Registration.waiting_city)
    except Exception as e:
        logger.error("Error processing name: %s", e)
        await message.answer(strings.ERROR_GENERAL)


@router.message(Registration.waiting_city)
async def process_city(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        city = message.text.strip()
        username = message.from_user.username or ""
        full_name = data["full_name"]

        await create_volunteer(
            telegram_id=message.from_user.id,
            username=username,
            full_name=full_name,
            city=city,
            phone="",
            role="volunteer",
        )

        await state.clear()
        await message.answer(strings.REG_SUCCESS_VOLUNTEER.format(name=full_name))
        volunteer = await get_volunteer(message.from_user.id)
        await show_volunteer_menu(message, volunteer)
    except Exception as e:
        logger.error("Error completing registration: %s", e)
        await message.answer(strings.ERROR_GENERAL)
