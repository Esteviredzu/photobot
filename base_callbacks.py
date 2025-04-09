from io import BytesIO
from PIL import Image
from aiogram import types, F, Bot, Dispatcher
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
)
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types.input_file import BufferedInputFile

from yolo_processor import YOLOProcessor
from ImageController import ImageController
from OutputController import OutputController


async def start_command(message: Message) -> None:
    """Обработчик команды /start."""
    text = "Привет! Я бот! Отправь мне фото, и я обработаю его!"
    await message.answer(text)

async def stop_command(message: Message) -> None:
    return

async def handle_photo(message: Message, state: FSMContext) -> None:
    """Обрабатывает получение фотографии от пользователя."""
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"
    
    await state.update_data(photo=file_url)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В размеченном PDF", callback_data="export_to_pdf")],
        [InlineKeyboardButton(text="Фото с выделенными значками", callback_data="marked_photo")],
        [InlineKeyboardButton(text="Скачать все распознанные значки", callback_data="download_all_icons")]
        [InlineKeyboardButton(text="Выход", callback_data="stop")],
    ])

    await message.reply("Фото получено! Как хотите получить результат?", reply_markup=keyboard)


async def handle_marked_photo(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обрабатывает запрос на получение фото с выделенными объектами."""
    await callback.message.delete()
    await callback.message.answer("Обрабатываю изображение...")

    try:
        data = await state.get_data()
        photo_url = str(data.get("photo"))
        yolo_processor = YOLOProcessor()

        processed_image = yolo_processor.process_image(photo_url)
        coordinates = yolo_processor.get_objects(photo_url)

        if processed_image:
            await callback.message.answer_photo(
                BufferedInputFile(processed_image.getvalue(), filename="processed_image.png")
            )
            
            coordinates_text = "\n".join(
                [f"{x_min}, {y_min}, {x_max}, {y_max}" for x_min, y_min, x_max, y_max in coordinates]
            )
            formatted_coordinates = f"```\n{coordinates_text}\n```"
            await callback.message.answer("Готово! Вот координаты найденных объектов: ")
            await callback.message.answer(formatted_coordinates, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await callback.message.answer("Не удалось обработать изображение.")

    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {e}")
        print(f"Произошла ошибка: {e}")


async def handle_download_all_icons(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обрабатывает запрос на скачивание всех распознанных значков в zip."""
    await callback.message.delete()
    
    try:
        data = await state.get_data()
        photo_url = str(data.get("photo"))
        yolo_processor = YOLOProcessor()

        coordinates = [tuple(sublist) for sublist in yolo_processor.get_objects(photo_url)]
        controller = ImageController(photo_url, coordinates)
        bytes_images = controller.export_bytes_images(False, False)

        pil_images = [Image.open(img_bytes) for img_bytes in bytes_images]
        output_controller = OutputController(pil_images)
        zip_bytes = output_controller.export_zip_bytes()

        await callback.message.answer("Я поработал, сейчас отправлю!")
        await callback.message.answer_document(
            BufferedInputFile(zip_bytes.getvalue(), filename="cropped_icons.zip")
        )
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка: {e}")
        print(f"Произошла ошибка: {e}")


def register_base_callbacks(dp: Dispatcher, bot: Bot) -> None:
    """Регистрирует обработчики команд и событий."""
    dp.message.register(start_command, Command("start"))
    dp.message.register(handle_photo, F.photo)
    db.message.register(stop_command, Command("stop"))
    dp.callback_query.register(handle_marked_photo, F.data == "marked_photo")
    dp.callback_query.register(handle_download_all_icons, F.data == "download_all_icons")
