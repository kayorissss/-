import json
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# === Настройки ===
BOT_TOKEN = "7690445262:AAHIRQax0ZNI6-lTKAB_8eR8tukfJaoIJdg"
ADMIN_ID = 1253981775
TRIGGER_FILE = "triggers.json"

# === FSM ===
class TriggerState(StatesGroup):
    adding = State()
    deleting = State()

# === Работа с файлами ===
def load_triggers():
    try:
        with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_triggers(data):
    with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === Обновление глобального списка ===
triggers = {}

def update_triggers_from_file():
    global triggers
    triggers = load_triggers()

update_triggers_from_file()

# === Инициализация ===
storage = MemoryStorage()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# === Кнопки ===
def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add")],
        [InlineKeyboardButton(text="➖ Удалить", callback_data="delete")],
        [InlineKeyboardButton(text="📃 Список", callback_data="list")]
    ])

# === /admin ===
@dp.message(Command("admin"))
async def admin_menu(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔧 Меню управления:", reply_markup=admin_keyboard())
    else:
        await message.answer("⛔ Нет доступа.")

# === Ответ на триггеры ===
@dp.message(F.text)
async def respond_to_trigger(message: Message):
    for trigger, answer in triggers.items():
        if trigger.lower() in message.text.lower():
            await message.reply(answer)
            break

# === Кнопки ===
@dp.callback_query()
async def handle_buttons(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа.")
        return

    if call.data == "add":
        await state.set_state(TriggerState.adding)
        await call.message.answer("✏️ Введите триггер и ответ через двоеточие\nПример: `привет:Приветствую!`")

    elif call.data == "delete":
        await state.set_state(TriggerState.deleting)
        await call.message.answer("❌ Введите триггер, который хотите удалить:")

    elif call.data == "list":
        update_triggers_from_file()
        if triggers:
            text = "\n".join([f"🔹 <b>{k}</b> → {v}" for k, v in triggers.items()])
        else:
            text = "❗ Триггеры пока не добавлены."
        await call.message.answer(text)

# === Добавление ===
@dp.message(TriggerState.adding, F.text)
async def handle_add(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if ":" not in message.text:
        await message.reply("⚠️ Неверный формат. Используй `триггер:ответ`.")
        return

    key, value = map(str.strip, message.text.split(":", 1))
    triggers[key.lower()] = value
    save_triggers(triggers)
    update_triggers_from_file()
    await message.reply(f"✅ Добавлено:\n<b>{key}</b> → {value}")
    await state.clear()

# === Удаление ===
@dp.message(TriggerState.deleting, F.text)
async def handle_delete(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    key = message.text.strip().lower()
    if key in triggers:
        del triggers[key]
        save_triggers(triggers)
        update_triggers_from_file()
        await message.reply(f"🗑️ Удалено: <b>{key}</b>")
    else:
        await message.reply("⚠️ Триггер не найден.")
    await state.clear()

# === Запуск ===
async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
