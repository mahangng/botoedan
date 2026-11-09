#import asyncio
import random
import time
from fast_rub import Client, filters
from fast_rub.types import Update

# ==========================================
# ⚙️ تنظیمات
# ==========================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = "YOUR_RUBIKA_USER_ID"

bot = Client("world_war_bot_session", token=BOT_TOKEN)

# ==========================================
# 🗄️ دیتابیس (FastRub ORM)
# ==========================================
# دیتابیس به صورت خودکار در فایل world_war.db ساخته می‌شود
db = bot.db

class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True)
    country = db.Column(db.String)
    gold = db.Column(db.Integer, default=1000)
    oil = db.Column(db.Integer, default=500)
    soldiers = db.Column(db.Integer, default=100)
    tanks = db.Column(db.Integer, default=0)
    last_attack = db.Column(db.Float, default=0.0)  # timestamp آخرین حمله

# ==========================================
# 🌍 لیست کشورها
# ==========================================
COUNTRIES = {
    "ایران": {"gold": 1200, "oil": 600, "soldiers": 150},
    "روسیه": {"gold": 800, "oil": 1000, "soldiers": 200},
    "آمریکا": {"gold": 1500, "oil": 400, "soldiers": 100},
    "چین": {"gold": 1000, "oil": 800, "soldiers": 180},
}

# ==========================================
# 🛠️ توابع کمکی
# ==========================================
async def get_player(user_id: str):
    return await Player.get(user_id=user_id)

async def create_player(user_id: str, country: str):
    stats = COUNTRIES[country]
    player = Player(
        user_id=user_id,
        country=country,
        gold=stats["gold"],
        oil=stats["oil"],
        soldiers=stats["soldiers"],
    )
    await player.save()
    return player

# ==========================================
# 🎮 دستورات بازی
# ==========================================

@bot.on_message(filters.text("/start"))
async def cmd_start(msg: Update):
    user_id = str(msg.sender_id)
    player = await get_player(user_id)

    if player:
        await msg.reply(
            f"🌍 **بازگشت به میدان جنگ**\n"
            f"🏳️ کشور شما: **{player.country}**\n"
            f"💰 طلا: {player.gold} | 🛢️ نفت: {player.oil}\n"
            f"💂 سرباز: {player.soldiers} | 🚜 تانک: {player.tanks}\n\n"
            f"دستورات:\n"
            f"`/attack` — حمله به کشور تصادفی\n"
            f"`/build` — ساخت تجهیزات\n"
            f"`/stats` — آمار کامل"
        )
        return

    # اگر بازیکن جدید است
    countries_list = "\n".join([f"• `{c}`" for c in COUNTRIES.keys()])
    await msg.reply(
        f"⚔️ **به بازی جنگ جهانی خوش آمدید!**\n\n"
        f"برای شروع، یک کشور انتخاب کنید:\n{countries_list}\n\n"
        f"دستور: `/select <نام کشور>`\n"
        f"مثال: `/select ایران`"
    )

@bot.on_message(filters.text.startswith("/select"))
async def cmd_select(msg: Update):
    user_id = str(msg.sender_id)

    if await get_player(user_id):
        await msg.reply("⚠️ شما قبلاً یک کشور انتخاب کرده‌اید.")
        return

    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply("⚠️ نام کشور را وارد کنید. مثال: `/select ایران`")
        return

    country_name = parts[1].strip()
    if country_name not in COUNTRIES:
        await msg.reply("❌ کشور نامعتبر است. از لیست `/start` انتخاب کنید.")
        return

    await create_player(user_id, country_name)
    await msg.reply(
        f"✅ کشور **{country_name}** با موفقیت انتخاب شد!\n"
        f"💰 طلا: {COUNTRIES[country_name]['gold']}\n"
        f"🛢️ نفت: {COUNTRIES[country_name]['oil']}\n"
        f"💂 سرباز: {COUNTRIES[country_name]['soldiers']}\n\n"
        f"با `/attack` به دشمنان حمله کنید!"
    )

@bot.on_message(filters.text("/stats"))
async def cmd_stats(msg: Update):
    player = await get_player(str(msg.sender_id))
    if not player:
        await msg.reply("⚠️ ابتدا با `/start` ثبت‌نام کنید.")
        return

    # محاسبه قدرت
    power = player.soldiers * 1 + player.tanks * 5

    await msg.reply(
        f"📊 **آمار امپراتوری شما**\n"
        f"🏳️ کشور: {player.country}\n"
        f"💰 طلا: {player.gold}\n"
        f"🛢️ نفت: {player.oil}\n"
        f"💂 سرباز: {player.soldiers}\n"
        f"🚜 تانک: {player.tanks}\n"
        f"⚡ قدرت نظامی: {power}"
    )

