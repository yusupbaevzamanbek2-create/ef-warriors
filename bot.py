import os
import asyncio
import logging
import requests
import telebot
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread

# ---- CONFIG ----
BOT_TOKEN = '8950414020:AAGIA0C4-dhmn0r0mGmmFP_hSQM31RusNn4'
JSONBIN_SECRET = '$2a$10$iuenatd1i8qDLQBJh17cBenJYq4qjFaeWz0E.3mAkvCUf8fw1HYLG'
JSONBIN_BIN_ID = '6a3ed42ada38895dfe0459aa'
CHANNEL = '@eFWarriors'
ROUNDS_PER_DAY = 2

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
    res = requests.get(
        f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest',
        headers={'X-Master-Key': JSONBIN_SECRET}
    )
    return res.json().get('record', {})

def save_data(data):
    requests.put(
        f'https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}',
        headers={'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_SECRET},
        json=data
    )

# ---- TELEGRAM ----
def send_msg(chat_id, text):
    try:
        bot.send_message(chat_id, text, parse_mode='HTML')
        import time; time.sleep(0.05)
    except Exception as e:
        log.warning(f'Xabar yuborilmadi {chat_id}: {e}')

def get_team_name(index):
    try:
        return TEAM_NAMES[int(index)]
    except:
        return f'Jamoa {index}'

# ---- CRON: 00:00 — YANGI 2 TUR OCHISH ----
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

        # 1. Avvalgi ochiq turlarni auto 0:0 tasdiqlash
        for rnd in opened_rounds:
            for match in [m for m in schedule if m['round'] == rnd]:
                key = f"{min(match['home'], match['away'])}_{max(match['home'], match['away'])}_{match['round']}"
                if key not in all_matches:
                    all_matches[key] = {'confirmed': True, 'homeScore': 0, 'awayScore': 0, 'autoConfirmed': True}
                    log.info(f'Auto 0:0: {key}')
                    home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
                    away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)
                    msg = (
                        f"⏰ <b>{rnd}-tur natijasi avtomatik tasdiqlandi!</b>\n\n"
                        f"⚽ {get_team_name(match['home'])} <b>0 : 0</b> {get_team_name(match['away'])}\n\n"
                        f"Natija kiritilmaganligi sababli 0:0 tasdiqlandi."
                    )
                    if home_p and home_p.get('username'):
                        send_msg('@' + home_p['username'].replace('@', ''), msg)
                    if away_p and away_p.get('username'):
                        send_msg('@' + away_p['username'].replace('@', ''), msg)

        data['allMatches'] = all_matches

        # 2. Yangi 2 tur ochish
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

        # Har bir o'yinchiga xabar
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
                    f"🏠 {get_team_name(match['home'])} vs <b>{get_team_name(match['away'])}</b>\n"
                    f"👤 Raqib: {home_user}\n\n"
                    f"⏰ Deadline: <b>23:59</b>\n📲 APL botda natijani kiriting!"
                )

        log.info(f'[00:00] {rounds_text}-turlar ochildi.')
    except Exception as e:
        log.error(f'[00:00] Xato: {e}')

# ---- CRON: 23:30 — DEADLINE ESLATMASI ----
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

# ---- FLASK (Render uchun) ----
@app.route('/')
def index():
    return 'eF Warriors bot ishlayapti ✅'

# ---- MAIN ----
if __name__ == '__main__':
    scheduler = BackgroundScheduler(timezone='Asia/Tashkent')
    scheduler.add_job(job_midnight, 'cron', hour=0, minute=0)
    scheduler.add_job(job_reminder, 'cron', hour=23, minute=30)
    scheduler.start()
    log.info('✅ eF Warriors bot ishga tushdi!')
    log.info('⏰ 00:00 — turlar | 23:30 — eslatma')
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    
