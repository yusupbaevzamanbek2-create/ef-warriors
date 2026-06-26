@bot.message_handler(commands=["start"])
def start(message):
    kb = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, ".", reply_markup=kb)
    
    inline = types.InlineKeyboardMarkup()
    inline.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="en")
    )
    bot.send_message(
        message.chat.id,
        "Выберите язык / Tilni tanlang / Choose language:",
        reply_markup=inline
    )
