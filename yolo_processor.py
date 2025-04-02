from ultralytics import YOLO
import requests
from io import BytesIO
from PIL import Image
import numpy as np
import cv2


class YOLOProcessor:
    def __init__(self, model_filename: str = "yolo_custom.pt"):
        """
        Загружает модель YOLO.
        :param model_filename: Имя файла модели YOLO.
        """
        self.model = YOLO(model_filename)

    def download_image(self, image_url: str):
        """
        Скачивает изображение по URL и возвращает его в виде объекта BytesIO.
        :param image_url: URL изображения.
        :return: BytesIO объект с изображением или None при ошибке.
        """
        response = requests.get(image_url)
        if response.status_code == 200:
            return BytesIO(response.content)
        return None

    def process_image(self, image_url: str):
        """
        Прогоняет изображение через YOLO и возвращает размеченное изображение в памяти.
        :param image_url: URL изображения.
        :return: BytesIO объект с размеченным изображением или None при ошибке.
        """
        image_bytes = self.download_image(image_url)
        if not image_bytes:
            return None

        image = Image.open(image_bytes)
        results = self.model(image)

        marked_image = results[0].plot()
        marked_image_rgb = cv2.cvtColor(marked_image, cv2.COLOR_BGR2RGB)

        output = BytesIO()
        Image.fromarray(marked_image_rgb).save(output, format="PNG")
        output.seek(0)

        return output

    def get_objects(self, image_url: str):
        """
        Возвращает координаты объектов на изображении (bounding boxes).
        :param image_url: URL изображения.
        :return: Список координат объектов или None при ошибке.
        """
        image_bytes = self.download_image(image_url)
        if not image_bytes:
            return None

        image = Image.open(image_bytes)
        results = self.model(image)

        coordinates = []
        for obj in results[0].boxes:
            coords = obj.xyxy[0].cpu().numpy()
            coordinates.append(coords.tolist())

        return coordinates