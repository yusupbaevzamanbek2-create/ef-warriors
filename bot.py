import asyncio
import logging
import requests
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.error import TelegramError
from aiohttp import web

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
bot = Bot(token=BOT_TOKEN)

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
async def send_msg(chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        await asyncio.sleep(0.05)
    except TelegramError as e:
        log.warning(f'Xabar yuborilmadi {chat_id}: {e}')

async def notify_players(data, text):
    for player in data.get('players', []):
        username = player.get('username', '').replace('@', '')
        if username:
            await send_msg('@' + username, text)

def get_team_name(index):
    try:
        return TEAM_NAMES[int(index)]
    except:
        return f'Jamoa {index}'

# ---- CRON: 00:00 — YANGI 2 TUR OCHISH ----
async def job_midnight():
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
            round_matches = [m for m in schedule if m['round'] == rnd]
            for match in round_matches:
                key = f"{min(match['home'], match['away'])}_{max(match['home'], match['away'])}_{match['round']}"
                if key not in all_matches:
                    all_matches[key] = {
                        'confirmed': True,
                        'homeScore': 0,
                        'awayScore': 0,
                        'autoConfirmed': True
                    }
                    log.info(f'Auto 0:0 tasdiqlandi: {key}')

                    # Ikki o'yinchiga ham xabar
                    home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
                    away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)
                    auto_msg = (
                        f"⏰ <b>{rnd}-tur natijasi avtomatik tasdiqlandi!</b>\n\n"
                        f"⚽ {get_team_name(match['home'])} <b>0 : 0</b> {get_team_name(match['away'])}\n\n"
                        f"Natija kiritilmaganligi sababli 0:0 hisobida tasdiqlandi."
                    )
                    if home_p and home_p.get('username'):
                        await send_msg('@' + home_p['username'].replace('@', ''), auto_msg)
                    if away_p and away_p.get('username'):
                        await send_msg('@' + away_p['username'].replace('@', ''), auto_msg)

        data['allMatches'] = all_matches

        # 2. Yangi 2 tur ochish
        next_rounds = [r for r in all_rounds if r not in opened_rounds][:ROUNDS_PER_DAY]

        if not next_rounds:
            log.info('Barcha turlar yakunlandi!')
            await send_msg(CHANNEL, '🏁 <b>APL liga yakunlandi!</b>\n\nBarcha turlar o\'tkazildi. Reyting jadvalini tekshiring!')
            return

        data['openedRounds'] = opened_rounds + next_rounds
        data['currentRounds'] = next_rounds
        save_data(data)

        rounds_text = ' va '.join(str(r) for r in next_rounds)

        # Kanalga xabar
        await send_msg(CHANNEL,
            f"⚽ <b>APL — {rounds_text}-tur boshlandi!</b>\n\n"
            f"📅 Deadline: bugun <b>23:59</b>\n"
            f"📲 Natijani botda kiriting\n\n"
            f"#eFWarriors #APL"
        )

        # Har bir o'yinchiga shaxsiy xabar
        for match in [m for m in schedule if m['round'] in next_rounds]:
            home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
            away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)

            home_name = get_team_name(match['home'])
            away_name = get_team_name(match['away'])
            home_user = home_p['username'] if home_p else '—'
            away_user = away_p['username'] if away_p else '—'

            if home_p and home_p.get('username'):
                await send_msg('@' + home_p['username'].replace('@', ''),
                    f"⚽ <b>{match['round']}-tur o'yiningiz boshlandi!</b>\n\n"
                    f"🏠 <b>{home_name}</b> (Siz) vs {away_name}\n"
                    f"👤 Raqib: {away_user}\n\n"
                    f"⏰ Deadline: <b>23:59</b>\n"
                    f"📲 APL botda natijani kiriting!"
                )

            if away_p and away_p.get('username'):
                await send_msg('@' + away_p['username'].replace('@', ''),
                    f"⚽ <b>{match['round']}-tur o'yiningiz boshlandi!</b>\n\n"
                    f"🏠 {home_name} vs <b>{away_name}</b> (Siz)\n"
                    f"👤 Raqib: {home_user}\n\n"
                    f"⏰ Deadline: <b>23:59</b>\n"
                    f"📲 APL botda natijani kiriting!"
                )

        log.info(f'[00:00] {rounds_text}-turlar ochildi.')

    except Exception as e:
        log.error(f'[00:00] Xato: {e}')

# ---- CRON: 23:30 — DEADLINE ESLATMASI ----
async def job_reminder():
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
                continue  # allaqachon kiritilgan

            home_p = next((p for p in players if p.get('teamIndex') == match['home']), None)
            away_p = next((p for p in players if p.get('teamIndex') == match['away']), None)

            reminder = (
                f"⚠️ <b>Deadline yarim soat qoldi!</b>\n\n"
                f"{match['round']}-tur: {get_team_name(match['home'])} vs {get_team_name(match['away'])}\n\n"
                f"Natija kiritilmasa <b>0:0</b> avtomatik tasdiqlanadi!\n"
                f"📲 APL botni oching va natijani kiriting!"
            )

            if home_p and home_p.get('username'):
                await send_msg('@' + home_p['username'].replace('@', ''), reminder)
            if away_p and away_p.get('username'):
                await send_msg('@' + away_p['username'].replace('@', ''), reminder)

        log.info('[23:30] Eslatmalar yuborildi.')
    except Exception as e:
        log.error(f'[23:30] Xato: {e}')

# ---- HTTP SERVER (Render uchun) ----
async def handle(request):
    return web.Response(text='eF Warriors bot ishlayapti ✅')

async def run_web():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    import os
    port = int(os.environ.get('PORT', 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    log.info(f'HTTP server port {port} da ishga tushdi')

# ---- MAIN ----
async def main():
    log.info('✅ eF Warriors bot ishga tushdi!')

    scheduler = AsyncIOScheduler(timezone='Asia/Tashkent')
    scheduler.add_job(job_midnight, 'cron', hour=0, minute=0)
    scheduler.add_job(job_reminder, 'cron', hour=23, minute=30)
    scheduler.start()

    log.info('⏰ Cron: 00:00 — turlar ochiladi | 23:30 — eslatma')

    await run_web()

    # Abadiy ishlaydi
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
                               