@bot.on_message(filters.text("/build"))
async def cmd_build(msg: Update):
    player = await get_player(str(msg.sender_id))
    if not player:
        await msg.reply("⚠️ ابتدا با `/start` ثبت‌نام کنید.")
        return

    # هزینه ساخت
    tank_cost_gold = 200
    tank_cost_oil = 100
    soldier_cost_gold = 50

    if player.gold >= tank_cost_gold and player.oil >= tank_cost_oil:
        player.gold -= tank_cost_gold
        player.oil -= tank_cost_oil
        player.tanks += 1
        await player.save()
        await msg.reply(f"✅ یک تانک ساخته شد! (🚜 {player.tanks})\n💰 طلا: {player.gold} | 🛢️ نفت: {player.oil}")
    elif player.gold >= soldier_cost_gold:
        player.gold -= soldier_cost_gold
        player.soldiers += 10
        await player.save()
        await msg.reply(f"✅ ۱۰ سرباز جدید اضافه شد! (💂 {player.soldiers})\n💰 طلا: {player.gold}")
    else:
        await msg.reply(
            f"❌ منابع کافی نیست.\n"
            f"تانک: {tank_cost_gold} طلا + {tank_cost_oil} نفت\n"
            f"سرباز: {soldier_cost_gold} طلا برای ۱۰ نفر"
        )

@bot.on_message(filters.text("/attack"))
async def cmd_attack(msg: Update):
    user_id = str(msg.sender_id)
    attacker = await get_player(user_id)

    if not attacker:
        await msg.reply("⚠️ ابتدا با `/start` ثبت‌نام کنید.")
        return

    # محدودیت زمانی (هر ۱ دقیقه)
    now = time.time()
    if now - attacker.last_attack < 60:
        remaining = int(60 - (now - attacker.last_attack))
        await msg.reply(f"⏳ تا حمله بعدی **{remaining}** ثانیه صبر کنید.")
        return

    # پیدا کردن یک مدافع تصادفی (غیر از خود بازیکن)
    all_players = await Player.all()
    possible_targets = [p for p in all_players if p.user_id != user_id]

    if not possible_targets:
        await msg.reply("🌍 هنوز بازیکن دیگری در بازی نیست. منتظر بمانید...")
        return

    defender = random.choice(possible_targets)

    # محاسبه قدرت
    attack_power = attacker.soldiers * 1 + attacker.tanks * 5
    defend_power = defender.soldiers * 1 + defender.tanks * 5 + random.randint(0, 50)  # کمی شانس

    result_text = ""

    if attack_power > defend_power:
        # پیروزی مهاجم
        loot_gold = random.randint(50, 200)
        loot_oil = random.randint(20, 100)

        attacker.gold += loot_gold
        attacker.oil += loot_oil
        attacker.soldiers = max(0, attacker.soldiers - random.randint(5, 20))

        defender.gold = max(0, defender.gold - loot_gold)
        defender.oil = max(0, defender.oil - loot_oil)
        defender.soldiers = max(0, defender.soldiers - random.randint(10, 30))

        result_text = (
            f"🏆 **پیروزی!**\n"
            f"شما به **{defender.country}** حمله کردید و پیروز شدید.\n"
            f"💰 غنیمت: {loot_gold} طلا | 🛢️ {loot_oil} نفت\n"
            f"💂 سربازان شما: {attacker.soldiers}"
        )
    else:
        # شکست مهاجم
        attacker.soldiers = max(0, attacker.soldiers - random.randint(20, 40))
        attacker.tanks = max(0, attacker.tanks - random.randint(0, 2))

        result_text = (
            f"💀 **شکست!**\n"
            f"حمله شما به **{defender.country}** دفع شد.\n"
            f"💂 سربازان باقی‌مانده: {attacker.soldiers}\n"
            f"🚜 تانک‌ها: {attacker.tanks}"
        )

    attacker.last_attack = now
    await attacker.save()
    await defender.save()

    await msg.reply(result_text)

# ==========================================
# 🚀 اجرا
# ==========================================
async def main():
    # ساخت جداول دیتابیس در اولین اجرا
    await Player.create_table()
    print("✅ ربات جنگ جهانی آماده است...")
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())