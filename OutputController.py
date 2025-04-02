import os
import zipfile
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance
from fpdf import FPDF


class OutputController:
    def __init__(self, images: list[Image.Image]):
        """
        :param images: Список изображений (PIL Image)
        """
        self.images = images

    def apply_filters(self, filter_type: str):
        """
        Применяет фильтр ко всем изображениям.
        :param filter_type: Тип фильтра (grayscale, invert, contrast, threshold)
        """
        filters = {
            "grayscale": lambda img: ImageOps.grayscale(img),
            "invert": lambda img: ImageOps.invert(img.convert("RGB")),
            "contrast": lambda img: ImageEnhance.Contrast(img).enhance(2.0),
            "threshold": lambda img: img.convert("L").point(lambda p: 255 if p > 128 else 0, "1")
        }
        
        if filter_type in filters:
            self.images = [filters[filter_type](img) for img in self.images]
    
    def export_pdf_bytes(self, rows: int = 4, cols: int = 3, margin: int = 10) -> BytesIO:
        """
        Экспортирует изображения в PDF в памяти (BytesIO), вписывая их в сетку.
        """
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        page_width, page_height = 210, 297  # Размеры A4 в мм
        available_width = page_width - (cols + 1) * margin
        available_height = page_height - (rows + 1) * margin

        cell_width = available_width / cols
        cell_height = available_height / rows

        for i, img in enumerate(self.images):
            if i % (rows * cols) == 0 and i > 0:
                pdf.add_page()

            col = i % cols
            row = (i // cols) % rows

            img_width, img_height = img.size
            img_aspect = img_width / img_height
            cell_aspect = cell_width / cell_height

            if img_aspect > cell_aspect:
                new_width = cell_width
                new_height = cell_width / img_aspect
            else:
                new_height = cell_height
                new_width = cell_height * img_aspect

            temp_io = BytesIO()
            img.resize((int(new_width * 3.78), int(new_height * 3.78)), Image.LANCZOS).save(temp_io, format="PNG")
            temp_io.seek(0)

            x = margin + col * (cell_width + margin) + (cell_width - new_width) / 2
            y = margin + row * (cell_height + margin) + (cell_height - new_height) / 2
            pdf.image(temp_io, x, y, new_width, new_height)

        pdf_output = BytesIO()
        pdf.output(pdf_output, 'F')
        pdf_output.seek(0)
        return pdf_output

    def save_pdf(self, output_path: str = "output.pdf", rows: int = 4, cols: int = 3, margin: int = 10):
        """
        Сохраняет PDF с изображениями в сетке.
        """
        with open(output_path, "wb") as f:
            f.write(self.export_pdf_bytes(rows, cols, margin).getvalue())

    def export_zip_bytes(self) -> BytesIO:
        """
        Экспортирует изображения в ZIP-архив в памяти (BytesIO).
        """
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, img in enumerate(self.images):
                img_bytes = BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                zip_file.writestr(f"image_{i}.png", img_bytes.getvalue())
        
        zip_buffer.seek(0)
        return zip_buffer

    def save_zip(self, output_path: str = "output.zip"):
        """
        Сохраняет ZIP-архив с изображениями на диск.
        """
        with open(output_path, "wb") as f:
            f.write(self.export_zip_bytes().getvalue())
