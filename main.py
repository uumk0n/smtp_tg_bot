import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.token import TokenValidationError
from aiogram import F
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv
import asyncio
import os

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_LOGIN = os.getenv("SMTP_LOGIN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Регулярное выражение для проверки корректности email
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# Состояния для хранения данных
user_data = {}


@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user_id = message.from_user.id
    user_data[user_id] = {"email": None, "message": None}
    await message.answer("Привет! Пожалуйста, отправьте свой email для продолжения.")


@dp.message(F.text)
async def collect_email(message: Message, state: FSMContext):
    """Получение и проверка email"""
    user_id = message.from_user.id

    if user_data.get(user_id, {}).get("email") is None:
        email = message.text.strip()

        if not re.match(EMAIL_REGEX, email):
            await message.reply("Похоже, вы ввели некорректный email. Попробуйте снова.")
            return

        user_data[user_id]["email"] = email
        await message.reply("Email принят. Теперь отправьте текст сообщения, который вы хотите отправить.")
        return

    # Получение текста сообщения
    user_message = message.text.strip()
    user_data[user_id]["message"] = user_message
    await message.reply("Сообщение принято. Попытка отправки письма...")

    # Попробуем отправить письмо
    email = user_data[user_id]["email"]
    try:
        send_email(email, "Уведомление от Telegram-бота", user_message)
        await message.reply("Письмо успешно отправлено!")
    except Exception as e:
        await message.reply(f"Ошибка при отправке письма: {str(e)}")


def send_email(to_email, subject, body):
    """Отправка письма через SMTP Яндекса"""
    msg = MIMEMultipart()
    msg["From"] = SMTP_LOGIN
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_LOGIN, SMTP_PASSWORD)
        server.sendmail(SMTP_LOGIN, to_email, msg.as_string())


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
