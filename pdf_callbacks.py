from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from yolo_processor import YOLOProcessor
from aiogram.types.input_file import BufferedInputFile
from PIL import Image
from ImageController import ImageController
from OutputController import OutputController
from io import BytesIO


class PdfExport(StatesGroup):
    orientation = State()
    grid = State()
    photo = State()


async def handle_export_to_pdf(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PdfExport.orientation)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Альбомная", callback_data="orientation_landscape")],
        [InlineKeyboardButton(text="Портретная", callback_data="orientation_portrait")]
    ])
    await callback.message.delete()
    await callback.message.answer("Выберите ориентацию для PDF:", reply_markup=keyboard)
    await callback.answer()


async def handle_orientation(callback: types.CallbackQuery, state: FSMContext):
    if await state.get_state() != PdfExport.orientation.state:
        return

    orientation = "landscape" if callback.data == "orientation_landscape" else "portrait"
    await state.update_data(orientation=orientation)
    await callback.message.delete()
    await state.set_state(PdfExport.grid)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сетка 10x3", callback_data="grid_10x3")],
        [InlineKeyboardButton(text="Сетка 8x3", callback_data="grid_8x3")],
        [InlineKeyboardButton(text="Сетка 5x2", callback_data="grid_5x2")],
    ]) if orientation == 'landscape' else InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сетка 3x5", callback_data="grid_3x5")],
        [InlineKeyboardButton(text="Сетка 5x9", callback_data="grid_5x9")],
        [InlineKeyboardButton(text="Сетка 10x15", callback_data="grid_10x15")],
    ])

    await callback.message.answer(f"Вы выбрали {orientation}. Теперь выберите сетку:", reply_markup=keyboard)
    await callback.answer()


async def send_final_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    orientation = data.get('orientation')
    grid = data.get('grid')
    rows, cols = map(int, grid.split('x'))
    await message.answer(f"Ваши параметры:\n\nОриентация: {orientation}\nСетка: {grid}")
    
    try:
        photo_url = str(data.get("photo"))
        yolo_processor = YOLOProcessor()
        coordinates = [tuple(sublist) for sublist in yolo_processor.get_objects(photo_url)]
        
        controller = ImageController(photo_url, coordinates)
        bytes_images = controller.export_bytes_images(False, False)
        pil_images = [Image.open(img_bytes) for img_bytes in bytes_images]
        
        output_controller = OutputController(pil_images)
        pdf_bytes = output_controller.export_pdf_bytes(rows=rows, cols=cols)
        
        await message.answer_document(BufferedInputFile(pdf_bytes.getvalue(), filename="icons.pdf"))
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")


async def handle_grid(callback: types.CallbackQuery, state: FSMContext):
    if await state.get_state() != PdfExport.grid.state:
        return
    
    grid_size = callback.data.split("_")[1]
    await state.update_data(grid=grid_size)
    await callback.message.delete()
    await send_final_message(callback.message, state)
    await callback.answer()


async def handle_custom_grid_input(message: types.Message, state: FSMContext):
    if await state.get_state() != PdfExport.grid.state:
        return
    
    grid_size = message.text.strip()
    if not grid_size.count('x') == 1 or not all(i.isdigit() for i in grid_size.split('x')):
        await message.answer("Некорректный формат. Введите два числа через 'x', например, 4x3.")
        return
    
    await state.update_data(grid=grid_size)
    await message.delete()
    await send_final_message(message, state)


def register_pdf_callbacks(dp, bot):
    dp.callback_query.register(handle_export_to_pdf, lambda c: c.data == "export_to_pdf")
    dp.callback_query.register(handle_orientation, lambda c: c.data.startswith("orientation"))
    dp.callback_query.register(handle_grid, lambda c: c.data.startswith("grid"))
    dp.message.register(handle_custom_grid_input, lambda message: message.text and "x" in message.text)
