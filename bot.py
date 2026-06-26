@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Salom!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    inline = types.InlineKeyboardMarkup()
    inline.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="en")
    )
    bot.send_message(
        message.chat.id,
        "Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=inline
    )
