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
    
    welcome_text = (
        f"👋 **أهلاً بك يا {message.from_user.first_name}!**\n\n"
        "أنا بوت تحميل الميديا الشامل. أستطيع التحميل من أغلب منصات التواصل الاجتماعي بأعلى جودة ممكنة.\n\n"
        "**📌 المنصات المدعومة:**\n"
        "• Facebook 🔵 | TikTok ⚫ | Instagram 📱\n"
        "• YouTube 🔴 | Twitter (X) 🐦 | Pinterest 📌\n"
        "• SoundCloud 🎵 | Threads 🧵 | والمزيد...\n\n"
        "**📝 كيف تستخدم البوت؟**\n"
        "1️⃣ أرسل رابط الفيديو أو المقطع الصوتي.\n"
        "2️⃣ اختر الجودة المطلوبة (فيديو عالي، منخفض، أو صوت).\n"
        "3️⃣ انتظر ثواني وسأرسل لك الملف مباشرة!\n\n"
        "⚠️ **ملاحظة:** الحد الأقصى للملفات هو 50 ميجابايت (قيود تليجرام)."
    )
    
    await message.answer(welcome_text, parse_mode="Markdown")

from aiogram.utils.keyboard import InlineKeyboardBuilder

# Global URL cache (simple way for now)
url_cache = {}

@dp.message(F.text.startswith("http"))
async def handle_url(message: types.Message):
    url = message.text.strip()
    
    try:
        # Extract info first
        info = await downloader.get_info(url)
        title = info.get('title', 'Video')
        
        # Store URL in cache
        cache_key = str(message.from_user.id)
        url_cache[cache_key] = url
        
        # Create buttons
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="جودة عالية 🎬", callback_data="dl_video_high"),
            types.InlineKeyboardButton(text="جودة منخفضة 📱", callback_data="dl_video_low")
        )
        builder.row(
            types.InlineKeyboardButton(text="صوت فقط 🎵", callback_data="dl_audio")
        )
        
        await message.answer(
            f"🎬 **{title}**\n\nاختار عايز تحمله بأي جودة؟",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Error extracting info: {e}")
        await message.answer("❌ مقدرتش أتعرف على اللينك ده. اتأكد إنه صح.")

@dp.callback_query(F.data.startswith("dl_"))
async def process_download(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    url = url_cache.get(user_id)
    
    if not url:
        await callback.answer("❌ اللينك انتهى مدته، ابعته تاني.", show_alert=True)
        return

    mode = callback.data.replace("dl_", "")
    action = "الملف"
    if mode == "audio": action = "الصوت"
    elif "video" in mode: action = "الفيديو"
    
    await callback.message.edit_text(f"⏳ جاري تجهيز {action}... استنى لحظة.")
    
    try:
        file_path, title = await downloader.download_video(url, mode=mode)
        
        if not os.path.exists(file_path):
            await callback.message.edit_text("❌ حصلت مشكلة في التحميل.")
            return

        await callback.message.edit_text(f"📤 جاري رفع {action}...")
        
        bot_info = await bot.get_me()
        
        if mode == "audio":
            audio = FSInputFile(file_path)
            await callback.message.answer_audio(
                audio=audio, 
                caption=f"🎵 {title}\n\nDone by @{bot_info.username}"
            )
        else:
            video = FSInputFile(file_path)
            await callback.message.answer_video(
                video=video, 
                caption=f"🎬 {title}\n\nDone by @{bot_info.username}"
            )
        
        # Cleanup
        os.remove(file_path)
        await callback.message.delete()
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        await callback.message.edit_text("❌ حصلت مشكلة أثناء التحميل. ممكن يكون الملف حجمه كبير جداً.")
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
