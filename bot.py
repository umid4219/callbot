import os
import glob
import telebot
from telebot import types
import pandas as pd

# Твой токен от @BotFather
TOKEN = "8800194423:AAG3Fo11dgB9HCbktMHkg1eLlkLA27oovhk"

bot = telebot.TeleBot(TOKEN)

# Создаем папки для хранения файлов, если их нет
UPLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_day = types.KeyboardButton("📊 Собрать за весь день (Сводный)")
    btn_hour = types.KeyboardButton("⏱ Собрать за последний час")
    btn_merge = types.KeyboardButton("📁 Объединить все присланные файлы в один")
    markup.add(btn_day, btn_hour, btn_merge)
    
    bot.send_message(
        message.chat.id, 
        "🤖 Бот-сборщик звонков запущен.\nВыберите действие:", 
        reply_markup=markup
    )

# Обработка текстовых кнопок
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if message.text == "📊 Собрать за весь день (Сводный)":
        bot.send_message(message.chat.id, "⏳ Запрос отправлен всем телефонам... Ждем выгрузку.")
        
    elif message.text == "⏱ Собрать за последний час":
        bot.send_message(message.chat.id, "⏳ Запрос за последний час отправлен...")
        
    elif message.text == "📁 Объединить все присланные файлы в один":
        # Ищем все Excel файлы в папке downloads
        all_files = glob.glob(os.path.join(UPLOAD_FOLDER, "*.xlsx"))
        
        if not all_files:
            bot.send_message(message.chat.id, "⚠️ Пока нет ни одного файла от телефонов! Сотрудники еще ничего не прислали.")
            return

        bot.send_message(message.chat.id, f"🔄 Найдено файлов: {len(ces := all_files)}. Объединяю в общую таблицу...")

        try:
            combined_data = []
            for file in all_files:
                # Читаем каждый Excel файл
                df = pd.read_excel(file)
                # Добавляем колонку с именем файла (чтобы знать, чей это телефон/сотрудник)
                file_name = os.path.basename(file)
                df.insert(0, "Сотрудник / Устройство", file_name.replace(".xlsx", ""))
                combined_data.append(df)

            # Собираем всё в одну таблицу
            final_df = pd.concat(combined_data, ignore_index=True)
            
            # Сохраняем итоговый файл
            output_path = "Сводный_отчет_по_звонкам.xlsx"
            final_df.to_excel(output_path, index=False)

            # Отправляем готовый сводный файл руководителю
            with open(output_path, "rb") as doc:
                bot.send_document(message.chat.id, doc, caption="✅ Вот единый сводный отчет со всех телефонов!")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при объединении файлов: {e}")

# Автоматический перехват Excel-файлов, которые присылают телефоны
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохраняем файл в папку downloads с именем, которое прислал телефон
    file_name = message.document.file_name
    if not file_name.endswith(".xlsx"):
        bot.reply_to(message, "⚠️ Пожалуйста, отправляйте файлы в формате .xlsx")
        return

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    with open(file_path, "wb") as new_file:
        new_file.write(downloaded_file)

    bot.reply_to(message, f"📥 Файл отчета «{file_name}» успешно получен и сохранен в базу!")

if __name__ == "__main__":
    print("Бот успешно запущен и готов принимать файлы от телефонов...")
    bot.infinity_polling()