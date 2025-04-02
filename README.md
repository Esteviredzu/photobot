# photobot
# YOLO Image Processor Bot

Этот Telegram-бот использует модель YOLO для распознавания объектов на изображениях и экспорта их в PDF.

## Установка и запуск

### Требования
- Python 3.8+
- `pip`
- `git`

### Установка на Linux
```bash
# Клонируем репозиторий
git clone https://github.com/Esteviredzu/photobot.git
cd photobot

# Устанавливаем зависимости
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создаём .env файл
cp .env.example .env

# Запускаем бота
python bot.py
```

### Установка на Windows
```powershell
# Клонируем репозиторий
git clone https://github.com/Esteviredzu/photobot.git
cd photobot

# Устанавливаем зависимости
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Создаём .env файл
copy .env.example .env

# Запускаем бота
python bot.py
```

## Конфигурация `.env`
Создайте файл `.env` в корне проекта и укажите в нём:
```ini
BOT_TOKEN=your_telegram_bot_token

```


## Использование
Бот принимает изображение, обрабатывает его с помощью YOLO, а затем позволяет выбрать ориентацию и сетку для экспорта распознанных объектов в PDF.


