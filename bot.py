import os
import time
import logging
import requests
import telebot
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

# ---- CONFIG ----
BOT_TOKEN = '8950414020:AAGIA0C4-dhmn0r0mGmmFP_hSQM31RusNn4'
JSONBIN_SECRET = '$2a$10$iuenatd1i8qDLQBJh17cBenJYq4qjFaeWz0E.3mAkvCUf8fw1HYLG'
JSONBIN_BIN_ID = '6a3ed42ada38895dfe0459aa'
CHANNEL = '@eFWarriors'
ROUNDS_PER_DAY = 2
ADMIN = '@yusupbaevvvv'
WEB_APP_URL = 'https://yusupbaevzamanbek2-create.github.io/ef-warriors'

TEAM_NAMES = [
    'Man City', 'Arsenal', 'Liverpool', 'Chelsea', 'Man Utd',
    'Tottenham', 'Newcastle', 'Aston Villa', 'Brighton', 'West Ham',
    'Brentford', 'Fulham', 'Crystal Palace', 'Wolves', 'Everton',
    'Nottm Forest', 'Bournemouth', 'Luton', 'Burnley', 'Sheffield Utd'
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---- JSONBIN ----
def get_data():
    try:
        res = requests.get(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest',
            headers={'X-Master-Key': JSONBIN_SECRET},
            timeout=10
        )
        return res.json().get('record', {})
    except Exception as e:
        log.error(f'get_data xato: {e}')
        return {}

def save_data(data):
    try:
        requests.put(
            f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
            headers={'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_SECRET},
            json=data,
            timeout=10
        )
    except Exception as e:
        log.error(f'save_data xato: {e}')

# ---- TELEGRAM ----
def send_msg(chat_id, text, markup=None):
    try:
        bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)
        time.sleep(0.05)
    except Exception as e:
        log.warning(f'Xabar yuborilmadi {chat_id}: {e}')
        if 'username' in str(e).lower() or 'chat not found' in str(e).lower() or 'user not found' in str(e).lower():
            try:
                bot.send_message(ADMIN, f"⚠️ <b>Xabar yuborilmadi!</b>\n👤 {chat_id}\n❌ Username yo'q yoki bot blokda", parse_mode='HTML')
            except:
                pass

def get_team_name(index):
    try:
        return TEAM_NAMES[int(index)]
    except:
        return f'Jamoa {index}'

# ---- /start HANDLER ----
@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton('🇺🇿 O\'zbekcha', callback_data='lang_uz'),
            telebot.types.InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru')
        )
        bot.send_message(
            message.chat.id,
            "👋 Salom! Tilni tanlang / Выберите язык:",
            reply_markup=markup
        )
    except Exception as e:
        log.error(f'/start xato: {e}')

@bot.callback_query_handler(func=lambda c: c.data in ['lang_uz', 'lang_ru'])
def lang_chosen(call):
    try:
        bot.answer_callback_query(call.id)
        # Kanalga obuna tekshirish
        try:
            member = bot.get_chat_member('@eFWarriors', call.from_user.id)
            is_member = member.status in ['member', 'administrator', 'creator']
        except:
            is_member = False

        if not is_member:
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton('📢 Kanalga o\'tish', url='https://t.me/eFWarriors'))
            markup.add(telebot.types.InlineKeyboardButton('✅ Obuna bo\'ldim', callback_data='check_sub_' + call.data))
            bot.send_message(
                call.message.chat.id,
                "⚠️ Botdan foydalanish uchun avval kanalga obuna bo'ling!\n\n📢 @eFWarriors",
                reply_markup=markup
            )
            return

        send_webapp(call.message.chat.id, call.from_user.first_name)
    except Exception as e:
        log.error(f'lang_chosen xato: {e}')

@bot.callback_query_handler(func=lambda c: c.data.startswith('check_sub_'))
def check_sub(call):
    try:
        bot.answer_callback_query(call.id)
        try:
            member = bot.get_chat_member('@eFWarriors', call.from_user.id)
            is_member = member.status in ['member', 'administrator', 'creator']
        except:
            is_member = False

        if not is_member:
            bot.answer_callback_query(call.id, "❌ Siz hali obuna bo'lmadingiz!", show_alert=True)
            return

        send_webapp(call.message.chat.id, call.from_user.first_name)
    except Exception as e:
        log.error(f'check_sub xato: {e}')

def send_webapp(chat_id, first_name):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        '🏆 eF Warriors',
        web_app=telebot.types.WebAppInfo(url=WEB_APP_URL)
    ))
    bot.send_message(
        chat_id,
        f"👋 Salom, <b>{first_name}</b>!\n\n"
        f"📲 Quyidagi tugmani bosib botga kiring:",
        parse_mode='HTML',
        reply_markup=markup
    )

