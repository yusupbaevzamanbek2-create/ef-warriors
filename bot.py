import telebot
from telebot import types
import os
from flask import Flask, request

TOKEN = "8950414020:AAGIA0C4-dhmn0r0mGmmFP_hSQM31RusNn4"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

users_lang = {}

texts = {
    "uz": {
        "tournaments": "Turnirlar",
        "results": "Natijalar",
        "profile": "Profil",
        "admin": "Admin",
        "register": "Turnirga yozilish",
        "registered": "Siz turnirga qoshildingiz!",
        "no_results": "Hozircha natijalar yoq."
    },
    "ru": {
        "tournaments": "Turniry",
        "results": "Rezultaty",
        "profile": "Profil",
        "admin": "Admin",
        "register": "Registratsiya",
        "registered": "Vy zaregistrirovany!",
        "no_results": "Rezultatov poka net."
    },
    "en": {
        "tournaments": "Tournaments",
        "results": "Results",
        "profile": "Profile",
        "admin": "Admin",
        "register": "Register",
        "registered": "Registered successfully!",
        "no_results": "No results yet."
    }
}

def menu(chat_id, lang):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(texts[lang]["tournaments"]))
    kb.add(types.KeyboardButton(texts[lang]["results"]))
    kb.add(types.KeyboardButton(texts[lang]["profile"]))
    kb.add(types.KeyboardButton(texts[lang]["register"]))
    kb.add(types.KeyboardButton(texts[lang]["admin"]))
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton(
        "eF Warriors App",
        web_app=types.WebAppInfo(
            url="https://yusupbaevzamanbek2-create.github.io/ef-warriors/"
        )
    ))
    bot.send_message(chat_id, "eF Warriors", reply_markup=kb)
    bot.send_message(chat_id, "Web App:", reply_markup=inline)

@bot.message_handler(commands=["start"])
def start(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Ozbekcha", callback_data="uz"),
        types.InlineKeyboardButton("Russkiy", callback_data="ru"),
        types.InlineKeyboardButton("English", callback_data="en")
    )
    bot.send_message(message.chat.id, "Tilni tanlang", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def language(call):
    users_lang[call.from_user.id] = call.data
    menu(call.message.chat.id, call.data)

@bot.message_handler(func=lambda m: True)
def handler(message):
    lang = users_lang.get(message.from_user.id, "uz")
    if message.text == texts[lang]["register"]:
        bot.send_message(message.chat.id, texts[lang]["registered"])
    elif message.text == texts[lang]["tournaments"]:
        bot.send_message(message.chat.id, "World Cup 2026\n\n0/32")
    elif message.text == texts[lang]["results"]:
        bot.send_message(message.chat.id, texts[lang]["no_results"])
    elif message.text == texts[lang]["profile"]:
        bot.send_message(message.chat.id, f"{message.from_user.first_name}\nID: {message.from_user.id}")
    elif message.text == texts[lang]["admin"]:
        bot.send_message(message.chat.id, "@yusupbaevv")

@app.route("/" + TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "eF Warriors ishlayapti!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://ef-warriors.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
