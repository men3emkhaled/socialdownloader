import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from downloader import downloader
from database import init_db, get_or_create_user
from dotenv import load_dotenv

# Load env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 أهلاً بيك في بوت التحميل!\n\n"
        "ابعتلي أي لينك فيديو (فيسبوك، تيك توك، إنستجرام، ساوند كلاود) وأنا هبعتهولك فيديو على طول.\n\n"
        "💡 البوت بيدعم معظم المواقع المشهورة."
    )

@dp.message(F.text.startswith("http"))
async def handle_url(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("🔍 جاري فحص اللينك والتحميل... استنى لحظة.")
    
    try:
        # Download the video
        file_path, title = await downloader.download_video(url)
        
        if not os.path.exists(file_path):
            await status_msg.edit_text("❌ للأسف مقدرتش أحمل الفيديو ده. جرب لينك تاني.")
            return

        await status_msg.edit_text(f"📤 جاري رفع الفيديو: {title}...")
        
        # Send to Telegram
        bot_info = await bot.get_me()
        video = FSInputFile(file_path)
        await message.answer_video(
            video=video, 
            caption=f"🎬 {title}\n\nDone by @{bot_info.username}"
        )
        
        # Delete local file to save space
        os.remove(file_path)
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        error_msg = str(e)
        if "File is too large" in error_msg or "max_filesize" in error_msg:
            await status_msg.edit_text("⚠️ الفيديو حجمه كبير جداً (أكبر من 50 ميجا)، التليجرام مش بيسمح برفعه من خلالي.")
        else:
            await status_msg.edit_text("❌ حصلت مشكلة وأنا بحمل الفيديو. اتأكد إن اللينك صح أو جرب فيديو تاني.")
        
        # Cleanup if file was created
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def main():
    # Initialize database
    try:
        if os.getenv("DATABASE_URL"):
            await init_db()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"DB Init Error: {e}")

    logger.info("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
