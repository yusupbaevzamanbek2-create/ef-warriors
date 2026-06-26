import telebot
from telebot import types
import os
from flask import Flask, request

TOKEN = "8950414020:AAGIA0C4-dhmn0r0mGmmFP_hSQM31RusNn4"
CHANNEL = "@eFWarriors"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

users_lang = {}

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def send_webapp(chat_id, lang):
    messages = {
        "uz": "Xush kelibsiz! eF Warriors ga kiring:",
        "ru": "Dobro pozhalovat! Voydite v eF Warriors:",
        "en": "Welcome! Enter eF Warriors:"
    }
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton(
        "🏆 eF Warriors App",
        web_app=types.WebAppInfo(
            url="https://yusupbaevzamanbek2-create.github.io/ef-warriors/"
        )
    ))
    bot.send_message(chat_id, messages[lang], reply_markup=inline)

def send_subscribe(chat_id, lang):
    messages = {
        "uz": "Botdan foydalanish uchun kanalga obuna boning:",
        "ru": "Podpishites na kanal chtoby polzovatsya botom:",
        "en": "Subscribe to our channel to use the bot:"
    }
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton(
        "📢 Kanalga obuna bolish",
        url="https://t.me/eFWarriors"
    ))
    inline.add(types.InlineKeyboardButton(
        "✅ Tekshirish",
        callback_data="check_sub"
    ))
    bot.send_message(chat_id, messages[lang], reply_markup=inline)

@bot.message_handler(commands=["start"])
def start(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🇺🇿 Ozbekcha", callback_data="uz"),
        types.InlineKeyboardButton("🇷🇺 Russkiy", callback_data="ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="en")
    )
    bot.send_message(
        message.chat.id,
        "Salom! Tilni tanlang / Privet! Vyberi yazyk / Hello! Choose language:",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data in ["uz", "ru", "en"])
def language(call):
    users_lang[call.from_user.id] = call.data
    if check_subscription(call.from_user.id):
        send_webapp(call.message.chat.id, call.data)
    else:
        send_subscribe(call.message.chat.id, call.data)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    lang = users_lang.get(call.from_user.id, "uz")
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "Rahmat!")
        send_webapp(call.message.chat.id, lang)
    else:
        messages = {
            "uz": "Hali obuna bolmadingiz!",
            "ru": "Vy eshyo ne podpisalis!",
            "en": "You are not subscribed yet!"
        }
        bot.answer_callback_query(call.id, messages[lang])

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
