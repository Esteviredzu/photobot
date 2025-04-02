import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from base_callbacks import register_base_callbacks
from pdf_callbacks import register_pdf_callbacks

load_dotenv()
TOKEN: str | None = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("В .env нет токена!")

bot: Bot = Bot(token=TOKEN)
dp: Dispatcher = Dispatcher()

register_base_callbacks(dp, bot)
register_pdf_callbacks(dp, bot)

async def main() -> None:
    """Основная функция для запуска бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Бот запущен!")
    asyncio.run(main())
