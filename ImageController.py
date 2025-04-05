import os
from io import BytesIO
from typing import List, Tuple

import cv2
import numpy as np
import requests
from PIL import Image
from skimage.measure import label, regionprops
import rembg


def read_coordinates(file_path: str, image_width: int, image_height: int) -> List[Tuple[int, int, int, int]]:
    """
    Читает нормализованные координаты из файла и конвертирует их в пиксельные значения.
    """
    coordinates = []
    with open(file_path, "r") as file:
        for line in file:
            values = list(map(float, line.strip().split()))
            if len(values) == 5:
                _, x_center, y_center, width, height = values
                left = int((x_center - width / 2) * image_width)
                top = int((y_center - height / 2) * image_height)
                right = int((x_center + width / 2) * image_width)
                bottom = int((y_center + height / 2) * image_height)
                coordinates.append((left, top, right, bottom))
    return coordinates


def remove_background(image: Image.Image) -> Image.Image:
    """
    Удаляет фон с изображения, сохраняя прозрачность.
    """
    input_data = np.array(image)
    output_data = rembg.remove(input_data)
    return Image.fromarray(output_data)


def align_symbol(image):
    """
    Выравнивает значок по вертикали и обрезает по его границам.
    Использует удаление фона только для оценки формы.
    """
    # Получаем изображение с удалённым фоном для анализа
    img_no_bg = remove_background(image)
    img_no_bg_array = np.array(img_no_bg.convert("RGBA"))

    original_array = np.array(image.convert("RGBA"))

    min_area = float('inf')
    best_angle = 0

    def get_mask(img_arr):
        gray = cv2.cvtColor(img_arr, cv2.COLOR_RGBA2GRAY)
        _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        return thresh

    # Ищем лучший угол вращения
    for angle in range(-45, 46, 1):
        rotated_mask_img = Image.fromarray(img_no_bg_array).rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
        rotated_mask_array = np.array(rotated_mask_img)

        mask = get_mask(rotated_mask_array)
        labeled = label(mask)
        regions = regionprops(labeled)

        if not regions:
            continue

        region = max(regions, key=lambda r: r.area)
        minr, minc, maxr, maxc = region.bbox
        area = (maxr - minr) * (maxc - minc)

        if area < min_area:
            min_area = area
            best_angle = angle

    # Поворачиваем оригинальное изображение
    rotated_img = Image.fromarray(original_array).rotate(best_angle, expand=True, fillcolor=(0, 0, 0, 0))
    rotated_arr = np.array(rotated_img)

    # Также поворачиваем маску, чтобы определить границы значка
    rotated_mask_img = Image.fromarray(img_no_bg_array).rotate(best_angle, expand=True, fillcolor=(0, 0, 0, 0))
    rotated_mask_arr = np.array(rotated_mask_img)
    mask = get_mask(rotated_mask_arr)

    labeled = label(mask)
    regions = regionprops(labeled)

    if not regions:
        return rotated_img  # fallback

    region = max(regions, key=lambda r: r.area)
    minr, minc, maxr, maxc = region.bbox

    # Обрезаем повернутое изображение по найденным границам
    cropped = rotated_arr[minr:maxr, minc:maxc]

    return Image.fromarray(cropped)


class ImageController:
    """
    Контроллер обработки изображений.
    """
    def __init__(self, url: str, coordinates: List[Tuple[int, int, int, int]]):
        response = requests.get(url)
        response.raise_for_status()
        
        self.image = Image.open(BytesIO(response.content)).convert("RGBA")
        self.width, self.height = self.image.size
        self.coordinates = coordinates

    def crop_images(self, remove_bg: bool = False, align: bool = False) -> List[Image.Image]:
        """
        Обрезает изображение по координатам и применяет доп. обработку.
        """
        cropped_images = [self.image.crop(coords) for coords in self.coordinates]

        if remove_bg:
            cropped_images = [remove_background(img) for img in cropped_images]
        if align:
            cropped_images = [align_symbol(img) for img in cropped_images]

        return cropped_images

    def save_cropped_images(self, output_folder: str, remove_bg: bool = False, align: bool = False) -> None:
        """
        Сохраняет обрезанные изображения в папку.
        """
        os.makedirs(output_folder, exist_ok=True)
        for i, cropped_img in enumerate(self.crop_images(remove_bg, align)):
            output_path = os.path.join(output_folder, f"cropped_{i}.png")
            cropped_img.save(output_path, format="PNG")

    def export_bytes_images(self, remove_bg: bool = False, align: bool = False) -> List[BytesIO]:
        """
        Экспортирует обработанные изображения в виде списка байтовых объектов.
        """
        images_bytes = []
        for cropped_img in self.crop_images(remove_bg, align):
            img_io = BytesIO()
            cropped_img.save(img_io, format="PNG")
            img_io.seek(0)
            images_bytes.append(img_io)
        return images_bytes