# ---- CRON: 00:00 ----
def job_midnight():
    log.info('[00:00] Yangi turlar ochilmoqda...')
    try:
        data = get_data()
        if not data.get('drawDone') or not data.get('schedule'):
            log.info('Qura hali tashlanmagan.')
            return

        schedule = data.get('schedule', [])
        all_rounds = sorted(set(m['round'] for m in schedule))
        opened_rounds = data.get('openedRounds', [])
        all_matches = data.get('allMatches', {})
        players = data.get('players', [])

        # 1. Avvalgi turlarni auto 0:0 yopish
        for rnd in opened_rounds:
            for match in [m for m in schedule if m['round'] == rnd]:
                key = f"{min(match['home'], match['away'])}_{max(match['home'], match['away'])}_{match['round']}"
                if key not in all_matches:
                    all_matches[key] = {'confirmed': True, 'homeScore': 0, 'awayScore': 0, 'autoConfirmed': True}
                    log.info(f'Auto 0:0: {key}')
                    home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
                    away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)
                    msg = (
                        f"⏰ <b>{rnd}-tur avtomatik tasdiqlandi!</b>\n\n"
                        f"⚽ {get_team_name(match['home'])} <b>0 : 0</b> {get_team_name(match['away'])}\n\n"
                        f"Natija kiritilmaganligi sababli 0:0 tasdiqlandi."
                    )
                    if home_p and home_p.get('username'):
                        send_msg('@' + home_p['username'].replace('@', ''), msg)
                    if away_p and away_p.get('username'):
                        send_msg('@' + away_p['username'].replace('@', ''), msg)

        data['allMatches'] = all_matches

        # 2. Keyingi 2 tur
        next_rounds = [r for r in all_rounds if r not in opened_rounds][:ROUNDS_PER_DAY]
        if not next_rounds:
            send_msg(CHANNEL, '🏁 <b>APL liga yakunlandi!</b>\n\nBarcha turlar o\'tkazildi!')
            return

        data['openedRounds'] = opened_rounds + next_rounds
        data['currentRounds'] = next_rounds
        save_data(data)

        rounds_text = ' va '.join(str(r) for r in next_rounds)
        send_msg(CHANNEL,
            f"⚽ <b>APL — {rounds_text}-tur boshlandi!</b>\n\n"
            f"📅 Deadline: bugun <b>23:59</b>\n"
            f"📲 Natijani botda kiriting\n\n#eFWarriors #APL"
        )

        for match in [m for m in schedule if m['round'] in next_rounds]:
            home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
            away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)
            home_user = home_p.get('username', '—') if home_p else '—'
            away_user = away_p.get('username', '—') if away_p else '—'
            if home_p and home_p.get('username'):
                send_msg('@' + home_p['username'].replace('@', ''),
                    f"⚽ <b>{match['round']}-tur boshlandi!</b>\n\n"
                    f"🏠 <b>{get_team_name(match['home'])}</b> vs {get_team_name(match['away'])}\n"
                    f"👤 Raqib: {away_user}\n\n"
                    f"⏰ Deadline: <b>23:59</b>\n📲 APL botda natijani kiriting!"
                )
            if away_p and away_p.get('username'):
                send_msg('@' + away_p['username'].replace('@', ''),
                    f"⚽ <b>{match['round']}-tur boshlandi!</b>\n\n"
                    f"{get_team_name(match['home'])} vs <b>{get_team_name(match['away'])}</b>\n"
                    f"👤 Raqib: {home_user}\n\n"
                    f"⏰ Deadline: <b>23:59</b>\n📲 APL botda natijani kiriting!"
                )

        log.info(f'{rounds_text}-turlar ochildi.')
    except Exception as e:
        log.error(f'[00:00] Xato: {e}')

# ---- CRON: 23:30 ----
def job_reminder():
    log.info('[23:30] Deadline eslatmasi...')
    try:
        data = get_data()
        if not data.get('drawDone'):
            return
        current_rounds = data.get('currentRounds', [])
        schedule = data.get('schedule', [])
        all_matches = data.get('allMatches', {})
        players = data.get('players', [])
        for match in [m for m in schedule if m['round'] in current_rounds]:
            key = f"{min(match['home'], match['away'])}_{max(match['home'], match['away'])}_{match['round']}"
            if key in all_matches:
                continue
            home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
            away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)
            reminder = (
                f"⚠️ <b>Deadline yarim soat qoldi!</b>\n\n"
                f"{match['round']}-tur: {get_team_name(match['home'])} vs {get_team_name(match['away'])}\n\n"
                f"Natija kiritilmasa <b>0:0</b> avtomatik tasdiqlanadi!\n"
                f"📲 APL botni oching va natijani kiriting!"
            )
            if home_p and home_p.get('username'):
                send_msg('@' + home_p['username'].replace('@', ''), reminder)
            if away_p and away_p.get('username'):
                send_msg('@' + away_p['username'].replace('@', ''), reminder)
        log.info('[23:30] Eslatmalar yuborildi.')
    except Exception as e:
        log.error(f'[23:30] Xato: {e}')

# ---- FLASK ----
@app.route('/')
def index():
    return 'eF Warriors bot ishlayapti ✅'

@app.route('/open-rounds')
def open_rounds():
    job_midnight()
    return 'Turlar ochildi ✅'

# ---- MAIN ----
if __name__ == '__main__':
    from threading import Thread

    # Bot polling alohida threadda
    def run_bot():
        log.info('Webhook o\'chirilmoqda...')
        try:
            bot.delete_webhook()
            log.info('Webhook o\'chirildi. Polling boshlanyapti...')
        except Exception as e:
            log.error(f'deleteWebhook xato: {e}')
        bot.infinity_polling(timeout=30, long_polling_timeout=20)

    Thread(target=run_bot, daemon=True).start()

    scheduler = BackgroundScheduler(timezone='Asia/Tashkent')
    scheduler.add_job(job_midnight, 'cron', hour=0, minute=0)
    scheduler.add_job(job_reminder, 'cron', hour=23, minute=30)
    scheduler.start()

    log.info('✅ eF Warriors bot ishga tushdi!')
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
        
