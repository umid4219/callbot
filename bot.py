import os
from threading import Thread
from flask import Flask

app = Flask("")


@app.route("/")
def home():
    return "Bot is running!"


def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


Thread(target=run_web).daemon = True

import openpyxl
import pandas as pd
import telebot
from telebot import types

TOKEN = "8800194423:AAG3Fo11dgB9HCbktMHkg1eLlkLA27oovhk"
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Собрать за весь день")
    btn2 = types.KeyboardButton("Собрать за последний час")
    markup.add(btn1, btn2)
    bot.send_message(
        message.chat.id,
        "Привет! Выберите действие с помощью кнопок ниже:",
        reply_markup=markup,
    )


@bot.message_handler(
    func=lambda message: message.text
    in ["Собрать за весь день", "Собрать за последний час"]
)
def handle_actions(message):
    bot.send_message(
        message.chat.id, "Запрос отправлен всем телефонам... Ждем выгрузку."
    )


if __name__ == "__main__":
    bot.infinity_polling()
