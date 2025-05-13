import base64
import aiohttp
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Конфигурация
TELEGRAM_TOKEN = "7862122325:AAHWae2MOU_rZnTOvdpJMduoamgyZgeP0QU"
PLANTID_API_KEY = "n9p0XsKZeMRLIRFNheoVlM28G8xxt65LErsXrQI5Ghym20IecH"
PLANTID_API_URL = "https://api.plant.id/v3/identification"

# Кнопка /start
start_button = ReplyKeyboardMarkup(
    [[KeyboardButton('/start')]],
    resize_keyboard=True,
    one_time_keyboard=False
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь фото растения, и я распишу тебе его натальную карту 🌿",
        reply_markup=start_button
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что получен именно фото
    if not update.message.photo:
        return

    # Загружаем изображение
    photo = await update.message.photo[-1].get_file()
    image_bytes = await photo.download_as_bytearray()

    # Кодируем в Base64 и готовим payload
    img_base64 = base64.b64encode(image_bytes).decode('ascii')
    payload = {"images": [img_base64]}
    headers = {"Api-Key": PLANTID_API_KEY}

    # Отправляем запрос
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            PLANTID_API_URL,
            headers=headers,
            json=payload,
        )
        resp_json = await resp.json()

    # Извлекаем suggestions
    suggestions = (
        resp_json.get('result', {})
                 .get('classification', {})
                 .get('suggestions', [])
    )

    # Если нет распознаваний
    if not suggestions:
        await update.message.reply_text(
            "❌ Растение не распознано.",
            reply_markup=start_button
        )
        return

    # Берём первое предположение
    plant = suggestions[0]
    name_scientific = plant.get('name') or plant.get('plant_name') or 'Неизвестно'

    # Обычные названия
    common_list = plant.get('details', {}).get('common_names')
    name_common = common_list[0] if common_list else 'Неизвестно'

    # Вероятность
    probability = plant.get('probability', 0)

    # URL для деталей
    url = plant.get('details', {}).get('url', '')

    # Описание
    description = (
        plant.get('details', {})
             .get('wiki_description', {})
             .get('value', '')
    )

    # Формируем сообщение
    text = (
        f"🌱 Научное: {name_scientific}\n"
        f"📝 Обычное: {name_common}\n"
        f"🔍 Точность: {probability:.1%}\n"
    )
    if url:
        text += f"🌐 Подробнее: {url}\n"
    if description:
        text += f"\n{description}"

    # Отправляем ответ
    await update.message.reply_text(
        text,
        reply_markup=start_button
    )

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()